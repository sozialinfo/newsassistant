## ADDED Requirements

### Requirement: Stage 1 — Listing page discovery

The system SHALL fetch the listing page URL of a news source via the Jina Reader API and send the markdown content to the Infomaniak AI API. The AI SHALL extract a JSON array of article objects, each with `title` (string) and `url` (absolute URL string). The system SHALL use a system prompt that instructs the LLM to extract article links from markdown content, returning only actual news/blog article links, excluding navigation, category, and pagination links.

#### Scenario: Discover articles from a listing page

- **WHEN** the system scrapes a listing page that contains 5 news article links
- **THEN** the AI SHALL return a JSON array with 5 objects
- **THEN** each object SHALL have a `title` and an absolute `url`

#### Scenario: Handle relative URLs

- **WHEN** the AI returns a relative URL for an article
- **THEN** the system SHALL resolve it to an absolute URL using the source's base URL

#### Scenario: Handle AI returning invalid JSON

- **WHEN** the AI response cannot be parsed as valid JSON
- **THEN** the system SHALL log the error on the source record and skip this scrape cycle

#### Scenario: JavaScript-heavy listing page

- **WHEN** the listing page content is rendered via JavaScript (e.g., Gatsby, Next.js)
- **THEN** the Jina Reader API SHALL execute the JavaScript and return the rendered content
- **THEN** the AI SHALL be able to extract article links from the rendered content

### Requirement: URL-based deduplication

Before processing a discovered article URL, the system SHALL check if a `news.article` record with that URL already exists. If yes, the article SHALL be skipped entirely (no HTTP fetch, no AI call). URLs SHALL be normalized by stripping trailing slashes and URL fragments before comparison.

#### Scenario: Skip known article

- **WHEN** Stage 1 discovers an article URL that already exists in `news.article`
- **THEN** the system SHALL NOT fetch the article page
- **THEN** the system SHALL NOT make an AI extraction call for that article

#### Scenario: Normalize URLs for dedup

- **WHEN** Stage 1 discovers URL "https://example.com/article/1/" and "https://example.com/article/1" already exists
- **THEN** both URLs SHALL normalize to the same value
- **THEN** the article SHALL be skipped as a duplicate

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

### Requirement: Infomaniak AI API integration

The system SHALL call the Infomaniak AI API at `https://api.infomaniak.com/2/ai/{product_id}/openai/v1/chat/completions` using the `qwen3` model. The API key SHALL be read from the `INFOMANIAK_AI_API_KEY` environment variable. The product ID SHALL be read from `ir.config_parameter` key `newsassistant.infomaniak_product_id` (default: `103794`).

#### Scenario: Successful AI API call

- **WHEN** the system sends a chat completion request with valid content
- **THEN** the API SHALL return a response with extracted article data in JSON format

#### Scenario: API key missing

- **WHEN** the `INFOMANIAK_AI_API_KEY` environment variable is not set
- **THEN** the system SHALL raise a `UserError` with a clear message explaining the missing configuration

### Requirement: HTTP request configuration

All HTTP requests to external websites SHALL include a reasonable User-Agent header (e.g. "NewsAssistant/1.0") and a timeout of 30 seconds. Requests to the Infomaniak AI API SHALL have a timeout of 120 seconds. Requests to the Jina Reader API SHALL have a timeout of 60 seconds.

#### Scenario: HTTP request timeout

- **WHEN** an external website does not respond within the configured timeout
- **THEN** the request SHALL time out and raise an appropriate error

#### Scenario: User-Agent header sent

- **WHEN** the system makes an HTTP request to a news source
- **THEN** the request SHALL include a User-Agent header identifying the scraper

### Requirement: Source state update after scrape

After a successful listing scrape (Stage 1 completes without error), the source's `last_scrape_date` SHALL be updated to the current timestamp and `state` SHALL be set to `'ok'`.

#### Scenario: Successful scrape updates source

- **WHEN** Stage 1 completes successfully for a source
- **THEN** `last_scrape_date` SHALL be set to the current datetime
- **THEN** `state` SHALL be `'ok'`

### Requirement: Source scrape creates log entry

When Stage 1 listing scrape completes (success or failure), the system SHALL create a `news.source.log` record with timestamp, status, duration, articles_found (on success), and error_message (on failure).

#### Scenario: Successful scrape logged

- **WHEN** Stage 1 listing scrape completes successfully finding 5 new articles
- **THEN** a `news.source.log` record SHALL be created with `status='success'` and `articles_found=5`

#### Scenario: Failed scrape logged

- **WHEN** Stage 1 listing scrape fails with a connection timeout
- **THEN** a `news.source.log` record SHALL be created with `status='error'` and `error_message` describing the timeout
