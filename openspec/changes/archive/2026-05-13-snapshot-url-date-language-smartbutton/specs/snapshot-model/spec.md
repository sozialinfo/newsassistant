## MODIFIED Requirements

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
