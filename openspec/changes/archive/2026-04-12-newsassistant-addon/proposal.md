## Why

The organization monitors ~60 Swiss social-sector news sources (NGOs, government bodies, research institutions) for relevant developments. Currently there is no automated way to collect, clean, and triage these articles. Staff must manually visit each site, sift through navigation chrome and boilerplate, and decide what matters. This addon automates discovery and presents only clean article content in a kanban board for human triage.

## What Changes

- New Odoo 18 addon `newsassistant` in `addons/newsassistant/`
- **News source management**: CRUD for web sources to scrape, seeded from `news_source.csv` via demo data
- **Two-stage scraping pipeline**: Stage 1 discovers article URLs from listing pages; Stage 2 follows each link and extracts clean content using Infomaniak AI (LLM)
- **AI-powered content extraction**: Raw HTML is pre-cleaned (strip nav, footer, scripts) then sent to Infomaniak's OpenAI-compatible API (`qwen3` model) to extract structured article data (title, date, summary, full clean text) in the original language
- **Deduplication**: Articles are deduplicated by URL — known URLs are never re-fetched
- **Kanban triage workflow**: Articles appear in a kanban board with stages (New → Relevant → Archived / Discarded) for manual sorting
- **Background processing via OCA queue_job**: The daily cron fans out into one queue job per source, each of which fans out into one job per new article. Channel-based concurrency control prevents hammering external sites
- **README.md and agents.md**: Addon includes a README documenting purpose, setup, and configuration, and an `agents.md` with definition of done
- **Unit tests**: Full test suite covering models, scraping logic, AI integration (mocked), deduplication, and kanban workflow

## Capabilities

### New Capabilities
- `source-management`: CRUD for news sources with URL, name, active flag, scrape state tracking, and error reporting
- `scraping-pipeline`: Two-stage scraping (listing discovery + article extraction) with HTML pre-cleaning, AI-powered content extraction via Infomaniak API, and URL-based deduplication
- `kanban-triage`: Kanban board with configurable stages for triaging discovered articles; articles display title, source, date, and clean summary
- `queue-job-integration`: OCA queue_job integration for background processing with channel-based concurrency control and retry/error handling
- `addon-documentation`: README.md with setup/config instructions and agents.md with definition of done

### Modified Capabilities
(none — this is a greenfield addon)

## Impact

- **New addon**: `addons/newsassistant/` with models, views, data, demo data, tests
- **Dependencies**: Requires `queue_job` OCA module (already available at `/home/debian/shared/odoo-src/18.0/oca/queue/`)
- **Server config**: `queue_job` must be added to `server_wide_modules` in `odoo.conf`; OCA queue path must be added to `addons_path`
- **Docker config**: `docker-compose.yml` needs volume mount for OCA queue addons and environment variable for Infomaniak API key
- **Environment**: `.env` file at project root stores `INFOMANIAK_AI_API_KEY`; passed to container via docker-compose
- **External services**: Infomaniak AI API (product ID 103794, model `qwen3`), ~60 external websites scraped daily
