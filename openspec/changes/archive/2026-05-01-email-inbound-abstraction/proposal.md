## Why

The current codebase conflates "news source" with "website scraping", making it impossible to receive content from other channels. Introducing a typed abstraction layer (source → snapshot → articles) enables email newsletters to be processed through the same pipeline as scraped websites.

## What Changes

- **BREAKING** `news.source` gains a `source_type` field (`website` | `email`); website-specific scraping logic moves to a new `newsassistant_website` module
- **BREAKING** `news.article` no longer links directly to `news.source`; it links to `news.snapshot`, with `source_id` as a stored computed field
- New model `news.snapshot` is introduced in the base module — the canonical raw HTML capture between a source and its extracted articles
- New module `newsassistant_website` extracts all Jina-based scraping, URL discovery, image selection, and cron jobs from `newsassistant`
- New module `newsassistant_email` implements Odoo inbound email aliasing on `news.snapshot`, auto-creates email-type sources from sender domains, and triggers article extraction
- `newsassistant_blog` dependency changes from `newsassistant` to `newsassistant` (base remains sufficient; no blog-level changes needed)
- Demo data is updated for all three modules; no data migration needed (no production data)

## Capabilities

### New Capabilities

- `snapshot-model`: The `news.snapshot` model — raw HTML capture linking a source to its extracted articles
- `source-types`: Typed news sources (`website` | `email`) with type-specific behaviour and UI
- `website-scraping`: Jina-based website scraping, URL listing, and image selection (extracted from base into `newsassistant_website`)
- `email-inbound`: Inbound email alias on `news.snapshot`, domain-to-source routing, auto-source creation with AI naming, and extraction trigger

### Modified Capabilities

- `source-management`: `news.source` gains `source_type`; form view adapts to show website/email-specific fields
- `scraping-pipeline`: Pipeline stages now operate on `news.snapshot` rather than directly on `news.source`; article extraction reads `snapshot.raw_content` (HTML) instead of fetching a URL
- `unified-logging`: Log entries now reference `snapshot_id` in addition to `source_id` and `article_id`
- `jina-fetching`: Moves entirely to `newsassistant_website`; base module no longer depends on Jina

## Impact

- **Modules added:** `newsassistant_website`, `newsassistant_email`
- **Module restructured:** `newsassistant` (base) loses scraping code, gains snapshot model
- **Breaking model change:** `news.article.source_id` becomes computed (stored); direct write to it is removed
- **New dependency:** `newsassistant_email` depends on `mail` (for `mail.alias.mixin`)
- **No migration needed:** Fresh instance only; demo data updated across all modules
- **Tests:** All existing tests must be updated to reflect new module locations; new tests added for snapshot and email modules
