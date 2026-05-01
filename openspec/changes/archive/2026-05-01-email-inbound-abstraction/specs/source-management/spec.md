## MODIFIED Requirements

### Requirement: News source model
The system SHALL provide a `news.source` model with fields: `name` (Char, required), `url` (Char, required for website sources), `source_type` (Selection: website/email, required, default=website), `sender_domain` (Char, for email sources), `active` (Boolean, default True), `last_scrape_date` (Datetime), `state` (Selection: ok/error, default ok), `error_message` (Text), `article_count` (Integer, computed from related articles via snapshots), and `snapshot_ids` (One2many to news.snapshot).

#### Scenario: Create a news source
- **WHEN** a user creates a new `news.source` record with name "Test Source" and url "https://example.com/news"
- **THEN** the record SHALL be created with `active=True`, `state='ok'`, `error_message` empty, `article_count=0`, and `source_type='website'`

#### Scenario: Computed article count via snapshots
- **WHEN** a news source has 2 snapshots, one with 3 articles and one with 2 articles
- **THEN** the `article_count` field SHALL return 5

### Requirement: News source form view

The system SHALL provide a form view for `news.source` allowing editing of name, source_type, active flag, and type-specific fields (url for website; sender_domain for email), with read-only display of state, last_scrape_date, error_message, a "Snapshots" tab listing related snapshots, and a list of related articles. For users in admin group, website sources SHALL also display a "Scrape Now" button, a "Scrape Status" section showing last job details (status, retries, next retry time, error), and a "Scrape History" section showing the last 10 log entries.

#### Scenario: Edit a news source

- **WHEN** the user opens a news source form
- **THEN** the user SHALL be able to edit name, source_type, and active flag
- **THEN** state, last_scrape_date, and error_message SHALL be read-only

#### Scenario: Website source shows URL field

- **WHEN** a user opens a source form with `source_type='website'`
- **THEN** the `url` field SHALL be visible and editable

#### Scenario: Email source shows domain field

- **WHEN** a user opens a source form with `source_type='email'`
- **THEN** the `sender_domain` field SHALL be visible and editable
- **THEN** the `url` field SHALL NOT be shown

#### Scenario: Admin sees scrape controls for website source

- **WHEN** an admin opens a website source form
- **THEN** the "Scrape Now" button SHALL be visible in the form header
- **THEN** the "Scrape Status" section SHALL be visible showing last job information
- **THEN** the "Scrape History" section SHALL be visible showing recent log entries

#### Scenario: User does not see scrape controls

- **WHEN** a regular user opens a news source form
- **THEN** the "Scrape Now" button SHALL NOT be visible
- **THEN** the "Scrape Status" section SHALL NOT be visible
- **THEN** the "Scrape History" section SHALL NOT be visible

### Requirement: Demo data with diverse sources
The system SHALL include demo data with at least 8 website news sources and at least 1 email news source. Website sources SHALL be selected from `news_source.csv`, representing diverse CMS platforms and HTML structures (Drupal, WordPress, TYPO3, and others). The email demo source SHALL represent a known newsletter.

#### Scenario: Install with demo data
- **WHEN** the module is installed with demo data enabled
- **THEN** at least 8 active website source records SHALL exist
- **THEN** at least 1 email source record SHALL exist with a valid sender_domain

### Requirement: Source error tracking
The system SHALL track scraping errors on the source record. When a scrape fails permanently (non-retryable), the source `state` SHALL be set to `'error'` and `error_message` SHALL contain a description of the failure. When a subsequent scrape succeeds, `state` SHALL be reset to `'ok'` and `error_message` cleared.

#### Scenario: Source enters error state
- **WHEN** a source scrape encounters a permanent error (e.g. HTTP 404)
- **THEN** the source `state` SHALL be set to `'error'`
- **THEN** `error_message` SHALL describe the failure

#### Scenario: Source recovers from error
- **WHEN** a source in `state='error'` is successfully scraped
- **THEN** the source `state` SHALL be set to `'ok'`
- **THEN** `error_message` SHALL be cleared

### Requirement: Source list filters for scrape status

The source list view search SHALL include filters: "Has Errors" (state=error), "Never Scraped" (last_scrape_date is empty), "Stale" (last_scrape_date older than 7 days), "Website Sources" (source_type=website), "Email Sources" (source_type=email).

#### Scenario: Filter sources with errors

- **WHEN** a user selects the "Has Errors" filter
- **THEN** only sources with `state='error'` SHALL be displayed

#### Scenario: Filter never scraped sources

- **WHEN** a user selects the "Never Scraped" filter
- **THEN** only sources where `last_scrape_date` is empty SHALL be displayed

#### Scenario: Filter stale sources

- **WHEN** a user selects the "Stale" filter and today is April 12
- **THEN** only sources where `last_scrape_date` is before April 5 SHALL be displayed
