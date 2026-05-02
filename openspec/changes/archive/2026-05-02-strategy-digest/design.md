## Context

The newsassistant project has a well-established pattern for AI-driven article processing (`newsassistant_blog`). The new `newsassistant_strategy_digest` module extends the same `news.article` model, reuses the same AI infrastructure (`_call_ai`, `_parse_ai_json`), and follows the same cron+queue_job pipeline pattern.

Key constraints:
- AI provider: qwen3 via Infomaniak API (text-only, no file uploads)
- PDF text extraction: `pdfminer.six` (already installed in container)
- Paper format / report layout: fully inherited from `res.company` — no hardcoding
- Kanban grouping by M2M not supported in Odoo natively → use filter/facet instead
- OCA naming: M2M field uses `_ids` suffix → `strategy_label_ids`

## Goals / Non-Goals

**Goals:**
- `strategy.label`: config-managed coloured labels, M2M on `news.article`
- `strategy.strategy`: named strategy with PDF docs, labels, date range, AI-distilled prompt
- Cron + manual re-evaluate: assigns `strategy_label_ids` to articles based on each strategy's prompt
- `strategy.digest`: period-based AI brief (HTML), PDF export via QWeb using company settings
- Strategy label filter in existing article search bar + colour chips on kanban cards
- DE + FR translations for all user-facing strings

**Non-Goals:**
- Kanban grouping by M2M label (not feasible natively)
- Translating article content/titles into the user's language
- Multi-company isolation of strategies/labels (single company scope)
- Real-time evaluation (cron-based, not event-triggered)

## Decisions

### D1: Module dependency — inherit news.article, not fork it

`newsassistant_strategy_digest` depends on `newsassistant` only (not `newsassistant_blog`). The `strategy_label_ids` field is added via `_inherit = "news.article"`, following the exact same pattern as `newsassistant_blog`. This keeps the module independently installable.

Alternatives considered:
- Fork `news.article` directly → rejected, creates duplication and breaks upgrade path
- Depend on `newsassistant_blog` → rejected, unnecessary coupling; strategy digest is independent of blog publishing

### D2: PDF text extraction via pdfminer.six

`pdfminer.high_level.extract_text()` is used to extract text from uploaded PDF strategy documents before sending to the AI for prompt distillation. Odoo's own test suite uses the same library for the same purpose.

Alternatives considered:
- `PyPDF2.page.extract_text()` → less accurate for complex layouts
- Odoo's `OdooPdfFileReader` → only extracts embedded file attachments, not page text
- User writes strategy as text only (no PDF) → rejected per requirements

### D3: Strategy documents stored as ir.attachment via Many2many

`strategy.strategy` has `document_ids = Many2many('ir.attachment')` with `domain=[('mimetype', 'like', 'pdf')]`. This is the standard Odoo pattern; files appear in the chatter/attachments area and can be previewed inline.

Alternatives considered:
- Dedicated `strategy.document` model with Binary field → duplicates what ir.attachment already does

### D4: Article evaluation pipeline — cron + manual trigger (same as blog digest)

A cron evaluates articles in state `scraped` that have not yet been evaluated for strategy labels (`strategy_eval_state = 'pending'`). Each article is evaluated against each **active** strategy (strategies where today falls within `date_from`–`date_to`, or where dates are unset). A manual "Re-evaluate" button on the article form resets `strategy_eval_state` to `pending` and re-queues the job.

Alternatives considered:
- Evaluate only when creating a digest → simpler but labels arrive too late for kanban triage
- Per-strategy cron → N crons for N strategies; harder to manage

### D5: Digest brief generation — one AI call per digest

When the user clicks "Generate Brief" on a `strategy.digest` record, a single AI call receives: the list of strategies (names + prompts) active in the period, and all articles with matching `strategy_label_ids` in the period (title + summary + source + date). The AI returns HTML in the user's language with executive summary and detailed analysis with footnote references. The brief is stored in `strategy.digest.brief` (Html field).

Alternatives considered:
- One AI call per strategy → multiple calls, incoherent cross-strategy references
- Streaming → not supported by Infomaniak API wrapper

### D6: PDF report — no hardcoded paperformat_id

The `ir.actions.report` record for `strategy.digest` intentionally omits `paperformat_id`. Odoo's `get_paperformat()` method falls back to `self.env.company.paperformat_id`, which is configured per-company via General Settings → "Configure Document Layout". The template uses `t-call="web.external_layout"` which picks up logo, font, brand colours, header/footer from `res.company` automatically.

### D7: Multi-strategy article reference — once in brief, cited across sections

An article matching multiple strategies appears once in the article list of the digest and is referenced in each relevant strategy section of the brief. The AI prompt instructs cross-referencing rather than repetition.

## Risks / Trade-offs

- **pdfminer text quality** → Scanned PDFs (image-only) yield no text. Mitigation: log a warning and skip the document; user can supplement with text description field on strategy.
- **Large strategy documents** → Extracted text may exceed context window. Mitigation: truncate to 8000 chars per document in the AI call.
- **AI brief length** → AI cannot guarantee exactly 2 A4 pages. Mitigation: the prompt instructs brevity; the QWeb template uses CSS `max-height` with `overflow: hidden` as soft enforcement.
- **Many articles in period** → Long AI context. Mitigation: include only `title`, `summary` (≤200 chars), `source`, `date` per article; truncate at 50 articles with a note.

## Migration Plan

1. Install `newsassistant_strategy_digest` module
2. No migration scripts required — all new models
3. Existing articles get `strategy_eval_state = 'pending'` (default); cron will evaluate them on next run
4. Rollback: uninstall module (all new tables dropped automatically)

## Open Questions

None — all decisions resolved during exploration phase.
