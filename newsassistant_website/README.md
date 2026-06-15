# News Assistant — Website

Website scraping extension for News Assistant.

## Overview

This addon adds website scraping to the News Assistant pipeline. It fetches listing pages daily,
uses AI to discover article URLs, then fetches each article page and stores the raw content as a
`news.snapshot` for extraction. It handles JavaScript-rendered pages, bot protection (Cloudflare),
PDFs, and validates header images automatically.

Requires `newsassistant` (base module).

## Features

- AI-powered article URL discovery from listing pages
- crawl4ai integration for JavaScript-rendered pages (bypasses Cloudflare and similar bot protection)
- PDF support: text extracted via `pdfminer`, then sent to AI
- Header image selection with validation: landscape orientation (min 800×400 px), JPEG/PNG/WebP only
- Deduplication by normalized URL — known articles are never re-fetched
- Daily cron job for all active website sources
- Manual "Scrape Now" button on the source form view

## Pipeline

```
ir.cron (daily)
    └─▶ news.source._cron_scrape_all()
            └─▶ [per active website source]
                    └─▶ source.with_delay()._scrape_listing()        [Stage 1]
                            └─▶ [per new article URL]
                                    └─▶ source.with_delay()._fetch_and_create_snapshot()  [Stage 2]
                                            └─▶ snapshot.with_delay()._extract_articles_website()
```

**Stage 1 — Listing discovery**: Fetches the source listing page via crawl4ai, pre-cleans the
HTML (strips nav/footer/script/style, removes attributes except `href` and `src`), and asks the AI
to return a JSON array of `{title, url}` objects. Known URLs are filtered out before Stage 2 jobs
are queued.

**Stage 2 — Snapshot creation**: Fetches each article page via crawl4ai. The raw content is stored
as a `news.snapshot`. A queue job on the base module then extracts the structured article
(`news.article`) from the snapshot.

## Configuration

### Environment variables

| Variable | Required | Description |
|---|---|---|
| `INFOMANIAK_AI_API_KEY` | Yes | Infomaniak AI key for URL discovery and extraction |

### crawl4ai server

crawl4ai runs as a separate Docker container. It is configured via **Settings → News Assistant**
under the "Scraping" section. The default URL is `http://crawl4ai:11235`.

### Adding website sources

1. Go to **News Assistant → Sources**.
2. Click **New**.
3. Set **Type** to `Website`.
4. Enter the **Name** and the **URL** of the listing/news page.
5. Leave **Active** enabled to include it in the daily scrape.

### Scraping schedule

The daily cron job is registered at installation. Adjust timing at
**Settings → Technical → Automation → Scheduled Actions** →
"News Assistant: Scrape All Website Sources".

## Usage

### Trigger a scrape manually

Open a source record and click **Scrape Now**. A queue job is enqueued immediately.
Monitor progress at **Settings → Technical → Queue → Jobs**.

### Monitor sources

**News Assistant → Sources** shows:

- Last scrape date per source
- Error state (`ok` / `error`) with error detail
- Snapshot and article counts

### Check for errors

If a source shows `error` state, open the source record and read the **Error Message** field.
For more detail, click the **Logs** smart button to see the full LLM request/response trace.

## Error Handling

| Condition | Behaviour |
|---|---|
| crawl4ai server unreachable | `RetryableJobError` — retried up to 3 times with escalating delay |
| Non-200 response from crawl4ai | `RetryableJobError` — retried up to 3 times with escalating delay |
| crawl4ai returns `success: false` | Error logged on source; no retry |
| HTTP 404 | Logged on source; no retry |
| PDF extraction failure | Error logged on snapshot; article marked as `error` |
| Header image fails validation | Image discarded silently; article saved without header image |
| AI returns no URLs | Empty result logged; no snapshots created for this run |
| Malformed AI JSON | Robust parser retries with relaxed parsing before failing |

## Security

| Group | Access |
|---|---|
| `newsassistant.newsassistant_group_user` | Trigger manual scrapes, view sources and articles |
| `newsassistant.newsassistant_group_admin` | Full access |

No additional models or access rules beyond the base module.

## Dependencies

- `newsassistant` — base module (required)
- `queue_job` — OCA background job processing
- `INFOMANIAK_AI_API_KEY` — environment variable (required)
- crawl4ai — self-hosted Docker container (required)

## Testing

```bash
make test-module MODULE=newsassistant_website
```

## License

LGPL-3
