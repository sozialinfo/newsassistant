## MODIFIED Requirements

### Requirement: News source model
The system SHALL provide a `news.source` model with fields: `name` (Char, required), `url` (Char, required for website sources), `source_type` (Selection: website/email, required, default=website), `sender_domain` (Char, for email sources), `active` (Boolean, default True), `last_scrape_date` (Datetime), `state` (Selection: ok/error, default ok), `error_message` (Text), `article_count` (Integer, computed from related articles via snapshots), `snapshot_ids` (One2many to news.snapshot), and `language` (Char, optional, the ISO 639-1 language code of the source content, e.g. "de", "fr", "en"; auto-detected by LLM during listing scrape).

#### Scenario: Create a news source
- **WHEN** a user creates a new `news.source` record with name "Test Source" and url "https://example.com/news"
- **THEN** the record SHALL be created with `active=True`, `state='ok'`, `error_message` empty, `article_count=0`, and `source_type='website'`

#### Scenario: Computed article count via snapshots
- **WHEN** a news source has 2 snapshots, one with 3 articles and one with 2 articles
- **THEN** the `article_count` field SHALL return 5

#### Scenario: Language auto-detected during listing scrape
- **WHEN** the listing scraper processes a German-language source
- **THEN** the source `language` field SHALL be updated to "de"

#### Scenario: Language field is user-editable
- **WHEN** an admin opens the source form and changes the `language` field
- **THEN** the change SHALL be saved and used for subsequent blog post creation
