## Context

The newsassistant scraping pipeline currently fetches pages directly via HTTP requests. This fails for JavaScript-heavy sites (Gatsby, Next.js, SPAs) where content is rendered client-side. The Jina Reader API (`r.jina.ai`) executes JavaScript in a headless browser and returns rendered content as markdown.

Currently:
- `news_source.py`: `_scrape_listing()` uses `requests.get()` + `clean_html()` + AI extraction
- `news_article.py`: `_fetch_and_extract()` uses `requests.get()` with Jina fallback only on HTTP 403
- HTML is pre-cleaned with BeautifulSoup before sending to AI
- PDF handling uses `pdfminer` library

## Goals / Non-Goals

**Goals:**
- All page fetches use Jina Reader API as the primary (and only) method
- Unified `fetch_page()` function for both listing and article fetching
- Simplified codebase by removing HTML cleaning, PDF handling, and fallback logic
- AI prompts accept markdown input (Jina's native output format)
- Article `content` field remains HTML for proper display in Odoo

**Non-Goals:**
- Per-source configuration to choose fetch method (all sources use Jina)
- Fallback to direct HTTP if Jina fails (Jina is required)
- Caching or rate limiting for Jina API (out of scope)
- Changing the AI extraction logic or prompts beyond input format

## Decisions

### Decision 1: Unified `fetch_page()` utility function

Create a single `fetch_page(url)` function in `news_source.py` that:
- Reads `JINA_API_KEY` from environment (required)
- Calls `https://r.jina.ai/{url}` with Bearer auth
- Returns markdown content (truncated to `MAX_CLEAN_HTML_LENGTH`)
- Raises `RetryableJobError` on transient failures (timeout, 5xx)
- Raises `ValueError` on permanent failures or missing API key

**Rationale**: Centralizes all fetch logic, eliminates code duplication between `NewsSource` and `NewsArticle`, makes behavior consistent.

**Alternatives considered**:
- Keep separate fetch methods per model: Rejected (duplication, inconsistent behavior)
- Create a separate utility module: Considered, but `news_source.py` already has shared utilities

### Decision 2: Jina markdown output, AI produces HTML content

- Jina returns markdown via `Accept: text/plain` header
- AI prompts updated to describe input as "markdown content"
- AI continues to output HTML for the `content` field (existing behavior)

**Rationale**: Markdown is Jina's native format and cleaner for AI consumption. Keeping HTML output for `content` preserves the existing Odoo UI rendering without changes.

**Alternatives considered**:
- Request HTML from Jina (`Accept: text/html`): Rejected (markdown is cleaner, less tokens)
- Store markdown and render in UI: Rejected (requires field type change, JS widget, migration)

### Decision 3: Remove all fallback paths

- No direct HTTP fallback if Jina fails
- No fallback if `JINA_API_KEY` is not set (raise error immediately)
- Remove 403-specific Jina fallback logic (Jina is always used)

**Rationale**: Simplifies code significantly. One code path is easier to maintain and debug. Users must configure Jina API key.

### Decision 4: Remove PDF handling code

Jina Reader handles PDFs natively, extracting text and returning markdown. The `pdfminer` dependency and PDF detection logic can be removed.

**Rationale**: Less code, fewer dependencies, consistent behavior for all content types.

### Decision 5: Keep `clean_html()` available but unused by pipeline

The `clean_html()` function will remain in the codebase but won't be called by the scraping pipeline. It may be useful for other purposes or future features.

**Rationale**: Low-risk to keep, allows rollback if needed, may have other uses.

## Risks / Trade-offs

**[Risk] Jina API dependency** → All scraping now depends on external API availability. Mitigation: Jina has good uptime; `RetryableJobError` handles transient failures with backoff.

**[Risk] Increased API costs** → Every fetch now uses Jina API instead of free direct HTTP. Mitigation: Accept as cost of reliability; monitor usage.

**[Risk] Jina API key becomes mandatory** → Existing deployments without key will break. Mitigation: Clear error message; document in setup instructions.

**[Risk] Jina rate limits** → High-volume scraping may hit rate limits. Mitigation: Queue jobs already provide natural rate limiting; monitor and adjust if needed.

**[Trade-off] Latency increase** → Jina adds latency vs direct HTTP (headless browser rendering). Accepted: Reliability more important than speed for background jobs.
