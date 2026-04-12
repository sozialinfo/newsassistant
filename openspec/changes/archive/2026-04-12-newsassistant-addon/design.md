## Context

This is a greenfield Odoo 18 addon in an empty `addons/` directory. The project already has a Docker Compose setup with Odoo 18 and PostgreSQL. OCA web addons are mounted. The container has `beautifulsoup4`, `lxml`, and `requests` pre-installed — no additional Python packages are needed.

The addon must scrape ~60 Swiss social-sector websites with wildly different HTML structures (Drupal, WordPress, TYPO3, custom CMSes) and present clean article content to users. The Infomaniak AI API (OpenAI-compatible, product ID 103794) serves as the universal HTML-to-structured-data parser, eliminating the need for per-source CSS selector configurations.

OCA `queue_job` is available at `/home/debian/shared/odoo-src/18.0/oca/queue/` and will handle background job processing.

## Goals / Non-Goals

**Goals:**
- Fully automated daily scraping of all active news sources
- Clean, fluff-free article content presented in a kanban board
- Resilient pipeline: individual source/article failures don't block others
- Deduplication: never re-fetch or re-process known article URLs
- Concurrency-controlled scraping via queue_job channels
- Comprehensive test coverage within Odoo's standard test framework
- Clear documentation (README.md, agents.md with definition of done)

**Non-Goals:**
- Per-source CSS selector configuration (AI handles all extraction)
- Translation of articles (content stays in original language)
- Full-text search or semantic analysis of articles
- Export, reporting, or integration with other Odoo modules
- User-configurable scrape frequency (fixed daily cron)
- Change detection on already-known articles
- JavaScript-rendered page support (all sampled sources are server-rendered)

## Decisions

### 1. Two-stage AI extraction pipeline

**Decision**: Stage 1 sends pre-cleaned listing page HTML to the LLM to discover article URLs and titles. Stage 2 fetches each new article URL and sends its pre-cleaned HTML to the LLM to extract title, date, summary, and clean full text.

**Alternatives considered**:
- *Per-source CSS selectors*: Fast and cheap but requires 60+ configurations, breaks on redesign, unmaintainable
- *AI-only (no pre-cleaning)*: Simpler but sends full HTML including nav/footer/scripts, wastes tokens, may hit context limits
- *RSS/Atom feeds*: Most of these sources don't offer feeds; checked several and found none

**Rationale**: The hybrid approach (pre-clean HTML with BeautifulSoup, then AI extraction) keeps token costs manageable while being universally applicable to any HTML structure. Pre-cleaning strips `<script>`, `<style>`, `<nav>`, `<header>`, `<footer>`, `<aside>`, `<form>` tags and removes class/style/data attributes before sending to the LLM.

### 2. OCA queue_job with built-in runner

**Decision**: Use `queue_job` as a server-wide module with the built-in job runner (not `queue_job_cron_jobrunner`). Configure a dedicated channel `root.newsassistant` with capacity 4.

**Alternatives considered**:
- *queue_job_cron_jobrunner*: Simpler setup but no channel capacity enforcement — we'd risk 60 concurrent HTTP requests to external sites
- *Plain ir.cron with sequential processing*: Simple but slow (60 sources × N articles processed serially)

**Rationale**: Channel capacity control is important. We're making HTTP requests to external websites and API calls to Infomaniak. A capacity of 4 means at most 4 concurrent scrape operations, preventing both rate-limiting issues and resource exhaustion. The built-in runner requires adding `queue_job` to `server_wide_modules` in `odoo.conf` and setting `workers >= 2`.

### 3. Job fan-out pattern

**Decision**: One `ir.cron` fires daily and calls `_cron_scrape_all()`. This iterates active sources and calls `source.with_delay()._scrape_listing()` for each. Each listing job discovers new article URLs and calls `article.with_delay()._fetch_and_extract()` for each new article.

```
ir.cron (daily)
    └─▶ _cron_scrape_all()
            ├─▶ source_1.with_delay()._scrape_listing()
            │       ├─▶ article_A.with_delay()._fetch_and_extract()
            │       └─▶ article_B.with_delay()._fetch_and_extract()
            ├─▶ source_2.with_delay()._scrape_listing()
            │       └─▶ article_C.with_delay()._fetch_and_extract()
            └─▶ ...
```

**Rationale**: This gives maximum parallelism within channel capacity limits. Each job is independent — a failure in one source or article doesn't affect others. Queue job retry logic handles transient HTTP errors.

### 4. Deduplication by article URL

**Decision**: Before creating an article record, check if the URL already exists in `news.article`. If yes, skip it entirely. The URL is stored normalized (stripped of trailing slashes, fragments, and common tracking parameters).

**Alternatives considered**:
- *Content hash deduplication*: More robust against URL changes but requires fetching the article first, defeating the purpose
- *Title-based deduplication*: Too fragile, different sources might use similar titles

**Rationale**: URL-based dedup is simple, fast (database index lookup), and catches 99% of duplicates. It runs before the expensive Stage 2 fetch+AI call, saving both HTTP requests and API tokens.

