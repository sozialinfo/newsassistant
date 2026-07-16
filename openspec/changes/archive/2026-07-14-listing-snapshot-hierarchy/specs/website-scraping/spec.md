## MODIFIED Requirements

### Requirement: Website scraping module
The system SHALL provide a `newsassistant_website` module that depends on `newsassistant` and `queue_job`. This module SHALL contain all website-specific content capture functionality including crawl4ai fetching, URL listing, snapshot hierarchy management, and image selection.

#### Scenario: Module installs independently
- **WHEN** `newsassistant_website` is installed alongside `newsassistant`
- **THEN** website scraping functionality SHALL be available
- **THEN** the base `newsassistant` module SHALL function without `newsassistant_website`

### Requirement: Website source listing scrape
The `newsassistant_website` module SHALL extend `news.source` to add listing scrape functionality for `source_type='website'` sources. On trigger (cron or manual), it SHALL fetch the source URL via crawl4ai, create a listing `news.snapshot` with the fetched content, and enqueue `_discover_articles()` on that listing snapshot.

#### Scenario: Listing scrape creates listing snapshot
- **WHEN** a website source listing scrape runs successfully
- **THEN** one `news.snapshot` with `is_listing=True` SHALL be created for the source containing the listing page content
- **THEN** the listing snapshot creation SHALL enqueue `_discover_articles()` automatically

#### Scenario: Listing scrape skips known URLs
- **WHEN** a listing page contains 5 URLs and 3 already exist as articles
- **THEN** only 2 child snapshots SHALL be created for new URLs
- **THEN** `_discover_articles()` SHALL skip known URLs (dedup preserved)

### Requirement: Website _discover_articles() implementation
The `newsassistant_website` SHALL override `_discover_articles()` on `news.snapshot`. It SHALL send the listing snapshot's `raw_content` to the AI to extract article URLs (using the existing listing-scrape AI prompt). For each URL discovered, it SHALL crawl the article page via crawl4ai and create a child `news.snapshot` with `parent_id` set to the listing snapshot.

#### Scenario: Website discovery creates child snapshots
- **WHEN** `_discover_articles()` runs on a website listing snapshot containing 3 article URLs
- **THEN** the listing content SHALL be sent to AI for URL extraction
- **THEN** 3 child snapshots SHALL be created, one per discovered URL
- **THEN** each child snapshot SHALL have `parent_id` pointing to the listing snapshot
- **THEN** each child snapshot SHALL have `url` set to the article's URL

#### Scenario: Website discovery skips listing page URL
- **WHEN** a listing page contains a link to itself
- **THEN** `_discover_articles()` SHALL NOT create a child snapshot for the listing URL

#### Scenario: Website discovery skips binary resources
- **WHEN** a discovered URL points to a PDF or image file
- **THEN** `_discover_articles()` SHALL NOT create a child snapshot for that URL

### Requirement: Website article content capture
For website sources, article content is fetched via crawl4ai and converted from Markdown to HTML before being stored in child `news.snapshot.raw_content`.

#### Scenario: Article content stored as HTML
- **WHEN** crawl4ai returns Markdown content for an article page during `_discover_articles()`
- **THEN** the Markdown SHALL be converted to HTML
- **THEN** the HTML SHALL be stored in the child snapshot's `raw_content`

### Requirement: Header image selection in website module
The `newsassistant_website` module SHALL provide image selection logic. During `_discover_articles()`, when a child snapshot is created from a crawl4ai result, the images from crawl4ai SHALL be processed and the first valid landscape image SHALL be set on the resulting article.

#### Scenario: Header image selected for website article
- **WHEN** a website article child snapshot is created and crawl4ai returns images
- **THEN** the first valid landscape image SHALL be stored as `news.article.header_image`

### Requirement: Website scraping cron job
The `newsassistant_website` module SHALL provide a daily cron job that scrapes all active website-type sources.

#### Scenario: Cron scrapes all website sources
- **WHEN** the daily cron runs
- **THEN** all active `news.source` records with `source_type='website'` SHALL be enqueued for listing scrape
- **THEN** email-type sources SHALL NOT be scraped by this cron