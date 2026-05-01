## MODIFIED Requirements

### Requirement: Jina Reader API fetching

The `newsassistant_website` module (not the base module) SHALL fetch all website pages (listing pages and article pages) using the Jina Reader API at `https://r.jina.ai/{url}`. The API key SHALL be read from the `JINA_API_KEY` environment variable. If the environment variable is not set, the system SHALL raise a `ValueError` with message "JINA_API_KEY environment variable not set". The Jina fetch utility SHALL reside in `newsassistant_website`, not in `newsassistant` (base).

#### Scenario: Successful page fetch via Jina

- **WHEN** the website module fetches a page URL with a valid `JINA_API_KEY` configured
- **THEN** the system SHALL make a GET request to `https://r.jina.ai/{url}`
- **THEN** the request SHALL include an `Authorization: Bearer {key}` header
- **THEN** the request SHALL include an `Accept: text/plain` header
- **THEN** the system SHALL return the markdown content from the response

#### Scenario: Missing JINA_API_KEY

- **WHEN** the website module attempts to fetch a page and `JINA_API_KEY` is not set
- **THEN** the system SHALL raise a `ValueError` with message "JINA_API_KEY environment variable not set"
- **THEN** no HTTP request SHALL be made

### Requirement: Jina fetch timeout

The system SHALL use a timeout of 60 seconds for Jina API requests (double the standard HTTP timeout of 30 seconds).

#### Scenario: Jina request times out

- **WHEN** the Jina API does not respond within 60 seconds
- **THEN** the system SHALL raise a `RetryableJobError` with a 300-second retry delay

### Requirement: Jina transient error handling

The system SHALL treat HTTP status codes 408, 429, 500, 502, 503, and 504 from the Jina API as transient errors and raise a `RetryableJobError`.

#### Scenario: Jina returns 429 rate limit

- **WHEN** the Jina API returns HTTP 429
- **THEN** the system SHALL raise a `RetryableJobError` with a 300-second retry delay

#### Scenario: Jina returns 503 unavailable

- **WHEN** the Jina API returns HTTP 503
- **THEN** the system SHALL raise a `RetryableJobError` with a 300-second retry delay

### Requirement: Jina permanent error handling

The system SHALL treat non-200 HTTP status codes (other than transient codes) from the Jina API as permanent errors and raise a `ValueError` with the status code and response excerpt.

#### Scenario: Jina returns 400 bad request

- **WHEN** the Jina API returns HTTP 400
- **THEN** the system SHALL raise a `ValueError` containing "Jina API error 400"

### Requirement: Content length truncation

The system SHALL truncate content returned by Jina to 30,000 characters (`MAX_CLEAN_HTML_LENGTH`) to stay within LLM context limits.

#### Scenario: Large page content truncated

- **WHEN** Jina returns content exceeding 30,000 characters
- **THEN** the system SHALL truncate the content to exactly 30,000 characters
