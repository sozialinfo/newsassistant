## MODIFIED Requirements

### Requirement: Unified log summary model

The system SHALL provide a `news.log` model with fields:
- `timestamp` (Datetime, required, default=now)
- `level` (Selection: success/warning/error, required)
- `category` (Selection: listing/extraction/email, required)
- `message` (Char, required)
- `duration` (Float, seconds, optional)
- `source_id` (Many2one to news.source, optional, ondelete=set null)
- `snapshot_id` (Many2one to news.snapshot, optional, ondelete=set null)
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

#### Scenario: Log created for snapshot extraction

- **WHEN** snapshot article extraction completes
- **THEN** a `news.log` record SHALL be created
- **THEN** `category` SHALL be `extraction`
- **THEN** `snapshot_id` SHALL reference the snapshot that was processed
- **THEN** `source_id` SHALL reference the snapshot's source

#### Scenario: Log created for email inbound

- **WHEN** an inbound email is received and processed
- **THEN** a `news.log` record SHALL be created
- **THEN** `category` SHALL be `email`
- **THEN** `snapshot_id` SHALL reference the created snapshot
- **THEN** `source_id` SHALL reference the source (existing or auto-created)

#### Scenario: Cascade behavior on source delete

- **WHEN** a `news.source` record is deleted
- **THEN** related `news.log` records SHALL have `source_id` set to null
- **THEN** the log records SHALL NOT be deleted
