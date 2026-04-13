## MODIFIED Requirements

### Requirement: Stage 2 — Article content extraction

For each new (non-duplicate) article URL, the system SHALL fetch the article page via the Jina Reader API, and send the markdown content to the Infomaniak AI API. The AI SHALL extract a JSON object with: `title` (string), `date` (ISO 8601 string or null), `summary` (2-3 sentence summary), and `content` (full article text as clean HTML with semantic tags). The content SHALL be in the original language of the article. On success, the system SHALL set article `state` to `scraped`, clear `error_message` and `last_error_date`. On failure, the system SHALL set article `state` to `error`, set `error_message` to describe the failure, set `last_error_date` to current timestamp, and increment `retry_count`. The system SHALL create a `news.article.log` record for each extraction attempt.

#### Scenario: Extract content from an article page

- **WHEN** the system fetches and processes a new article page
- **THEN** a `news.article` record SHALL be created with title, date, summary, content, source_id, url, and scrape_date
- **THEN** article `state` SHALL be `scraped`

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
- **THEN** the `content` field SHALL NOT contain wrapper tags (html, head, body, nav, header, footer)

#### Scenario: JavaScript-heavy article page

- **WHEN** the article page content is rendered via JavaScript
- **THEN** the Jina Reader API SHALL execute the JavaScript and return the rendered content
- **THEN** the AI SHALL be able to extract article content from the rendered content

#### Scenario: PDF article

- **WHEN** the article URL points to a PDF document
- **THEN** the Jina Reader API SHALL extract text from the PDF and return it as markdown
- **THEN** the AI SHALL extract article content from the PDF text

#### Scenario: Extraction failure sets error state

- **WHEN** article extraction fails due to HTTP error or invalid AI response
- **THEN** article `state` SHALL be `error`
- **THEN** `error_message` SHALL describe the failure
- **THEN** `last_error_date` SHALL be current timestamp
- **THEN** `retry_count` SHALL be incremented by 1

#### Scenario: Extraction creates log entry

- **WHEN** the system attempts article extraction (success or failure)
- **THEN** a `news.article.log` record SHALL be created with timestamp, status, duration, and error_message (if failed)

## ADDED Requirements

### Requirement: Source scrape creates log entry

When Stage 1 listing scrape completes (success or failure), the system SHALL create a `news.source.log` record with timestamp, status, duration, articles_found (on success), and error_message (on failure).

#### Scenario: Successful scrape logged

- **WHEN** Stage 1 listing scrape completes successfully finding 5 new articles
- **THEN** a `news.source.log` record SHALL be created with `status='success'` and `articles_found=5`

#### Scenario: Failed scrape logged

- **WHEN** Stage 1 listing scrape fails with a connection timeout
- **THEN** a `news.source.log` record SHALL be created with `status='error'` and `error_message` describing the timeout
