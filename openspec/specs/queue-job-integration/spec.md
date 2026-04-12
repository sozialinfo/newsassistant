## ADDED Requirements

### Requirement: Daily cron job
The system SHALL provide an `ir.cron` record that runs once daily. The cron SHALL call `_cron_scrape_all()` on `news.source`, which iterates all active sources and enqueues a listing scrape job for each via `with_delay()`.

#### Scenario: Daily cron fires
- **WHEN** the daily cron triggers
- **THEN** one queue job SHALL be created for each active `news.source` record
- **THEN** inactive sources SHALL NOT be scraped

### Requirement: Queue job channel
The system SHALL define a `queue.job.channel` named `newsassistant` under the root channel. The channel SHALL be configured with a capacity appropriate for concurrent web scraping (recommended: 4).

#### Scenario: Channel limits concurrency
- **WHEN** more than 4 scrape jobs are enqueued
- **THEN** at most 4 SHALL run concurrently (remaining queue until a slot opens)

### Requirement: Job function registration
The system SHALL register `_scrape_listing` on `news.source` and `_fetch_and_extract` on `news.article` as queue job functions assigned to the `root.newsassistant` channel. A retry pattern of `{1: 300, 3: 900, 5: 3600}` SHALL be configured for both functions.

#### Scenario: Scrape listing job registered
- **WHEN** the module is installed
- **THEN** a `queue.job.function` record SHALL exist for `news.source._scrape_listing` on channel `root.newsassistant`

#### Scenario: Fetch and extract job registered
- **WHEN** the module is installed
- **THEN** a `queue.job.function` record SHALL exist for `news.article._fetch_and_extract` on channel `root.newsassistant`

### Requirement: Retryable errors for transient failures
The system SHALL raise `RetryableJobError` for transient HTTP errors (timeouts, 5xx status codes, connection errors) and transient AI API errors (rate limits, timeouts). Permanent errors (HTTP 404, 403, invalid domain) SHALL NOT be retried.

#### Scenario: Transient HTTP error retries
- **WHEN** a source returns HTTP 503
- **THEN** the job SHALL raise `RetryableJobError`
- **THEN** the job SHALL be retried according to the retry pattern

#### Scenario: Permanent HTTP error does not retry
- **WHEN** a source returns HTTP 404
- **THEN** the job SHALL NOT raise `RetryableJobError`
- **THEN** the source SHALL be marked with `state='error'`

#### Scenario: AI API rate limit retries
- **WHEN** the Infomaniak API returns HTTP 429
- **THEN** the job SHALL raise `RetryableJobError`

### Requirement: Server configuration for queue_job
The system documentation SHALL specify that `queue_job` MUST be added to `server_wide_modules` in `odoo.conf`, and the OCA queue addons path MUST be included in `addons_path`. The `odoo.conf` SHALL include a `[queue_job]` section with channel configuration.

#### Scenario: Configuration documented
- **WHEN** a developer reads the README
- **THEN** instructions for configuring `server_wide_modules`, `addons_path`, and queue job channels SHALL be present
