## Context

Currently, the `newsassistant_website` module fetches web pages using the Jina Reader API (`r.jina.ai`), an external SaaS service requiring a `JINA_API_KEY` environment variable. `fetch_page(url)` in `jina_utils.py` makes a GET request, parses the JSON response, and returns `(content_markdown, images_dict)`.

crawl4ai is an open-source, self-hosted web crawler that uses Chromium under the hood. It runs as a Docker container with a FastAPI server on port 11235, providing REST API endpoints (`POST /crawl`) that return markdown content plus media metadata. It handles JavaScript rendering, bot protection bypass, and content extraction — the same problems Jina solved, but self-hosted.

## Goals / Non-Goals

**Goals:**
- Replace Jina Reader API with self-hosted crawl4ai
- Maintain identical `fetch_page(url)` API contract: returns `(content, images_dict)`
- Make crawl4ai server URL configurable via Odoo Settings UI
- Remove `JINA_API_KEY` environment variable dependency

**Non-Goals:**
- No changes to any other module (`newsassistant_blog`, `newsassistant_email`, etc.)
- No changes to the AI extraction pipeline or kanban UI
- No performance optimization beyond what crawl4ai provides by default

## Decisions

**Decision 1: Self-hosted crawl4ai vs. external API**
- Chose self-hosted crawl4ai over Jina because it eliminates external dependency, API keys, rate limits, and data leaving the infrastructure
- crawl4ai runs Chromium natively, handling the same bot-protection scenarios Jina addressed

**Decision 2: Configurable URL via Settings UI**
- crawl4ai URL stored as `ir.config_parameter` key `newsassistant_website.crawl4ai_url`
- Default: `http://crawl4ai:11235` (Docker compose service name)
- Settings exposed in Odoo's Settings → News Assistant → Website Settings
- Same pattern as Pixabay API key in `newsassistant_blog`

**Decision 3: Replace, not dual-support**
- No fallback chain — crawl4ai is the sole fetch mechanism
- `RetryableJobError` handles transient failures as before
- Simpler code, no fallback complexity

**Decision 4: `/crawl` endpoint over `/md`**
- `/crawl` returns full JSON with markdown + media array
- `/md` returns markdown only (no images)
- Images are needed for header image selection, so `/crawl` is required

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| crawl4ai container crash brings down scraping | `restart: unless-stopped` in docker-compose; Odoo's `RetryableJobError` retries failed jobs |
| Chromium memory usage | `--shm-size=1g` allocated; browser pool reuses instances |
| crawl4ai API changes upstream | Pinned version tag (`unclecode/crawl4ai:latest` — consider pinning to specific version for production) |
| First crawl cold start latency | Browser pool keeps Chromium warm after first request |
| No authentication on crawl4ai endpoint | No need — internal Docker network only, not exposed externally |
