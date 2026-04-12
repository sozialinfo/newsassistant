## 1. Core Fetch Utility

- [x] 1.1 Create `fetch_page(url)` function in `news_source.py` that fetches via Jina Reader API
- [x] 1.2 Add JINA_API_KEY validation (raise ValueError if not set)
- [x] 1.3 Implement timeout handling (60 seconds, raise RetryableJobError)
- [x] 1.4 Implement transient error handling (408, 429, 5xx → RetryableJobError)
- [x] 1.5 Implement permanent error handling (other non-200 → ValueError)
- [x] 1.6 Add content truncation to MAX_CLEAN_HTML_LENGTH (30,000 chars)

## 2. Update Listing Scraper

- [x] 2.1 Replace direct HTTP fetch with `fetch_page()` call in `_scrape_listing()`
- [x] 2.2 Update AI system prompt to describe input as "markdown content from a news listing page"
- [x] 2.3 Update prompt to reference "markdown links [text](url)" instead of "href attribute"
- [x] 2.4 Remove `clean_html()` call from `_scrape_listing()`

## 3. Update Article Extractor

- [x] 3.1 Replace direct HTTP fetch and Jina fallback with single `fetch_page()` call in `_fetch_and_extract()`
- [x] 3.2 Update AI system prompt to describe input as "markdown content from a news article"
- [x] 3.3 Remove `source_type` variable (always markdown now)
- [x] 3.4 Remove PDF detection and pdfminer handling (Jina handles PDFs)
- [x] 3.5 Remove 403-specific Jina fallback logic
- [x] 3.6 Delete `_fetch_via_jina()` method from NewsArticle class

## 4. Cleanup

- [x] 4.1 Remove unused imports from `news_article.py` (BytesIO, urlparse if unused)
- [x] 4.2 Verify `clean_html()` and `STRIP_TAGS` can remain for potential other uses
- [x] 4.3 Update `__manifest__.py` to remove `pdfminer.six` from external dependencies if listed

## 5. Testing

- [x] 5.1 Test listing scrape with JS-heavy source (caritas.ch)
- [x] 5.2 Test article extraction with standard HTML page
- [x] 5.3 Test error handling when JINA_API_KEY is not set
- [x] 5.4 Verify existing tests still pass (update mocks if needed)
