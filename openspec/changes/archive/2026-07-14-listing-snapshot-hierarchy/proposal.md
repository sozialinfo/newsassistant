## Why

Newsletter emails contain multiple articles, but the current snapshot pipeline treats every snapshot as a single article. When a newsletter with 6 articles arrives, the AI correctly identifies it as "not a single article" and discards it. Meanwhile, the website path already understands listing pages — it extracts URLs and creates per-article snapshots. The two paths should be unified.

## What Changes

- **news.snapshot** gains `is_listing`, `parent_id`, `child_ids` fields to support a listing → article hierarchy
- **news.snapshot** gains a `_discover_articles()` method (raises `NotImplementedError` in core)
- **news.snapshot.create()** skips `_extract_articles()` for listing snapshots, enqueues `_discover_articles()` instead
- **newsassistant_website** implements `_discover_articles()`: AI extracts URLs from listing content, crawl4ai fetches each URL → child snapshot
- **newsassistant_website** `_scrape_listing()` persists the listing page as a listing snapshot before discovering child articles
- **newsassistant_email** implements `_discover_articles()`: AI extracts article sections from newsletter HTML → child snapshot per section
- **newsassistant_email** `message_new()` creates a listing snapshot instead of running direct extraction
- Existing `_extract_articles()` remains unchanged — it already handles single-article child snapshots correctly
- **BREAKING**: `news.snapshot.create()` no longer auto-enqueues `_extract_articles()` for listing snapshots

## Capabilities

### New Capabilities
- `snapshot-hierarchy`: Parent/child snapshot relationship with `is_listing`, `parent_id`, `child_ids` fields on `news.snapshot`
- `newsletter-discovery`: AI-based article section extraction from newsletter email content in `newsassistant_email`

### Modified Capabilities
- `snapshot-model`: Snapshot creation auto-enqueues `_discover_articles()` for listing snapshots instead of `_extract_articles()`
- `website-scraping`: Listing scrape persists listing page as a listing snapshot; article discovery happens via `_discover_articles()`
- `email-inbound`: Inbound email creates a listing snapshot; article discovery happens via `_discover_articles()`
- `scraping-pipeline`: Stage 2 extraction now operates on child snapshots; listing snapshots take a different path

## Impact

- `newsassistant/models/news_snapshot.py`: New fields, modified `create()`, new `_discover_articles()` base method
- `newsassistant_website/models/news_snapshot_website.py`: New `_discover_articles()` override, update `_extract_articles_website()`
- `newsassistant_website/models/news_source_website.py`: `_scrape_listing()` now creates listing snapshot, `_fetch_and_create_snapshot()` links to parent
- `newsassistant_email/models/news_snapshot_email.py`: `_discover_articles()` override, `message_new()` creates listing snapshot
- Tests in all three modules need updates for new flow
- Snapshot list/form views may need to show parent/child relationships