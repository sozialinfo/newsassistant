## MODIFIED Requirements

### Requirement: Stage 2 — Article content extraction

For each non-listing `news.snapshot` (child snapshot), the system SHALL read `raw_content` (HTML) and send it to the Infomaniak AI API. The AI prompt SHALL first validate whether the content is a single article. If NOT an article, the AI SHALL return `{is_article: false, reason: "..."}` and no article SHALL be created from this snapshot. If it IS an article, the AI SHALL extract a JSON object with: `is_article: true`, `title` (string), `date` (ISO 8601 string or null), `summary` (2-3 sentence summary), and `content` (full article text as clean HTML with semantic tags). The content SHALL be in the original language of the article. On successful extraction, the system SHALL create a `news.article` record with `state='scraped'`. On extraction failure, the system SHALL log a warning. The system SHALL create a `news.log` record for each extraction attempt.

Listing snapshots SHALL NOT enter this pipeline — they SHALL use `_discover_articles()` to produce child snapshots instead.

#### Scenario: Extract content from a child snapshot
- **WHEN** the system processes a child snapshot with valid HTML containing a single article
- **THEN** a `news.article` record SHALL be created with title, date, summary, content, state=scraped, and snapshot_id linking to the child snapshot

#### Scenario: Non-article child snapshot detected during extraction
- **WHEN** the child snapshot HTML does not represent a single article
- **THEN** no `news.article` SHALL be created
- **THEN** a `news.log` record SHALL be created with level `warning` and a message explaining why

#### Scenario: Article with no discernible date
- **WHEN** the AI cannot determine the article's publication date
- **THEN** the `date` field SHALL be null/empty

#### Scenario: Original language preserved
- **WHEN** an article is in German
- **THEN** the title, summary, and content SHALL be in German
- **WHEN** an article is in French
- **THEN** the title, summary, and content SHALL be in French

#### Scenario: Content field contains HTML
- **WHEN** the AI extracts article content from HTML input
- **THEN** the `content` field SHALL contain clean HTML with semantic tags (h2, h3, p, ul, ol, li, strong, em)
- **THEN** the `content` field SHALL NOT contain wrapper tags (html, head, body, nav, header, footer)

#### Scenario: Extraction failure creates log entry
- **WHEN** article extraction fails due to invalid AI response
- **THEN** a `news.log` record SHALL be created with level `error`
- **THEN** the snapshot SHALL remain with its `raw_content` intact

### Requirement: Stage 2a — Listing article discovery (new stage)

Listing snapshots (`is_listing=True`) SHALL go through `_discover_articles()` before any article extraction can occur. This stage identifies individual article items within the listing content (URLs for websites, sections for newsletters) and creates a child snapshot for each.

#### Scenario: Website listing produces child snapshots via URL extraction
- **WHEN** `_discover_articles()` runs on a website listing snapshot
- **THEN** the AI SHALL extract article URLs from the listing content
- **THEN** each new URL SHALL be fetched via crawl4ai and stored as a child snapshot

#### Scenario: Newsletter listing produces child snapshots via section extraction
- **WHEN** `_discover_articles()` runs on a newsletter listing snapshot
- **THEN** the AI SHALL extract article sections from the newsletter HTML
- **THEN** each section SHALL be stored as a child snapshot with inline content

### Requirement: Infomaniak AI API integration

The system SHALL call the Infomaniak AI API at `https://api.infomaniak.com/2/ai/{product_id}/openai/v1/chat/completions` using the `qwen3` model. The API key SHALL be read from the `INFOMANIAK_AI_API_KEY` environment variable. The product ID SHALL be read from `ir.config_parameter` key `newsassistant.infomaniak_product_id` (default: `103794`).

#### Scenario: Successful AI API call
- **WHEN** the system sends a chat completion request with valid content
- **THEN** the API SHALL return a response with extracted article data in JSON format

#### Scenario: API key missing
- **WHEN** the `INFOMANIAK_AI_API_KEY` environment variable is not set
- **THEN** the system SHALL raise a `UserError` with a clear message explaining the missing configuration

### Requirement: HTTP request configuration

All HTTP requests to external websites SHALL include a reasonable User-Agent header (e.g. "NewsAssistant/1.0") and a timeout of 30 seconds. Requests to the Infomaniak AI API SHALL have a timeout of 120 seconds. Requests to crawl4ai SHALL have a timeout of 120 seconds.

#### Scenario: HTTP request timeout
- **WHEN** an external website does not respond within the configured timeout
- **THEN** the request SHALL time out and raise an appropriate error

#### Scenario: User-Agent header sent
- **WHEN** the system makes an HTTP request to a news source
- **THEN** the request SHALL include a User-Agent header identifying the scraper