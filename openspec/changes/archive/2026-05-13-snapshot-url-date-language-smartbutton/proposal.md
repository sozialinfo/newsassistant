## Why

Several small gaps in the data model and UI reduce the traceability and usability of the news pipeline: snapshots lack a source URL, article dates are optional causing downstream issues, the blog post "Read full article" link is hardcoded in English regardless of the article language, and there is no quick way to navigate from an article to its snapshot.

## What Changes

- Add a `url` field to `news.snapshot` so website snapshots record the exact page URL that was fetched; displayed in the snapshot form view
- Add a `language` field to `news.source` so the source language is stored explicitly; populated automatically by the LLM during the listing scrape
- Make `news.article.date` required with a default of today; the AI extraction fallback also defaults to today when no date is found
- Change `_create_blog_post()` to use the source language when generating the "Read full article…" link text (via the teaser prompt / AI), so blog post content matches the article's language
- Add an admin-only SmartButton on the `news.article` form view that navigates to the related snapshot

## Capabilities

### New Capabilities

- `snapshot-url`: Snapshot records the exact URL of the fetched web page

### Modified Capabilities

- `snapshot-model`: Adds `url` field to `news.snapshot`
- `source-management`: Adds `language` field to `news.source`; language auto-detected by LLM
- `blog-publishing`: Blog post content uses source language for the "Read full article…" text
- `article-views`: Article form view gets a snapshot SmartButton (admin only); article `date` becomes required with default today

## Impact

- `newsassistant`: `news_snapshot.py`, `news_article.py`, `news_snapshot_views.xml`, `news_article_views.xml`, `news_source.py`
- `newsassistant_website`: `news_source_website.py` — pass URL when creating snapshot; update listing LLM call to detect and store language
- `newsassistant_blog`: `news_article.py` (_create_blog_post) — pass language context so AI generates link text in correct language
- No new dependencies; no breaking API changes
