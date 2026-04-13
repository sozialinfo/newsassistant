## ADDED Requirements

### Requirement: Source scrape log model

The system SHALL provide a `news.source.log` model with fields: `source_id` (Many2one to news.source, required, ondelete=cascade), `timestamp` (Datetime, required), `status` (Selection: success/error, required), `duration` (Float, seconds), `articles_found` (Integer), `error_message` (Text), `job_id` (Many2one to queue.job, ondelete=set null).

#### Scenario: Log record created on successful scrape

- **WHEN** Stage 1 listing scrape completes successfully finding 5 new articles
- **THEN** a `news.source.log` record SHALL be created
- **THEN** `status` SHALL be `success`
- **THEN** `articles_found` SHALL be `5`
- **THEN** `timestamp` SHALL be the start time of the scrape

#### Scenario: Log record created on failed scrape

- **WHEN** Stage 1 listing scrape fails with a timeout
- **THEN** a `news.source.log` record SHALL be created
- **THEN** `status` SHALL be `error`
- **THEN** `error_message` SHALL describe the timeout

#### Scenario: Cascade delete with source

- **WHEN** a `news.source` record is deleted
- **THEN** all related `news.source.log` records SHALL be deleted

### Requirement: Article scrape log model

The system SHALL provide a `news.article.log` model with fields: `article_id` (Many2one to news.article, required, ondelete=cascade), `timestamp` (Datetime, required), `status` (Selection: success/error, required), `duration` (Float, seconds), `error_message` (Text), `job_id` (Many2one to queue.job, ondelete=set null).

#### Scenario: Log record created on successful extraction

- **WHEN** Stage 2 article extraction completes successfully in 4.5 seconds
- **THEN** a `news.article.log` record SHALL be created
- **THEN** `status` SHALL be `success`
- **THEN** `duration` SHALL be approximately `4.5`

#### Scenario: Log record created on failed extraction

- **WHEN** Stage 2 article extraction fails with invalid JSON from AI
- **THEN** a `news.article.log` record SHALL be created
- **THEN** `status` SHALL be `error`
- **THEN** `error_message` SHALL describe the parse failure

### Requirement: Scrape history on source form

The source form view SHALL display a "Scrape History" section showing the last 10 log entries for that source, with columns: Date, Status, Articles Found, Error. A "View All" button SHALL open the full log list filtered to that source.

#### Scenario: View source scrape history

- **WHEN** an admin views a source form with 15 scrape log entries
- **THEN** the last 10 entries SHALL be displayed in reverse chronological order
- **THEN** each entry SHALL show date, status badge, articles count, and error (if any)

#### Scenario: View all source logs

- **WHEN** an admin clicks "View All" on the scrape history section
- **THEN** a list view SHALL open showing all logs for that source

#### Scenario: Scrape history visibility

- **WHEN** a regular user views a source form
- **THEN** the "Scrape History" section SHALL NOT be visible

### Requirement: Extraction history on article form

The article form view SHALL display an "Extraction History" section showing the last 10 log entries for that article, with columns: Date, Status, Duration, Error. A "View All" button SHALL open the full log list filtered to that article.

#### Scenario: View article extraction history

- **WHEN** an admin views an article form with 5 extraction log entries
- **THEN** all 5 entries SHALL be displayed in reverse chronological order
- **THEN** each entry SHALL show date, status badge, duration, and error (if any)

#### Scenario: Extraction history visibility

- **WHEN** a regular user views an article form
- **THEN** the "Extraction History" section SHALL NOT be visible

### Requirement: View full job log link

Each log entry that has a linked `job_id` SHALL display a "View Full Log" link that opens the queue.job record in a new view.

#### Scenario: View full log from source history

- **WHEN** an admin clicks "View Full Log" on a source log entry
- **THEN** the linked queue.job record SHALL open in form view

#### Scenario: Job deleted but log remains

- **WHEN** a log entry's linked queue.job record has been deleted
- **THEN** the "View Full Log" link SHALL NOT be displayed
- **THEN** the log entry itself SHALL still be visible

### Requirement: Log model access control

The `news.source.log` and `news.article.log` models SHALL be readable by admin group only. No write/create/delete access via UI (created by system only).

#### Scenario: Regular user cannot access logs

- **WHEN** a regular user attempts to access `news.source.log` records directly
- **THEN** access SHALL be denied

#### Scenario: Admin can read logs

- **WHEN** an admin accesses `news.source.log` or `news.article.log` records
- **THEN** read access SHALL be granted
