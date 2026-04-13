## REMOVED Requirements

### Requirement: Source scrape log model

**Reason**: Replaced by unified `news.log` model which handles both source and article logging with a two-tier architecture (summary + details).

**Migration**: Logging now uses `news.log` with `category='listing'` for source scrapes. Detail entries are stored in `news.log.entry`.

### Requirement: Article scrape log model

**Reason**: Replaced by unified `news.log` model which handles both source and article logging with a two-tier architecture (summary + details).

**Migration**: Logging now uses `news.log` with `category='extraction'` for article extractions. Detail entries are stored in `news.log.entry`.

### Requirement: View full job log link

**Reason**: Replaced by unified log navigation. Job links are now part of the standard log list/form views with clickable `job_id` field.

**Migration**: Use the job link in the new Logs view or the Log tab on source/article forms.

### Requirement: Log model access control

**Reason**: Superseded by access control on new `news.log` and `news.log.entry` models.

**Migration**: Same admin-only read access applies to the new models.

## MODIFIED Requirements

### Requirement: Scrape history on source form

The source form view SHALL display a "Log" tab (renamed from "Scrape History") showing `news.log` records filtered to that source, with columns: Timestamp, Level (badge), Category, Article (if any), Message, Duration. The tab SHALL be visible to admin group only.

Each log entry SHALL provide clickable links to navigate to the linked article and job records.

#### Scenario: View source log

- **WHEN** an admin views a source form with 15 log entries
- **THEN** the "Log" tab SHALL display log entries in reverse chronological order
- **THEN** each entry SHALL show timestamp, level badge, category, linked article (if any), message, and duration

#### Scenario: Navigate to article from source log

- **WHEN** an admin clicks an article link on a log entry in the source Log tab
- **THEN** the linked `news.article` form SHALL open

#### Scenario: Log tab visibility

- **WHEN** a regular user views a source form
- **THEN** the "Log" tab SHALL NOT be visible

### Requirement: Extraction history on article form

The article form view SHALL display a "Log" tab (renamed from "History"/"Extraction History") showing `news.log` records filtered to that article, with columns: Timestamp, Level (badge), Message, Duration. The tab SHALL be visible to admin group only.

Each log entry SHALL provide a clickable link to navigate to the linked job record.

#### Scenario: View article log

- **WHEN** an admin views an article form with 5 log entries
- **THEN** the "Log" tab SHALL display all 5 entries in reverse chronological order
- **THEN** each entry SHALL show timestamp, level badge, message, and duration

#### Scenario: View log entry details

- **WHEN** an admin clicks on a log entry in the article Log tab
- **THEN** the log detail view SHALL open showing all entries including LLM interaction metadata

#### Scenario: Log tab visibility

- **WHEN** a regular user views an article form
- **THEN** the "Log" tab SHALL NOT be visible
