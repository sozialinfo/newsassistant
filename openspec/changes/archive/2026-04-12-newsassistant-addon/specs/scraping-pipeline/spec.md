## ADDED Requirements

### Requirement: HTML pre-cleaning
The system SHALL pre-clean raw HTML before sending it to the AI. Pre-cleaning MUST remove `<script>`, `<style>`, `<nav>`, `<header>`, `<footer>`, `<aside>`, and `<form>` tags and their contents. It MUST also strip all HTML attributes (class, style, data-*, id, etc.) to reduce token count. The output SHALL be a simplified HTML string suitable for LLM consumption.

#### Scenario: Pre-clean a typical news page
- **WHEN** raw HTML contains `<nav>`, `<footer>`, `<script>`, and `<style>` blocks alongside article content
- **THEN** the pre-cleaned output SHALL contain only the article-relevant HTML
- **THEN** all `<nav>`, `<footer>`, `<script>`, `<style>`, `<aside>`, `<header>`, and `<form>` elements SHALL be removed
- **THEN** no HTML attributes SHALL remain on any element

#### Scenario: Truncation for large pages
- **WHEN** pre-cleaned HTML exceeds 30,000 characters
- **THEN** the output SHALL be truncated to 30,000 characters to stay within LLM context limits

### Requirement: Stage 1 — Listing page discovery
The system SHALL fetch the listing page URL of a news source via HTTP GET and send the pre-cleaned HTML to the Infomaniak AI API. The AI SHALL extract a JSON array of article objects, each with `title` (string) and `url` (absolute URL string). The system SHALL use a system prompt that instructs the LLM to return only actual news/blog article links, excluding navigation, category, and pagination links.

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
For each new (non-duplicate) article URL, the system SHALL fetch the article page via HTTP GET, pre-clean the HTML, and send it to the Infomaniak AI API. The AI SHALL extract a JSON object with: `title` (string), `date` (ISO 8601 string or null), `summary` (2-3 sentence summary), and `content` (full article text, clean plain text, no HTML, no boilerplate). The content SHALL be in the original language of the article.

#### Scenario: Extract content from an article page
- **WHEN** the system fetches and processes a new article page
- **THEN** a `news.article` record SHALL be created with title, date, summary, content, source_id, url, and scrape_date

#### Scenario: Article with no discernible date
- **WHEN** the AI cannot determine the article's publication date
- **THEN** the `date` field SHALL be set to null/empty

#### Scenario: Original language preserved
- **WHEN** an article is in German
- **THEN** the title, summary, and content SHALL be in German
- **WHEN** an article is in French
- **THEN** the title, summary, and content SHALL be in French

### Requirement: Infomaniak AI API integration
The system SHALL call the Infomaniak AI API at `https://api.infomaniak.com/2/ai/{product_id}/openai/v1/chat/completions` using the `qwen3` model. The API key SHALL be read from the `INFOMANIAK_AI_API_KEY` environment variable. The product ID SHALL be read from `ir.config_parameter` key `newsassistant.infomaniak_product_id` (default: `103794`).

#### Scenario: Successful AI API call
- **WHEN** the system sends a chat completion request with valid HTML
- **THEN** the API SHALL return a response with extracted article data in JSON format

#### Scenario: API key missing
- **WHEN** the `INFOMANIAK_AI_API_KEY` environment variable is not set
- **THEN** the system SHALL raise a `UserError` with a clear message explaining the missing configuration

### Requirement: HTTP request configuration
All HTTP requests to external websites SHALL include a reasonable User-Agent header (e.g. "NewsAssistant/1.0") and a timeout of 30 seconds. Requests to the Infomaniak AI API SHALL have a timeout of 120 seconds.

#### Scenario: HTTP request timeout
- **WHEN** an external website does not respond within 30 seconds
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
