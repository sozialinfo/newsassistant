## 1. Core — news.snapshot fields and base method

- [x] 1.1 Add `is_listing` (Boolean, default=False), `parent_id` (Many2one self, index=True), `child_ids` (One2many self) to `news.snapshot`
- [x] 1.2 Add `_discover_articles()` base method with source-type dispatch
- [x] 1.3 Update `create()` to enqueue `_discover_articles()` for listing snapshots (instead of `_extract_articles()`), respecting `skip_snapshot_extraction` context key
- [x] 1.4 Update snapshot list/form views to show `is_listing`, `parent_id`, `child_ids`

## 2. Website — _discover_articles_website() implementation

- [x] 2.1 Implement `_discover_articles_website()` on website `news.snapshot`: AI extracts URLs from listing content, crawl4ai fetches each URL, creates child snapshot per article
- [x] 2.2 Update `_scrape_listing()` to create a listing snapshot instead of in-memory processing
- [x] 2.3 Update `_fetch_and_create_snapshot()` to accept parent context and link child snapshots to the listing

## 3. Email — _discover_articles_email() implementation

- [x] 3.1 Implement `_discover_articles_email()` on email `news.snapshot`: AI extracts article sections from newsletter HTML, creates child snapshot per section
- [x] 3.2 Update `message_new()` to create a listing snapshot and enqueue `_discover_articles()` on `root.email_extraction` channel

## 4. Tests

- [x] 4.1 Update existing snapshot tests for hierarchy and listing behavior
- [x] 4.2 Update website scraping tests for listing snapshot + _discover_articles()
- [x] 4.3 Update email inbound tests for listing snapshot + _discover_articles()

## 5. Deployment

- [x] 5.1 Upgrade newsassistant, newsassistant_website, newsassistant_email modules
- [x] 5.2 Restart container and smoke test
- [x] 5.3 Run existing tests