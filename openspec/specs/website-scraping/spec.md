## ADDED Requirements

### Requirement: Website scraping module
The system SHALL provide a `newsassistant_website` module that depends on `newsassistant` and `queue_job`. This module SHALL contain all website-specific content capture functionality including Jina fetching, URL listing, and image selection.

#### Scenario: Module installs independently
- **WHEN** `newsassistant_website` is installed alongside `newsassistant`
- **THEN** website scraping functionality SHALL be available
- **THEN** the base `newsassistant` module SHALL function without `newsassistant_website`

### Requirement: Website source listing scrape
The `newsassistant_website` module SHALL extend `news.source` to add listing scrape functionality for `source_type='website'` sources. On trigger (cron or manual), it SHALL fetch the source URL via Jina, extract article URLs via AI, create `news.snapshot` records (one per listing scrape), and create `news.article` stub records for each new URL discovered.

#### Scenario: Listing scrape creates snapshot
- **WHEN** a website source listing scrape runs successfully
- **THEN** one `news.snapshot` SHALL be created for the source containing the listing page HTML
- **THEN** the snapshot creation SHALL enqueue article extraction automatically

#### Scenario: Listing scrape skips known URLs
- **WHEN** a listing page contains 5 URLs and 3 already exist as articles
- **THEN** only 2 new article stubs SHALL be created
- **THEN** the 3 existing articles SHALL NOT be re-fetched

### Requirement: Website article content capture
For website sources, article content is fetched via Jina Reader API and converted from Markdown to HTML before being stored in `news.snapshot.raw_content`.

#### Scenario: Article content stored as HTML
- **WHEN** Jina returns Markdown content for an article page
- **THEN** the Markdown SHALL be converted to HTML
- **THEN** the HTML SHALL be stored in `news.snapshot.raw_content`

### Requirement: Header image selection in website module
The `newsassistant_website` module SHALL provide image selection logic (moved from base module): `select_header_image()`, `validate_and_download_image()`, and `should_skip_image_url()`. These SHALL be called during article extraction for website-sourced articles.

#### Scenario: Header image selected for website article
- **WHEN** a website article is extracted and Jina returns images
- **THEN** the first valid landscape image SHALL be stored as `news.article.header_image`

### Requirement: Website scraping cron job
The `newsassistant_website` module SHALL provide a daily cron job that scrapes all active website-type sources.

#### Scenario: Cron scrapes all website sources
- **WHEN** the daily cron runs
- **THEN** all active `news.source` records with `source_type='website'` SHALL be enqueued for listing scrape
- **THEN** email-type sources SHALL NOT be scraped by this cron
