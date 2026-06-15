## Why

Replace the external Jina Reader API dependency with a self-hosted crawl4ai container. This eliminates reliance on a third-party SaaS API (no API key needed, no rate limits, no external downtime), gives full control over the scraping pipeline, and keeps all data within the infrastructure.

## What Changes

- **New** `crawl4ai` Docker service in `docker-compose.yml` (self-hosted browser engine)
- **BREAKING** `fetch_page()` in `jina_utils.py` rewritten to call crawl4ai REST API instead of Jina
- **BREAKING** `JINA_API_KEY` environment variable removed (no longer needed)
- **New** Configurable crawl4ai URL setting in Settings UI (`res.config.settings`)
- **New** `crawl4ai_utils.py` renamed from `jina_utils.py` with updated import
- Tests updated to mock crawl4ai response format

## Capabilities

### New Capabilities
- `crawl4ai-fetching`: Self-hosted page fetching via crawl4ai REST API with configurable URL

### Modified Capabilities
- `jina-fetching` (existing at `openspec/specs/jina-fetching/spec.md`): Replaced entirely by crawl4ai-fetching; spec updated to reflect crawl4ai as the fetch mechanism

## Impact

- `docker-compose.yml` — new `crawl4ai` service
- `newsassistant_website/models/jina_utils.py` — rewritten to `crawl4ai_utils.py`
- `newsassistant_website/models/news_source_website.py` — import path update
- `newsassistant_website/__manifest__.py` — no dependency change
- `newsassistant_website/models/__init__.py` — update import
- `newsassistant_website/models/res_config_settings.py` — **new file** for crawl4ai URL setting
- `newsassistant_website/views/res_config_settings_views.xml` — **new file** for settings UI
- `newsassistant_website/tests/test_jina_utils.py` — rewritten to `test_crawl4ai_utils.py`
- `newsassistant_website/tests/test_website_scraping.py` — update mock patches
- `.env.example`, `README.md`, `agents.md` — remove JINA_API_KEY references
- `openspec/specs/jina-fetching/spec.md` — replaced by `openspec/specs/crawl4ai-fetching/spec.md`
