## MODIFIED Requirements

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

### Requirement: Stage 2 — Article content extraction

For each new (non-duplicate) article URL, the system SHALL fetch the article page via the Jina Reader API, and send the markdown content to the Infomaniak AI API. The AI SHALL extract a JSON object with: `title` (string), `date` (ISO 8601 string or null), `summary` (2-3 sentence summary), and `content` (full article text as clean HTML with semantic tags). The content SHALL be in the original language of the article.

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

## REMOVED Requirements

### Requirement: HTML pre-cleaning

**Reason**: Jina Reader API returns clean markdown content with JavaScript already rendered. HTML pre-cleaning with BeautifulSoup is no longer needed.

**Migration**: The `clean_html()` function will remain available but is no longer called by the scraping pipeline. Remove calls to `clean_html()` in `_scrape_listing()` and `_fetch_and_extract()`.
