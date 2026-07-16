## MODIFIED Requirements

### Requirement: News snapshot model
The system SHALL provide a `news.snapshot` model with fields: `name` (Char, computed from source name + timestamp), `source_id` (Many2one to news.source, required, ondelete=cascade), `raw_content` (Html, the captured content in HTML format), `captured_at` (Datetime, default=now, readonly), `article_ids` (One2many to news.article), `article_count` (Integer, computed), `url` (Char, optional, index=True, the exact URL of the fetched page), `is_listing` (Boolean, default=False), `parent_id` (Many2one to news.snapshot, optional, index=True), and `child_ids` (One2many to news.snapshot, inverse of parent_id).

#### Scenario: Create a snapshot
- **WHEN** a snapshot is created with a source and raw HTML content
- **THEN** the record SHALL be saved with `captured_at` set to the current datetime
- **THEN** `article_count` SHALL be 0
- **THEN** `is_listing` SHALL be `False` by default

#### Scenario: Create a listing snapshot
- **WHEN** a snapshot is created with `is_listing=True`
- **THEN** the record SHALL be saved with `is_listing=True`
- **THEN** `_discover_articles()` SHALL be enqueued instead of `_extract_articles()`

#### Scenario: Create a child snapshot
- **WHEN** a snapshot is created with `parent_id` set to a listing snapshot
- **THEN** `is_listing` SHALL default to `False`
- **THEN** `_extract_articles()` SHALL be enqueued (standard non-listing behavior)

#### Scenario: Computed name
- **WHEN** a snapshot is created for source "TechCrunch" at 2026-05-01 10:00
- **THEN** the `name` field SHALL reflect the source name and timestamp (e.g. "TechCrunch – 2026-05-01 10:00")

#### Scenario: Website snapshot stores URL
- **WHEN** a snapshot is created by the website scraper for "https://example.com/news/1"
- **THEN** the snapshot `url` field SHALL contain "https://example.com/news/1"

### Requirement: Snapshot auto-triggers articles or discovery
When a `news.snapshot` record is created:
- if `is_listing=True`, the system SHALL enqueue a `_discover_articles()` queue job
- if `is_listing=False`, the system SHALL enqueue a `_extract_articles()` queue job (existing behavior preserved)
All jobs SHALL use the `root.newsassistant` channel.

#### Scenario: Non-listing snapshot creation enqueues extraction
- **WHEN** a non-listing `news.snapshot` record is created
- **THEN** a queue job for `_extract_articles` SHALL be enqueued on that snapshot
- **THEN** the job SHALL use the `root.newsassistant` channel

#### Scenario: Listing snapshot creation enqueues discovery
- **WHEN** a listing `news.snapshot` record is created
- **THEN** a queue job for `_discover_articles` SHALL be enqueued on that snapshot
- **THEN** the job SHALL use the `root.newsassistant` channel

### Requirement: Snapshot article extraction method
The `news.snapshot` model SHALL provide a `_extract_articles()` method that reads `raw_content` (HTML) and calls the Infomaniak AI to extract articles. For each article found, it SHALL create a `news.article` record linked to the snapshot. If no articles are found or content is invalid, the method SHALL log a warning. This method SHALL operate on non-listing snapshots only.

#### Scenario: Extract articles from HTML snapshot
- **WHEN** `_extract_articles()` is called on a child snapshot with valid HTML
- **THEN** a `news.article` record SHALL be created linked to the snapshot
- **THEN** the article SHALL have title, date, summary, content, and state=scraped

#### Scenario: Empty snapshot content
- **WHEN** `_extract_articles()` is called on a snapshot with empty `raw_content`
- **THEN** no articles SHALL be created
- **THEN** a `news.log` record SHALL be created with level `warning`

### Requirement: _discover_articles() base method
The `news.snapshot` model SHALL provide a `_discover_articles()` method that raises `NotImplementedError`. Modules that create listing snapshots SHALL override this method to discover child articles from the listing content.

#### Scenario: Base _discover_articles raises error
- **WHEN** `_discover_articles()` is called on a base snapshot without override
- **THEN** a `NotImplementedError` SHALL be raised

### Requirement: Snapshot list and form views
The system SHALL provide list and form views for `news.snapshot` accessible from the news source form. The list view SHALL show: name, source, captured_at, article_count, is_listing. The form SHALL show all fields plus parent/child links and a list of related articles.

#### Scenario: View snapshots from source form
- **WHEN** an admin opens a news source form
- **THEN** a "Snapshots" tab or section SHALL show related snapshots with their article count

#### Scenario: Open snapshot form
- **WHEN** an admin opens a listing snapshot form
- **THEN** `is_listing`, `raw_content`, `captured_at`, and child snapshots SHALL be visible

#### Scenario: Open child snapshot form
- **WHEN** an admin opens a child snapshot form
- **THEN** `parent_id`, `raw_content`, `captured_at`, and the linked article SHALL be visible

## REMOVED Requirements

### Requirement: Snapshot always enqueues extraction
**Reason**: Listing snapshots now enqueue `_discover_articles()` instead. Non-listing snapshots still enqueue `_extract_articles()`.
**Migration**: See snapshot-hierarchy spec for the new behavior.

### Requirement: Single-article extraction prompt requires update
**Reason**: The single-article extraction prompt is unchanged — it now operates on child snapshots which always contain a single article. Listing snapshots go through `_discover_articles()` instead.
**Migration**: No migration needed. Existing prompt still valid for child snapshots.