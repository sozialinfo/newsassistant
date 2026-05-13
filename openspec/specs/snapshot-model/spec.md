## ADDED Requirements

### Requirement: News snapshot model
The system SHALL provide a `news.snapshot` model with fields: `name` (Char, computed from source name + timestamp), `source_id` (Many2one to news.source, required, ondelete=cascade), `raw_content` (Html, the captured content in HTML format), `captured_at` (Datetime, default=now, readonly), `article_ids` (One2many to news.article), `article_count` (Integer, computed), and `url` (Char, optional, index=True, the exact URL of the fetched page).

#### Scenario: Create a snapshot
- **WHEN** a snapshot is created with a source and raw HTML content
- **THEN** the record SHALL be saved with `captured_at` set to the current datetime
- **THEN** `article_count` SHALL be 0

#### Scenario: Computed name
- **WHEN** a snapshot is created for source "TechCrunch" at 2026-05-01 10:00
- **THEN** the `name` field SHALL reflect the source name and timestamp (e.g. "TechCrunch – 2026-05-01 10:00")

#### Scenario: Website snapshot stores URL
- **WHEN** a snapshot is created by the website scraper for "https://example.com/news/1"
- **THEN** the snapshot `url` field SHALL contain "https://example.com/news/1"

### Requirement: Snapshot auto-triggers article extraction
When a `news.snapshot` record is created, the system SHALL automatically enqueue a `_extract_articles()` queue job on the snapshot via the `root.newsassistant` channel.

#### Scenario: Snapshot creation enqueues extraction
- **WHEN** a `news.snapshot` record is created
- **THEN** a queue job for `_extract_articles` SHALL be enqueued on that snapshot
- **THEN** the job SHALL use the `root.newsassistant` channel

### Requirement: Snapshot article extraction method
The `news.snapshot` model SHALL provide a `_extract_articles()` method that reads `raw_content` (HTML) and calls the Infomaniak AI to extract articles. For each article found, it SHALL create a `news.article` record linked to the snapshot. If no articles are found or content is invalid, the method SHALL log a warning.

#### Scenario: Extract articles from HTML snapshot
- **WHEN** `_extract_articles()` is called on a snapshot with valid HTML containing 3 articles
- **THEN** 3 `news.article` records SHALL be created linked to the snapshot
- **THEN** each article SHALL have title, date, summary, content, and state=scraped

#### Scenario: Empty snapshot content
- **WHEN** `_extract_articles()` is called on a snapshot with empty `raw_content`
- **THEN** no articles SHALL be created
- **THEN** a `news.log` record SHALL be created with level `warning`

### Requirement: Snapshot list and form views
The system SHALL provide list and form views for `news.snapshot` accessible from the news source form. The list view SHALL show: name, source, captured_at, article_count. The form SHALL show all fields plus a list of related articles.

#### Scenario: View snapshots from source form
- **WHEN** an admin opens a news source form
- **THEN** a "Snapshots" tab or section SHALL show related snapshots with their article count

#### Scenario: Open snapshot form
- **WHEN** an admin opens a snapshot form
- **THEN** the raw_content, captured_at, and related articles SHALL be visible
