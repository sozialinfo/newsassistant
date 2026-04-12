# News Assistant

Automated news scraping and triage for Swiss social-sector sources.

## Overview

News Assistant monitors ~60 Swiss social-sector websites (NGOs, government bodies, research
institutions) for new articles. It scrapes listing pages daily, follows links to individual
articles, and uses AI (Infomaniak AI Services) to extract clean, structured content — stripping
away navigation, footers, ads, and other boilerplate.

Extracted articles are presented in a kanban board where users can triage them through stages:
**New** → **Relevant** → **Archived** / **Discarded**.

## Architecture

```
ir.cron (daily)
    └─▶ _cron_scrape_all()
            ├─▶ source_1.with_delay()._scrape_listing()     [Stage 1: discover URLs]
            │       ├─▶ article_A.with_delay()._fetch_and_extract()  [Stage 2: extract]
            │       └─▶ article_B.with_delay()._fetch_and_extract()
            ├─▶ source_2.with_delay()._scrape_listing()
            │       └─▶ article_C.with_delay()._fetch_and_extract()
            └─▶ ...
```

### Two-Stage Pipeline

1. **Stage 1 — Listing Discovery**: Fetches the listing page, pre-cleans the HTML
   (strips nav, footer, script, style tags and all attributes), sends it to the AI which
   returns a JSON array of `{title, url}` objects.

2. **Stage 2 — Article Extraction**: For each new (non-duplicate) URL, fetches the article
   page and extracts text based on the content type:
   - **HTML pages**: Pre-cleans the HTML (strips boilerplate, preserves links), sends to AI.
   - **PDF documents**: Extracts text using `pdfminer`, sends to AI.
   - **403 / bot-protected pages**: Falls back to the [Jina Reader API](https://r.jina.ai/)
     which renders pages via a headless browser, bypassing Cloudflare and similar protections.

   The AI returns `{title, date, summary, content}` as clean plain text in the original language.

### Background Processing

Uses OCA `queue_job` for background processing. Each source scrape and each article extraction
runs as an independent queue job. A dedicated channel `root.newsassistant` controls concurrency
(default: 4 parallel jobs) to avoid hammering external websites.

### Deduplication

Articles are deduplicated by URL. Known URLs are never re-fetched. URLs are normalized
(trailing slashes and fragments stripped) before comparison.

## Prerequisites

- Odoo 18.0
- OCA `queue_job` module
- Infomaniak AI Services account with API key
- Jina Reader API key (optional, for bot-protected sites)

## Installation

### 1. Mount OCA Queue Addons

In `docker-compose.yml`, add a volume for the queue addons:

```yaml
volumes:
  - /path/to/oca/queue:/mnt/oca/queue:ro
```

### 2. Configure odoo.conf

```ini
[options]
addons_path = /mnt/extra-addons,/mnt/oca/web,/mnt/oca/queue
server_wide_modules = web,queue_job
workers = 2

[queue_job]
channels = root:4,root.newsassistant:4
```

Key settings:
- `addons_path`: Must include the OCA queue addons path
- `server_wide_modules`: Must include `queue_job` for the built-in job runner
- `workers`: Must be >= 2 for the job runner to work in prefork mode
- `channels`: Controls concurrency; `root.newsassistant:4` means max 4 concurrent scrape jobs

### 3. Set the API Keys

Create a `.env` file at the project root:

```
INFOMANIAK_AI_API_KEY=your-infomaniak-api-key-here
JINA_API_KEY=your-jina-api-key-here
```

- **Infomaniak AI API Key** (required): Used for AI-powered content extraction via the
  Infomaniak AI Services (OpenAI-compatible API, model `qwen3`).
- **Jina Reader API Key** (optional but recommended): Used as a fallback when direct HTTP
  fetching is blocked (e.g. Cloudflare bot protection returning 403). The
  [Jina Reader API](https://r.jina.ai/) renders pages via a headless browser and returns
  clean text, bypassing most bot protection.

Pass both to the container in `docker-compose.yml`:

```yaml
environment:
  - INFOMANIAK_AI_API_KEY=${INFOMANIAK_AI_API_KEY}
  - JINA_API_KEY=${JINA_API_KEY}
```

### 4. Install the Module

1. Restart the Odoo container to pick up config changes
2. Install `queue_job` first (if not already installed)
3. Install `newsassistant` (enable demo data for sample sources)

## Configuration

### Infomaniak AI Product ID

The default product ID (`103794`) is stored as a system parameter
(`newsassistant.infomaniak_product_id`). Change it in Settings → Technical → Parameters
→ System Parameters if needed.

### Adding News Sources

Go to **News Assistant → Sources** and create records with:
- **Name**: Display name for the source
- **URL**: The listing/news page URL to scrape
- **Active**: Toggle to include/exclude from daily scraping

### Scraping Schedule

The daily cron job is configured at installation. To adjust timing, go to
Settings → Technical → Automation → Scheduled Actions and find
"News Assistant: Scrape All Sources".

## Usage

### Triage Articles

1. Go to **News Assistant → Articles**
2. Articles appear in the kanban board under the **New** column
3. Read the summary on each card; click to see full content
4. Drag articles to **Relevant**, **Archived**, or **Discarded**

### Monitor Sources

Go to **News Assistant → Sources** to see:
- Last scrape date for each source
- Error status (OK / Error) with error details
- Article count per source

## Technical Details

### Models

| Model | Description |
|-------|-------------|
| `news.source` | News website to scrape |
| `news.article` | Extracted article with clean content |
| `news.article.stage` | Kanban stage (New, Relevant, Archived, Discarded) |

### AI Model

Uses `qwen3` via the Infomaniak AI Services OpenAI-compatible API. Two prompts:
- Stage 1: Extract article links from listing page HTML
- Stage 2: Extract article content from individual article HTML

### Error Handling

- Transient HTTP errors (timeout, 5xx) → `RetryableJobError` with escalating retry pattern
- HTTP 403 (bot protection) → automatic fallback to Jina Reader API
- Permanent HTTP errors (404) → logged on source, no retry
- AI API errors (rate limit) → `RetryableJobError`
- Malformed AI responses → robust parser handles JSONL, markdown fences, thinking blocks
- PDF documents → text extracted via `pdfminer`, then processed normally

### Running Tests

```bash
docker exec odoo-newsassistant odoo --test-tags newsassistant --stop-after-init -d newsassistant
```
