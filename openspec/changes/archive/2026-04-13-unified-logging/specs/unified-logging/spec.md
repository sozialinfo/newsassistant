## ADDED Requirements

### Requirement: Unified log summary model

The system SHALL provide a `news.log` model with fields:
- `timestamp` (Datetime, required, default=now)
- `level` (Selection: success/warning/error, required)
- `category` (Selection: listing/extraction, required)
- `message` (Char, required)
- `duration` (Float, seconds, optional)
- `source_id` (Many2one to news.source, optional, ondelete=set null)
- `article_id` (Many2one to news.article, optional, ondelete=set null)
- `job_id` (Many2one to queue.job, optional, ondelete=set null)
- `entry_ids` (One2many to news.log.entry)

The model SHALL be ordered by timestamp descending.

#### Scenario: Log created for listing scrape

- **WHEN** Stage 1 listing scrape completes successfully finding 5 articles in 3.2 seconds
- **THEN** a `news.log` record SHALL be created
- **THEN** `level` SHALL be `success`
- **THEN** `category` SHALL be `listing`
- **THEN** `duration` SHALL be approximately `3.2`
- **THEN** `source_id` SHALL reference the scraped source

#### Scenario: Log created for article extraction

- **WHEN** Stage 2 article extraction fails with a parse error
- **THEN** a `news.log` record SHALL be created
- **THEN** `level` SHALL be `error`
- **THEN** `category` SHALL be `extraction`
- **THEN** `article_id` SHALL reference the article
- **THEN** `source_id` SHALL reference the article's source

#### Scenario: Cascade behavior on source delete

- **WHEN** a `news.source` record is deleted
- **THEN** related `news.log` records SHALL have `source_id` set to null
- **THEN** the log records SHALL NOT be deleted

### Requirement: Log entry detail model

The system SHALL provide a `news.log.entry` model with fields:
- `log_id` (Many2one to news.log, required, ondelete=cascade)
- `timestamp` (Datetime, required, default=now)
- `level` (Selection: debug/info/warning/error, required)
- `message` (Char, required)
- `duration` (Float, seconds, optional)
- `metadata` (JSON/Text, optional)

The model SHALL be ordered by timestamp ascending within a log.

#### Scenario: Entry created for Jina fetch

- **WHEN** Jina Reader fetch completes in 1.2 seconds returning 4521 characters
- **THEN** a `news.log.entry` record SHALL be created
- **THEN** `level` SHALL be `info`
- **THEN** `message` SHALL indicate fetch completion
- **THEN** `duration` SHALL be approximately `1.2`
- **THEN** `metadata` MAY include character count

#### Scenario: Entry created for LLM call

- **WHEN** LLM call completes with 2847 input tokens and 412 output tokens in 2.1 seconds
- **THEN** a `news.log.entry` record SHALL be created
- **THEN** `metadata` SHALL include `model`, `system_prompt`, `user_content`, `response_content`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `duration_ms`

#### Scenario: Entries deleted with parent log

- **WHEN** a `news.log` record is deleted
- **THEN** all related `news.log.entry` records SHALL be deleted

### Requirement: LLM interaction logging

The system SHALL log every LLM call as a `news.log.entry` with full request and response details in the `metadata` JSON field.

The metadata SHALL include:
- `request.model`: The model name (e.g., "qwen3")
- `request.temperature`: The temperature setting
- `request.system_prompt`: The full system prompt text
- `request.user_content`: The full user message content
- `response.content`: The full response content
- `response.status_code`: The HTTP status code
- `usage.prompt_tokens`: Number of input tokens
- `usage.completion_tokens`: Number of output tokens
- `usage.total_tokens`: Total tokens used
- `timing.duration_ms`: Response time in milliseconds

#### Scenario: Successful LLM call logged

- **WHEN** an LLM call succeeds with model "qwen3", 2847 prompt tokens, 412 completion tokens
- **THEN** a log entry SHALL be created with level `info`
- **THEN** `metadata.request.model` SHALL be "qwen3"
- **THEN** `metadata.usage.prompt_tokens` SHALL be 2847
- **THEN** `metadata.usage.completion_tokens` SHALL be 412
- **THEN** `metadata.response.content` SHALL contain the full LLM response

#### Scenario: Failed LLM call logged

- **WHEN** an LLM call fails with HTTP 429 rate limit error
- **THEN** a log entry SHALL be created with level `error`
- **THEN** `metadata.response.status_code` SHALL be 429
- **THEN** `metadata.request.system_prompt` and `metadata.request.user_content` SHALL be preserved for debugging

### Requirement: Log entry vacuum for successful operations

The system SHALL automatically delete `news.log.entry` records where the parent `news.log.level` is `success` and the entry is older than 1 day.

This SHALL be implemented using Odoo's `ir.autovacuum` mechanism.

Entries for logs with `level` of `warning` or `error` SHALL NOT be vacuumed.

#### Scenario: Successful log entries cleaned up

- **WHEN** the vacuum job runs
- **THEN** entries for `success` logs older than 1 day SHALL be deleted
- **THEN** the parent `news.log` record SHALL remain

