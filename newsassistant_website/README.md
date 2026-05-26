# News Assistant — Website

Website scraping extension for News Assistant. Fetches articles from news websites using the Jina Reader API.

## Features

- Jina Reader API integration for JavaScript-rendered pages (bypasses bot protection)
- AI-powered article URL discovery from listing pages
- Per-article snapshot creation with Markdown→HTML conversion
- Header image selection: landscape validation (min 800×400), format check (JPEG/PNG/WebP)
- Deduplication by normalized URL
- Daily cron job for all active website sources
- Manual scrape trigger from the source form view

## Models

### news.source (extended)

| Method | Description |
|--------|-------------|
| `action_scrape_now()` | Manual trigger: queue a scrape job for this source |
| `_cron_scrape_all()` | Cron entry point: queue all active website sources |
| `_scrape_listing()` | Queue job: fetch listing page and discover article URLs |
| `_fetch_and_create_snapshot()` | Queue job: fetch article page and create snapshot |

### news.snapshot (extended)

| Method | Description |
|--------|-------------|
| `_extract_articles_website()` | Website-specific extraction with URL and image handling |

## Security

| Group | Access |
|-------|--------|
| `newsassistant.newsassistant_group_user` | Trigger manual scrapes, view sources |
| `newsassistant.newsassistant_group_admin` | Full access |

No additional models or access rules beyond base module.

## Configuration

The following environment variables must be set:

| Variable | Description |
|----------|-------------|
| `JINA_API_KEY` | Jina Reader API key (required for website scraping) |
| `INFOMANIAK_AI_API_KEY` | Infomaniak AI API key (required for URL discovery) |

Add website sources in **News Assistant → Sources** with `Type = Website`.

## Dependencies

- `newsassistant` — base module
- `queue_job` — OCA background job processing
- `JINA_API_KEY` — environment variable (required)

## License

LGPL-3
