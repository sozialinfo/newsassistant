## Why

The article extraction pipeline is creating stubs for non-article URLs (category pages, navigation links, index pages). When the listing page LLM extracts URLs, it sometimes includes navigation menu links like `/themen/arbeit/news` which are topic listing pages, not actual articles. These then go through the full extraction pipeline, wasting API calls and cluttering the article database with invalid entries.

## What Changes

- Modify the extraction prompt (Stage 2) to first validate whether the fetched content is actually a single article before attempting extraction
- If validation determines the content is NOT an article (e.g., it's a category page, index page, or navigation page), mark the stub as `skipped` with a reason, preserving the URL to prevent re-discovery
- Improve the listing prompt (Stage 1) to better distinguish actual article links from navigation/category links, reducing false positives upfront

## Capabilities

### New Capabilities

- `article-validation`: Validation logic to determine if fetched content is a single article vs. a listing/category/navigation page, integrated into the extraction flow

### Modified Capabilities

- `scraping-pipeline`: Stage 2 extraction now includes validation step; Stage 1 prompt improved to reduce navigation link extraction

## Impact

- `news_article.py`: `_fetch_and_extract` method modified to include validation before extraction
- `news_source.py`: `_scrape_listing` method's system prompt improved
- Existing `skipped` state reused for validated-but-not-article URLs
- No schema changes required (reusing existing `state` and `error_message` fields)
- No breaking changes to external APIs or data model
