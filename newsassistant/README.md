# News Assistant

Automated news capture and triage — base module.

## Overview

News Assistant monitors news sources, captures raw content into snapshots, uses AI to extract
clean structured articles, and presents them in a kanban board for human triage. This base module
provides the shared data model, security groups, kanban UI, and logging infrastructure that all
other News Assistant addons build on.

It does **not** scrape websites or receive emails by itself — install `newsassistant_website`
and/or `newsassistant_email` to add those capabilities.

## Features

- Shared data model: `news.source` → `news.snapshot` → `news.article`
- Kanban board with configurable stages (New, Shortlist, Published, Discarded)
- Unified operation log with per-step LLM request/response audit trail
- Security groups: `newsassistant_group_user` and `newsassistant_group_admin`
- Configurable Infomaniak AI product ID
- Language detection: articles are tagged with their content language (auto-detected by AI)

## Architecture

The data flow is a three-layer pipeline. Extension addons plug in at Stages 1 and 2; the base
module owns Stage 3 (article extraction from a snapshot) and the kanban UI.

```
news.source  (website or email)
    │
    │  Stage 1 — newsassistant_website or newsassistant_email
    ▼
news.snapshot  (raw HTML or email content, one per page / email)
    │
    │  Stage 2 — base module (queue job: _extract_from_snapshot)
    ▼
news.article  (title, date, summary, content — clean structured text)
    │
    │  Stage 3 — newsassistant_blog (optional: triage + publish)
    ▼
blog.post  (published to Odoo website blog)
```

### Background Processing

Uses OCA `queue_job`. A dedicated channel `root.newsassistant` controls concurrency (capacity 2
by default). Each snapshot extraction runs as an independent queue job so failures are isolated.

### Deduplication

Articles are deduplicated by URL. A snapshot is not created if its URL already exists in the
database. URLs are normalised (trailing slashes and fragments stripped) before comparison.

## Configuration

### Infomaniak AI Product ID

The AI product ID (`103794` by default) is stored as a system parameter. Change it at
**Settings → Technical → Parameters → System Parameters**, key
`newsassistant.infomaniak_product_id`.

### Kanban Stages

Default stages are created on installation: **New**, **Shortlist**, **Published**, **Discarded**.
Add or rename stages at **News Assistant → Configuration → Stages**.

### Scraping Schedule

Extension addons register their own cron jobs. To adjust timing, go to
**Settings → Technical → Automation → Scheduled Actions**.

## Usage

### Triage articles

1. Go to **News Assistant → Articles**.
2. Articles appear in the kanban board under the **New** column.
3. Click a card to read the summary and full extracted content.
4. Drag articles to **Shortlist**, **Published**, or **Discarded** as appropriate.

### Monitor sources

Go to **News Assistant → Sources** to see:

- Source type (website or email) and last scrape date
- Error status with detailed error message
- Article and snapshot counts per source

### View logs

Go to **News Assistant → Logs** to see a record of every operation, including:

- Duration and outcome (success / error)
- LLM request and response content for each step
- Linked source, snapshot, and article records

## AI Model

All AI calls use `qwen3` via the Infomaniak AI Services OpenAI-compatible API (Swiss-hosted,
GDPR/FADP compliant). Prompts begin with `/no_think` to suppress Qwen3's thinking mode.

- **Temperature 0.1** — extraction and classification tasks
- **Temperature 0.7** — creative tasks (teaser generation in `newsassistant_blog`)

## Error Handling

| Condition | Behaviour |
|---|---|
| Transient HTTP errors (408, 429, 5xx) | `RetryableJobError` with escalating retry (5 min → 15 min → 1 hr) |
| HTTP 403 (bot protection) | Automatic fallback to Jina Reader API |
| HTTP 404 | Logged on source; no retry |
| AI rate limit | `RetryableJobError` |
| Malformed AI response | Robust JSON parser handles JSONL, markdown fences, thinking blocks |
| PDF document | Text extracted via `pdfminer`, then sent to AI as plain text |

## Security

| Group | Description |
|---|---|
| `newsassistant_group_user` | View articles and sources, move kanban cards, trigger actions |
| `newsassistant_group_admin` | Full access including create/edit/delete sources and stages |

## Dependencies

- `base` — Odoo core
- `queue_job` — OCA background job processing (v18.0.3.0.0+)
- `INFOMANIAK_AI_API_KEY` — environment variable (required)

## Testing

```bash
docker exec odoo-newsassistant odoo --test-tags newsassistant --stop-after-init -d newsassistant
```

## License

LGPL-3