#### Scenario: Error log entries preserved

- **WHEN** the vacuum job runs
- **THEN** entries for `error` logs SHALL NOT be deleted regardless of age

#### Scenario: Warning log entries preserved

- **WHEN** the vacuum job runs
- **THEN** entries for `warning` logs SHALL NOT be deleted regardless of age

### Requirement: Admin Logs menu

The News Assistant menu SHALL include a "Logs" menu item visible to admin group only. It SHALL open the unified log browser.

#### Scenario: Admin sees Logs menu

- **WHEN** an admin opens the News Assistant menu
- **THEN** "Logs" SHALL be visible as a menu item

#### Scenario: Regular user does not see Logs menu

- **WHEN** a regular user opens the News Assistant menu
- **THEN** "Logs" SHALL NOT be visible

### Requirement: Admin Logs view with filters

The Logs view SHALL display `news.log` records in a list view with columns: Timestamp, Level (badge), Category, Source, Article, Message, Duration.

The view SHALL provide filter options for:
- Source (dropdown)
- Article (dropdown)
- Level (success/warning/error)
- Category (listing/extraction)
- Date range

The view SHALL provide group by options for:
- Source
- Level
- Category

#### Scenario: Filter logs by source

- **WHEN** an admin selects source "Reuters" in the filter
- **THEN** only logs with `source_id` = Reuters SHALL be displayed

#### Scenario: Filter logs by level

- **WHEN** an admin selects level "error" in the filter
- **THEN** only logs with `level` = error SHALL be displayed

#### Scenario: Group logs by category

- **WHEN** an admin groups logs by category
- **THEN** logs SHALL be grouped into "listing" and "extraction" sections

### Requirement: Running jobs section in Logs view

The Logs view SHALL display a "Running Now" section at the top showing currently executing jobs from `queue.job` where `state='started'` and the job function is `_scrape_listing` or `_fetch_and_extract`.

Each running job SHALL display: Category (listing/extraction), Source/Article name, Started time.

#### Scenario: View running jobs

- **WHEN** an admin opens the Logs view and 3 jobs are currently running
- **THEN** the "Running Now" section SHALL show 3 entries

#### Scenario: No running jobs

- **WHEN** an admin opens the Logs view and no jobs are running
- **THEN** the "Running Now" section SHALL show "No jobs running" or be hidden

### Requirement: Admin Running Jobs menu

The News Assistant menu SHALL include a "Running Jobs" menu item visible to admin group only. It SHALL open a list of `queue.job` records filtered to `state='started'` and the newsassistant channel.

#### Scenario: Admin sees Running Jobs menu

- **WHEN** an admin opens the News Assistant menu
- **THEN** "Running Jobs" SHALL be visible as a menu item

#### Scenario: View running jobs list

- **WHEN** an admin clicks "Running Jobs" with 2 jobs currently running
- **THEN** a list view SHALL show 2 queue.job records

### Requirement: Source scraping indicator

The Sources list view SHALL display a visual indicator showing whether a source currently has a running scrape job.

#### Scenario: Source with running job

- **WHEN** a source has a `_scrape_listing` job with `state='started'`
- **THEN** the source row SHALL display a "scraping" indicator badge

#### Scenario: Source without running job

- **WHEN** a source has no running jobs
- **THEN** the source row SHALL NOT display a scraping indicator

### Requirement: Log navigation to linked objects

Each log entry in list and form views SHALL provide clickable links to navigate to the linked source, article, and job records.

#### Scenario: Navigate to source from log

- **WHEN** an admin clicks the source link on a log entry
- **THEN** the linked `news.source` form SHALL open

#### Scenario: Navigate to article from log

- **WHEN** an admin clicks the article link on a log entry
- **THEN** the linked `news.article` form SHALL open

#### Scenario: Navigate to job from log

- **WHEN** an admin clicks the job link on a log entry
- **THEN** the linked `queue.job` form SHALL open

#### Scenario: Missing linked object

- **WHEN** a log entry has no `article_id` (e.g., a listing scrape log)
- **THEN** the article column SHALL be empty or show "-"

### Requirement: Log detail view with entries

The log form view SHALL display all fields from the summary plus an expandable/collapsible list of detail entries.

Each entry SHALL display: Timestamp, Level (badge), Message, Duration (if present).

Entries with metadata SHALL provide a way to view the full metadata JSON.

#### Scenario: View log with entries

- **WHEN** an admin opens a log record with 5 detail entries
- **THEN** all 5 entries SHALL be displayed in chronological order

#### Scenario: View LLM metadata

- **WHEN** an admin views an entry with LLM metadata
- **THEN** the full metadata including prompt and response SHALL be viewable

### Requirement: Log model access control

The `news.log` and `news.log.entry` models SHALL be readable by admin group only. Write/create access SHALL be granted to system operations only (not via UI).

#### Scenario: Regular user cannot access logs

- **WHEN** a regular user attempts to access `news.log` records directly
- **THEN** access SHALL be denied

#### Scenario: Admin can read logs

- **WHEN** an admin accesses `news.log` or `news.log.entry` records
- **THEN** read access SHALL be granted
