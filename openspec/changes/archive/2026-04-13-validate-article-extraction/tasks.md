## 1. Stage 2 - Extraction Validation

- [x] 1.1 Update extraction system prompt in `_fetch_and_extract` to include validation step (ask LLM to first determine if content is article, return `is_article: false` with reason if not)
- [x] 1.2 Update response parsing to handle both `is_article: false` and `is_article: true` responses
- [x] 1.3 Add logic to set `state="skipped"` and `error_message="Not an article: {reason}"` when `is_article: false`
- [x] 1.4 Create log entry with level `warning` for skipped non-articles
- [x] 1.5 Verify `scrape_date` is set for skipped articles (for audit trail)

## 2. Stage 1 - Improved Listing Prompt

- [x] 2.1 Update listing system prompt in `_scrape_listing` to emphasize main content area over navigation
- [x] 2.2 Add explicit guidance to exclude category/index links (URLs ending in `/news`, generic titles)
- [x] 2.3 Add guidance to look for article indicators (dates, specific headlines, URL patterns like `/artikel/`)

## 3. Testing

- [x] 3.1 Test extraction with actual article URL - verify normal extraction works
- [x] 3.2 Test extraction with category page URL (e.g., `https://skos.ch/themen/arbeit/news`) - verify it gets skipped
- [x] 3.3 Test that skipped articles prevent re-discovery on next listing scrape
- [x] 3.4 Re-scrape source #5 (SKOS) and verify improved results

## 4. Cleanup

- [x] 4.1 Delete or skip existing bad articles from source #5 that are category pages
