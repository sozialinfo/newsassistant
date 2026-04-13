## MODIFIED Requirements

### Requirement: Article Extraction (Stage 2)

For each new (non-duplicate) article URL, the system SHALL fetch the article page via the Jina Reader API, and send the markdown content to the Infomaniak AI API. The AI prompt SHALL first validate whether the content is a single article. If NOT an article, the AI SHALL return `{is_article: false, reason: "..."}` and the system SHALL mark the stub as `skipped`. If it IS an article, the AI SHALL extract a JSON object with: `is_article: true`, `title` (string), `date` (ISO 8601 string or null), `summary` (2-3 sentence summary), and `content` (full article text as clean HTML with semantic tags). The content SHALL be in the original language of the article. On successful extraction, the system SHALL set article `state` to `scraped`, clear `error_message` and `last_error_date`. On extraction failure, the system SHALL set article `state` to `error`, set `error_message` to describe the failure, set `last_error_date` to current timestamp, and increment `retry_count`. On validation failure (not an article), the system SHALL set article `state` to `skipped` and set `error_message` to describe why it's not an article. The system SHALL create a `news.log` record for each extraction attempt.

#### Scenario: Extract content from an article page

- **WHEN** the system fetches and processes a new article page that is validated as an article
- **THEN** a `news.article` record SHALL be updated with title, date, summary, content, and scrape_date
- **THEN** article `state` SHALL be `scraped`

#### Scenario: Non-article page detected during extraction

- **WHEN** the system fetches a URL and the AI determines it is not a single article
- **THEN** article `state` SHALL be `skipped`
- **THEN** `error_message` SHALL be set to "Not an article: {reason from AI}"
- **THEN** `scrape_date` SHALL be set to current timestamp
- **THEN** a `news.log` record SHALL be created with level `info`

#### Scenario: Article with no discernible date

- **WHEN** the AI cannot determine the article's publication date
- **THEN** the `date` field SHALL be set to null/empty

#### Scenario: Original language preserved

- **WHEN** an article is in German
- **THEN** the title, summary, and content SHALL be in German
- **WHEN** an article is in French
- **THEN** the title, summary, and content SHALL be in French

#### Scenario: Content field contains HTML

- **WHEN** the AI extracts article content from markdown input
- **THEN** the `content` field SHALL contain clean HTML with semantic tags (h2, h3, p, ul, ol, li, strong, em)
