## ADDED Requirements

### Requirement: crawl4ai page fetching

The `newsassistant_website` module SHALL fetch all website pages (listing pages and article pages) using a self-hosted crawl4ai server. The crawl4ai server URL SHALL be configurable via the Odoo Settings UI, stored as `ir.config_parameter` key `newsassistant_website.crawl4ai_url`, defaulting to `http://crawl4ai:11235`. The fetch utility SHALL reside in `newsassistant_website`, not in `newsassistant` (base).

#### Scenario: Successful page fetch via crawl4ai

- **WHEN** the website module fetches a page URL with a valid crawl4ai server configured
- **THEN** the system SHALL make a POST request to `{crawl4ai_url}/crawl` with JSON body `{"urls": [target_url]}`
- **THEN** the system SHALL parse the response `results[0].markdown` as content
- **THEN** the system SHALL extract images from `results[0].media.images` array into a `{alt: src}` dict format
- **THEN** the system SHALL return the tuple `(content, images_dict)`

#### Scenario: Default crawl4ai URL

- **WHEN** no crawl4ai URL is configured in Settings
- **THEN** the system SHALL use `http://crawl4ai:11235` as the default

#### Scenario: Non-200 response from crawl4ai

- **WHEN** the crawl4ai server returns an HTTP status code other than 200
- **THEN** the system SHALL raise a `RetryableJobError` with a 300-second retry delay

#### Scenario: crawl4ai success=false in response

- **WHEN** the crawl4ai server returns `{"success": false}`
- **THEN** the system SHALL raise a `ValueError` with the error message from the response

### Requirement: crawl4ai timeout

The system SHALL use a timeout of 120 seconds for crawl4ai API requests.

#### Scenario: crawl4ai request times out

- **WHEN** the crawl4ai server does not respond within 120 seconds
- **THEN** the system SHALL raise a `RetryableJobError` with a 300-second retry delay

### Requirement: crawl4ai connection error handling

#### Scenario: crawl4ai server unreachable

- **WHEN** the crawl4ai server is unreachable (connection refused, DNS failure)
- **THEN** the system SHALL raise a `RetryableJobError` with a 300-second retry delay

### Requirement: Content length truncation

The system SHALL truncate content returned by crawl4ai to 30,000 characters to stay within LLM context limits.

#### Scenario: Large page content truncated

- **WHEN** crawl4ai returns content exceeding 30,000 characters
- **THEN** the system SHALL truncate the content to exactly 30,000 characters

## MODIFIED Requirements

### Requirement: Jina Reader API fetching

**Migration**: Replaced by crawl4ai server. Remove `JINA_API_KEY` environment variable; configure crawl4ai URL via Settings UI instead.

## REMOVED Requirements

### Requirement: Jina Reader API fetching

**Reason**: Replaced by self-hosted crawl4ai server
**Migration**: 
- Remove `JINA_API_KEY` from `.env` and `docker-compose.yml`
- Add `crawl4ai` service to `docker-compose.yml`
- Configure crawl4ai URL in Settings → News Assistant → Website Settings

### Requirement: Jina fetch timeout

**Reason**: Replaced by crawl4ai timeout handling

### Requirement: Jina transient error handling

**Reason**: Replaced by crawl4ai error handling (non-200 connection errors)

### Requirement: Jina permanent error handling

**Reason**: Replaced by crawl4ai error handling
