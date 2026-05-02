## Why

The organisation needs to track how incoming news relates to its long-term strategic priorities. Currently articles are manually triaged in the kanban but there is no structured way to label articles by strategic relevance, evaluate them against defined strategies, or produce an executive-quality digest for leadership. This feature closes that gap by introducing strategy-aware labelling, automated AI evaluation, and a polished PDF-exportable strategy brief.

## What Changes

- New Odoo module `newsassistant_strategy_digest` that depends on `newsassistant`
- New model `strategy.label` — coloured labels managed in Configuration; used to tag articles with strategic relevance
- New Many2many field `strategy_label_ids` on `news.article` linking to `strategy.label`
- New model `strategy.strategy` — a named strategy with optional date range, uploaded PDF documents, associated labels, and an AI-distilled prompt
- "Distill" action on `strategy.strategy`: extracts text from PDFs via `pdfminer.six` and calls the AI (qwen3 via Infomaniak) to generate a labelling prompt
- Background cron + manual trigger: evaluates new articles against each active strategy's prompt and assigns matching `strategy_label_ids`
- Strategy label filter added to the existing `news.article` kanban/list search bar (no grouping — M2M grouping not supported natively)
- Strategy labels shown as colour chips on kanban cards
- New model `strategy.digest` — a named digest for a selected period containing linked articles and an AI-generated HTML brief
- New menu "Strategy Digest" (under News Assistant) showing a list of digest records
- "Generate Brief" action on `strategy.digest`: collects labelled articles and active strategies for the period, calls AI to produce an HTML brief in the user's language (executive summary + detailed analysis with source references), stores it in an `Html` field
- QWeb PDF report on `strategy.digest` using `web.external_layout` with no hardcoded paper format — inherits company settings (logo, fonts, colours, paper size) from General Settings → Configure Document Layout
- DE and FR translations for all user-facing strings

## Capabilities

### New Capabilities

- `strategy-label`: Coloured label model (`strategy.label`) with configuration-level management and M2M field on `news.article`
- `strategy-management`: Strategy model (`strategy.strategy`) with PDF document upload, label associations, date range, and AI prompt distillation
- `strategy-article-evaluation`: Background cron + manual trigger that evaluates articles against strategy prompts and assigns strategy labels
- `strategy-digest`: Digest model (`strategy.digest`) with period selection, linked articles & strategies, AI-generated HTML brief, and PDF export via QWeb

### Modified Capabilities

- `kanban-triage`: Strategy label filter/facet added to the article search bar; strategy label chips shown on kanban cards

## Impact

- New module: `addons/newsassistant_strategy_digest/`
- Inherits `news.article` to add `strategy_label_ids`
- Inherits `res.config.settings` to expose label management (admin)
- Uses `pdfminer.six` (already available in container) for PDF text extraction
- Reuses Infomaniak AI API pattern from `newsassistant_blog` (`_call_ai`, `_parse_ai_json`)
- QWeb report registered as `ir.actions.report` with `report_type=qweb-pdf`; `paperformat_id` intentionally omitted so it inherits `env.company.paperformat_id`
- Adds cron job (`ir.cron`) for automatic article evaluation
- No changes to existing data models beyond the inherited `news.article` field addition
