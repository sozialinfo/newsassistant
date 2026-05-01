## Context

The current `newsassistant` module mixes two concerns: the abstract concept of a news source and the concrete mechanism of website scraping. All content enters the system via Jina Reader API, and `news.article` links directly to `news.source`. There is no intermediate model to capture raw content before extraction.

The change introduces `news.snapshot` as the canonical raw-content layer, splits the base module from the website-specific scraping module, and adds an email inbound module that uses Odoo's standard `mail.alias.mixin` pattern.

## Goals / Non-Goals

**Goals:**
- Introduce `news.snapshot` as the intermediate model between source and articles
- Type `news.source` with `source_type` (website | email)
- Move all Jina/website-specific code into `newsassistant_website`
- Implement `newsassistant_email` with Odoo inbound alias, domain routing, auto-source creation, and AI naming
- Article extraction in base module operates on `snapshot.raw_content` (HTML)
- `newsassistant_blog` continues to work unchanged (depends on base only)
- 100% test coverage, DE/FR translations, fresh instance

**Non-Goals:**
- Production data migration (fresh instance only)
- Multi-alias support (one shared `newsassistant@` alias)
- Email attachment handling (only email body HTML is captured)
- Digest/blog functionality for email-sourced articles (already works at article level)

## Decisions

### D1: `news.snapshot` as a first-class model in base

**Decision:** `news.snapshot` lives in `newsassistant` (base), not in child modules.

**Rationale:** Both website and email modules create snapshots; article extraction (also in base) reads from snapshots. If snapshot lived in a child module, base would have a circular dependency. The base module defines the full hierarchy: source → snapshot → article.

**Alternative considered:** Snapshot only in child modules, base works with source directly. Rejected because extraction logic would need to be duplicated or abstracted via overridable method with no concrete model.

---

### D2: `raw_content` stored as `Html` field (always HTML)

**Decision:** `news.snapshot.raw_content` is an Odoo `Html` field. Website module converts Jina Markdown output to HTML before storing. Email module stores the inbound email HTML body (sanitized).

**Rationale:** HTML is the common denominator. The AI extraction prompt can work with HTML directly (structured, semantic). Markdown→HTML conversion is trivial with Python's `markdown` library or `mistune`. Avoids branching logic in the base extraction method.

**Alternative considered:** Store format-specific content with a `content_format` discriminator field. Rejected: adds complexity without benefit since the base extraction prompt doesn't need Markdown-specific formatting.

---

### D3: `news.article.source_id` as stored computed field

**Decision:** `article.source_id` is `compute='_compute_source_id', store=True` derived from `snapshot_id.source_id`.

**Rationale:** Existing views, filters, and `newsassistant_blog` all reference `source_id` on articles. Keeping it as a stored computed field avoids breaking changes in views and queries while maintaining a single source of truth.

**Alternative considered:** Remove `source_id` from article entirely, traverse via snapshot. Rejected: would require updating all views and existing tests.

---

### D4: `mail.alias.mixin` on `news.snapshot` model level (shared alias)

**Decision:** `news.snapshot` inherits `mail.alias.mixin`. One alias (`newsassistant@domain`) is created for the model. All inbound emails go through `message_new()` on `news.snapshot`.

**Rationale:** Standard Odoo pattern for model-level inbound email. Configurable alias name via Settings. No per-source aliases needed since the handler resolves the source from the sender domain.

**Implementation:** `message_new()` override on `news.snapshot`:
1. Extract sender domain from `msg_dict['email_from']`
2. Look up `news.source` with `source_type='email'` and matching domain
3. If not found: call AI to name the source, create `news.source`
4. Create `news.snapshot` with `source_id`, `raw_content=msg_dict['body']`
5. Snapshot creation auto-enqueues extraction job (via `create()` override in base)

---

### D5: Auto-extraction triggered by `news.snapshot.create()`

**Decision:** `news.snapshot.create()` (in base module) enqueues `_extract_articles()` as a queue job automatically.

**Rationale:** Both website and email modules create snapshots; neither should need to remember to trigger extraction. Centralising the trigger in `create()` ensures consistent behaviour.

**Implementation:**
```python
@api.model_create_multi
def create(self, vals_list):
    snapshots = super().create(vals_list)
    for snapshot in snapshots:
        snapshot.with_delay(channel="root.newsassistant")._extract_articles()
    return snapshots
```

---

### D6: AI source naming for auto-created email sources

**Decision:** When an email arrives from an unknown domain, call `_call_infomaniak_ai()` with a prompt asking for the publication name. Fall back to the domain name if AI fails or returns an unparseable response.

**Prompt pattern:** `"What is the name of the newsletter or publication associated with the email domain '{domain}'? Return only the publication name, nothing else."`

---

### D7: Module dependency graph

```
mail (Odoo core)
    │
    └── newsassistant (base)
              │
    ┌─────────┴──────────┐
    │                    │
newsassistant_website  newsassistant_email
    │
    └── newsassistant_blog (unchanged)
```

`newsassistant_email` depends on: `newsassistant`, `mail`
`newsassistant_website` depends on: `newsassistant`, `queue_job`
`newsassistant` (base) depends on: `base`, `queue_job`, `mail` (for alias mixin)

## Risks / Trade-offs

**[Risk] Markdown→HTML conversion quality for website snapshots**
The Jina Reader API returns Markdown. Converting to HTML before storing may lose some formatting nuance (e.g., code blocks, tables). The AI extraction prompt must be updated to work from HTML.
→ Mitigation: Use `markdown` Python library for conversion. Test with real articles. AI prompt adjustment is contained to one system prompt string.

**[Risk] Email HTML quality varies widely**
Newsletter HTML can be complex (table-based layouts, inline styles, tracking pixels). The AI extraction may struggle more than with clean Markdown.
→ Mitigation: Sanitise inbound HTML (strip scripts, tracking pixels, excessive inline styles) before storing in `raw_content`. `clean_html()` utility (currently unused) is repurposed here.

**[Risk] `mail.alias.mixin` requires `mail` module dependency in base**
Adding `mail` to base module dependencies is a minor but real dependency increase.
→ Mitigation: Acceptable — `mail` is a standard Odoo module present in all installations. The alias configuration lives in `newsassistant_email`; base only needs `mail` for `mail.alias.mixin` inheritance on `news.snapshot`.
→ Alternative: Only inherit alias mixin in the email module via `_inherit`. This is cleaner: base `news.snapshot` does NOT inherit `mail.alias.mixin`. Only `newsassistant_email` adds it via `_inherit = ['news.snapshot', 'mail.alias.mixin']`. **This is the preferred approach** — keeps base module lighter.

**[Risk] Queue job channel for email extraction**
Email-triggered extractions share the `root.newsassistant` channel with website scraping jobs. Under high load, email extractions could be delayed.
→ Mitigation: Acceptable for current scale. Can be split into sub-channels later if needed.

## Open Questions

- None — all decisions are resolved based on the exploration session.
