## MODIFIED Requirements

### Requirement: Stage 1 — Listing page discovery

The system SHALL fetch the listing page URL of a news source via the Jina Reader API and send the markdown content to the Infomaniak AI API. The AI SHALL extract a JSON array of article objects, each with `title` (string) and `url` (absolute URL string). The system SHALL use a system prompt that instructs the LLM to extract article links from markdown content, returning only actual news/blog article links. The prompt SHALL explicitly instruct the LLM to:
- Focus on the main content area, not navigation menus
- Look for articles with publication dates and specific headlines
- Exclude navigation links, category index pages (URLs often ending in `/news`), pagination links, and social media links
- Exclude generic titled links like "News" that lead to listing pages
- Prefer URLs containing article indicators such as `/artikel/`, `/article/`, `/post/`, `/blog/`, or date segments

#### Scenario: Discover articles from a listing page

- **WHEN** the system scrapes a listing page that contains 5 news article links in the main content area
- **THEN** the AI SHALL return a JSON array with 5 objects
- **THEN** each object SHALL have a `title` and an absolute `url`

#### Scenario: Exclude navigation menu links

- **WHEN** the listing page has a navigation menu with category links like "/themen/arbeit/news"
- **THEN** the AI SHALL NOT include these navigation links in the extracted articles
- **THEN** only articles from the main content area SHALL be extracted

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

### Requirement: Stage 2 — Article content extraction

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
- **THEN** a `news.log` record SHALL be created with level `warning`

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

- **WHEN** the system attempts article extraction (success, failure, or skipped)
- **THEN** a `news.log` record SHALL be created with timestamp, level, duration, and message