### 5. Infomaniak API integration

**Decision**: Use `requests` library to call the Infomaniak API directly at `https://api.infomaniak.com/2/ai/103794/openai/v1/chat/completions`. The API key is stored as environment variable `INFOMANIAK_AI_API_KEY`, loaded from `.env` via docker-compose, and read via `os.environ` in Python. The product ID is stored as `ir.config_parameter` (`newsassistant.infomaniak_product_id`) defaulting to `103794`.

**Alternatives considered**:
- *OpenAI Python SDK*: Would work (API is compatible) but adds an external dependency not present in the container
- *ir.config_parameter for API key*: Stores secrets in the database, less secure than environment variables

**Rationale**: `requests` is already in the container. Environment variable for the secret follows security best practices. Product ID as `ir.config_parameter` allows changing it without restarting the container.

### 6. AI prompt design

**Decision**: Two distinct system prompts:

- **Stage 1 (listing discovery)**: "Given this HTML from a news listing page, extract all news article links. Return a JSON array of objects with `title` and `url` fields. Only include actual news/blog article links, not navigation, category, or pagination links. Return absolute URLs."

- **Stage 2 (article extraction)**: "Given this HTML from a news article page, extract the article content. Return a JSON object with `title`, `date` (ISO 8601 or null), `summary` (2-3 sentence summary of the article), and `content` (the full article text, clean, no HTML, no navigation or boilerplate). Keep the original language."

**Rationale**: Separate prompts for separate tasks. JSON output format enables structured parsing. The "keep the original language" instruction prevents the model from translating German/French content.

### 7. Data model

**Models**:

- **`news.source`**: `name` (Char), `url` (Char), `active` (Boolean), `last_scrape_date` (Datetime), `state` (Selection: ok/error), `error_message` (Text), `article_count` (Integer, computed)

- **`news.article`**: `title` (Char), `source_id` (Many2one → news.source), `url` (Char, indexed, unique), `date` (Date), `summary` (Text), `content` (Text), `stage_id` (Many2one → news.article.stage), `scrape_date` (Datetime)

- **`news.article.stage`**: `name` (Char), `sequence` (Integer), `fold` (Boolean). Default stages via data XML: New (seq 10), Relevant (seq 20), Archived (seq 30, folded), Discarded (seq 40, folded).

### 8. Kanban view design

**Decision**: Kanban view on `news.article` grouped by `stage_id`. Each card shows: title (bold), source name, date, and truncated summary. Click opens form with full content. Filter/group by source, date range.

### 9. Error handling and retries

**Decision**: Use `queue_job`'s built-in retry mechanism. Scraping jobs raise `RetryableJobError` on transient HTTP errors (timeout, 5xx). Permanent failures (404, parse errors) are logged on the source record (`state='error'`, `error_message` set) and the job completes normally (no retry). AI API errors (rate limit, timeout) raise `RetryableJobError`. Malformed AI responses (invalid JSON) are logged and skipped.

**Retry pattern**: `{1: 300, 3: 900, 5: 3600}` — retry after 5 min, then 15 min, then 1 hour.

### 10. Docker and server configuration

**Changes to existing files**:
- `docker-compose.yml`: Add volume mount for OCA queue addons, add `INFOMANIAK_AI_API_KEY` environment variable from `.env`
- `odoo.conf`: Add `server_wide_modules = web,queue_job` and add OCA queue path to `addons_path`. Add `[queue_job]` section with channel config.
- `.env`: New file with `INFOMANIAK_AI_API_KEY=aDvbaRabNHdS7SFKDFA7cC6z_OnLtSA6fsO0trEKAN-dgNlmV_viiB_lH2XDbv8W7lCdMQi5nf5U7I3s`
- `.gitignore`: Add `.env`

## Risks / Trade-offs

- **[AI extraction quality]** → LLM may misidentify article links or extract noisy content. Mitigation: careful prompt engineering, pre-cleaning HTML aggressively, and the human triage step in kanban catches errors.

- **[Token costs]** → Sending full page HTML (even pre-cleaned) to the LLM for 60 sources + N articles daily. Mitigation: aggressive pre-cleaning (strip tags, attributes), deduplication skips known articles, and most sources only publish 1-3 new articles per day.

- **[External site changes]** → Websites may redesign, add bot protection, or go offline. Mitigation: per-source error tracking, retry logic, error state visible in the UI. The AI-based approach is more resilient to redesigns than CSS selectors.

- **[Rate limiting by sources]** → Scraping 60 sites with follow-links could be seen as aggressive. Mitigation: queue_job channel capacity limits concurrent requests to 4; add reasonable request timeouts and User-Agent header.

- **[Infomaniak API availability]** → API downtime blocks all extraction. Mitigation: RetryableJobError with escalating retry pattern. Jobs queue up and process when API returns.

- **[Large listing pages]** → Some sources may have hundreds of articles on one listing page, producing HTML that exceeds LLM context window. Mitigation: truncate pre-cleaned HTML to a reasonable token budget (e.g. first 30,000 characters); most recent articles appear first on listing pages.
