## Context

The news pipeline has five small gaps:
1. `news.snapshot` has no URL — we cannot trace which exact page was fetched
2. `news.article.date` is optional — articles created without a date break downstream expectations
3. Blog post content hard-codes "Read full article…" in English regardless of the article's language
4. No quick navigation from an article form to its snapshot
5. `news.source` has no language field — the blog pipeline has no signal for what language to use

The Odoo instance is single-language (English admin, but articles/blog posts may be in any language). No multi-language website is in use.

## Goals / Non-Goals

**Goals:**
- Add `url` to `news.snapshot`; populate it from the website scraper
- Add `language` (Char) to `news.source`; auto-detect via LLM during listing
- Make `news.article.date` required with `default=fields.Date.today`; AI extraction fallback also uses today
- Have `_create_blog_post()` pass the source language to the teaser prompt so the AI generates the "Read full article…" text in the correct language
- Add an admin-only SmartButton on the article form that opens the related snapshot

**Non-Goals:**
- Multi-language Odoo website translations (Phase 2 / harden)
- Backfilling language on existing `news.source` records (auto-detected on next scrape)
- DB-level NOT NULL on `article.date` (UI-only required, no migration needed)

## Decisions

### Language detection: extend existing listing LLM call
The website scraper already calls the AI to extract article links from the listing page HTML. We extend the response schema to also include a `language` field (ISO 639-1 code, e.g. "de", "fr", "en"). If detected, it is stored on `news.source.language`. This avoids an extra AI call and is naturally correct: the listing page is the canonical representation of the source's language.

**Alternative considered:** Detect language per article during extraction. Rejected — noisier (could differ between articles), and we want a stable source-level signal.

### Blog post language: AI-generated link text via teaser prompt
The teaser prompt is already sent to the AI with the article title + content. We extend the prompt to return JSON with two fields: `teaser` (the teaser text) and `read_more` (the "Read full article…" link text). The AI naturally generates both in the source language. No translation lookup table needed.

**Alternative considered:** Static translation map (language → phrase). Rejected — limited coverage, maintenance burden, doesn't handle edge cases like mixed-language sites.

### SmartButton: direct Many2one link
`news.article.snapshot_id` is already a Many2one to `news.snapshot`. The SmartButton uses a standard `action_view_snapshot` method returning an `ir.actions.act_window` scoped to that one record. Count is always 0 or 1 — we use a computed `snapshot_count` field (trivially: 1 if `snapshot_id` else 0) to drive the `statinfo` widget. Admin-only via `groups=`.

### Article date default: model-level default only
`default=fields.Date.today` on the field covers both GUI creation and programmatic creation. The AI extraction code in `_extraction_create_article()` already sets `date` from the AI response; we add a fallback to `fields.Date.today()` when the AI returns no date. No DB migration required.

## Risks / Trade-offs

- **Language detection accuracy** → The LLM may misidentify language on multilingual listing pages. Mitigation: `language` is user-editable, so admins can correct it if needed. It is also re-detected on every scrape (but only written if detected).
- **Teaser prompt JSON change** → Existing tests mock the teaser AI response as plain text. After this change the response must be JSON with `teaser` and `read_more`. Tests will need updating. Mitigation: handled during implementation.
- **Snapshot URL for email sources** → Email snapshots have no URL; field left blank. No UI confusion since it's simply absent when empty.

## Migration Plan

1. Upgrade all affected modules (`newsassistant`, `newsassistant_website`, `newsassistant_blog`)
2. Odoo auto-adds the new columns (`news.snapshot.url`, `news.source.language`) with NULL defaults — safe for existing rows
3. Existing articles with `date=NULL` remain valid (UI-only required, no DB constraint)
4. Restart container; smoke test
5. Rollback: revert commits and upgrade — columns remain but are unused (safe)
