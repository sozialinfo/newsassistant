## Requirements

### Requirement: Snapshot records source URL
The `news.snapshot` model SHALL have a `url` field (Char, optional, index=True) storing the exact URL of the web page that was fetched to produce the snapshot. For email-based snapshots the field SHALL be left empty.

#### Scenario: Website snapshot has URL
- **WHEN** the website scraper creates a snapshot for an article page at "https://example.com/news/article-1"
- **THEN** the snapshot `url` field SHALL contain "https://example.com/news/article-1"

#### Scenario: Email snapshot has no URL
- **WHEN** an email-based snapshot is created
- **THEN** the snapshot `url` field SHALL be empty

#### Scenario: Snapshot form shows URL
- **WHEN** an admin opens a snapshot form for a website snapshot
- **THEN** the `url` field SHALL be visible as a clickable URL link
