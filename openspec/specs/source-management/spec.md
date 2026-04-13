## ADDED Requirements

### Requirement: News source model
The system SHALL provide a `news.source` model with fields: `name` (Char, required), `url` (Char, required), `active` (Boolean, default True), `last_scrape_date` (Datetime), `state` (Selection: ok/error, default ok), `error_message` (Text), and `article_count` (Integer, computed from related articles).

#### Scenario: Create a news source
- **WHEN** a user creates a new `news.source` record with name "Test Source" and url "https://example.com/news"
- **THEN** the record SHALL be created with `active=True`, `state='ok'`, `error_message` empty, and `article_count=0`

#### Scenario: Computed article count
- **WHEN** a news source has 5 related `news.article` records
- **THEN** the `article_count` field SHALL return 5

### Requirement: News source list view
The system SHALL provide a list (tree) view for `news.source` showing name, url, state, last_scrape_date, and article_count.

#### Scenario: View news sources
- **WHEN** the user navigates to the News Sources menu
- **THEN** all news source records SHALL be displayed in a list view with columns for name, url, state, last scrape date, and article count

### Requirement: News source form view

The system SHALL provide a form view for `news.source` allowing editing of name, url, and active flag, with read-only display of state, last_scrape_date, error_message, and a list of related articles. For users in admin group, the form SHALL also display a "Scrape Now" button, a "Scrape Status" section showing last job details (status, retries, next retry time, error), and a "Scrape History" section showing the last 10 log entries.

#### Scenario: Edit a news source

- **WHEN** the user opens a news source form
- **THEN** the user SHALL be able to edit name, url, and active flag
- **THEN** state, last_scrape_date, and error_message SHALL be read-only

#### Scenario: Admin sees scrape controls

- **WHEN** an admin opens a news source form
- **THEN** the "Scrape Now" button SHALL be visible in the form header
- **THEN** the "Scrape Status" section SHALL be visible showing last job information
- **THEN** the "Scrape History" section SHALL be visible showing recent log entries

#### Scenario: User does not see scrape controls

- **WHEN** a regular user opens a news source form
- **THEN** the "Scrape Now" button SHALL NOT be visible
- **THEN** the "Scrape Status" section SHALL NOT be visible
- **THEN** the "Scrape History" section SHALL NOT be visible

### Requirement: Demo data with diverse sources
The system SHALL include demo data with at least 8 news sources selected from `news_source.csv`, representing diverse CMS platforms and HTML structures (Drupal, WordPress, TYPO3, and others).

#### Scenario: Install with demo data
- **WHEN** the module is installed with demo data enabled
- **THEN** at least 8 active news source records SHALL exist
- **THEN** the sources SHALL include sites with different underlying CMS platforms

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

The source list view search SHALL include filters: "Has Errors" (state=error), "Never Scraped" (last_scrape_date is empty), "Stale" (last_scrape_date older than 7 days).

#### Scenario: Filter sources with errors

- **WHEN** a user selects the "Has Errors" filter
- **THEN** only sources with `state='error'` SHALL be displayed

#### Scenario: Filter never scraped sources

- **WHEN** a user selects the "Never Scraped" filter
- **THEN** only sources where `last_scrape_date` is empty SHALL be displayed

#### Scenario: Filter stale sources

- **WHEN** a user selects the "Stale" filter and today is April 12
- **THEN** only sources where `last_scrape_date` is before April 5 SHALL be displayed
