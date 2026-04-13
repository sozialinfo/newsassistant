# News Assistant — Agent Guidelines

## Project Overview

News Assistant is an Odoo 18 addon that automatically scrapes ~60 Swiss social-sector websites (NGOs, government bodies, research institutions), extracts clean article content using AI, and presents articles in a kanban board for manual triage.

**Key insight**: The AI (Infomaniak AI Services) acts as a universal HTML-to-structured-data parser, eliminating the need for per-source CSS selector configurations. This makes the system resilient to website redesigns.

## Application Access

| Item | Value |
|------|-------|
| URL | https://newsassistant.opencode.bruehlmeier.com |
| Username | `admin` |
| Password | `admin` |
| Database | `newsassistant` |

### Key UI Locations

- **Articles Kanban**: News Assistant → Articles (triage view)
- **Sources List**: News Assistant → Sources (manage scraped websites)
- **Queue Jobs**: Settings → Technical → Queue → Jobs (monitor background jobs)
- **Scheduled Actions**: Settings → Technical → Automation → Scheduled Actions

## Architecture

```
ir.cron (daily at 6:00 AM)
    └─▶ _cron_scrape_all()
            ├─▶ source_1.with_delay()._scrape_listing()     [Stage 1: discover URLs]
            │       ├─▶ article_A.with_delay()._fetch_and_extract()  [Stage 2: extract]
            │       └─▶ article_B.with_delay()._fetch_and_extract()
            ├─▶ source_2.with_delay()._scrape_listing()
            │       └─▶ article_C.with_delay()._fetch_and_extract()
            └─▶ ...
```

### Two-Stage Pipeline

| Stage | Method | Input | Output |
|-------|--------|-------|--------|
| **Stage 1** | `news.source._scrape_listing()` | Listing page URL | JSON array of `{title, url}` |
| **Stage 2** | `news.article._fetch_and_extract()` | Article URL | JSON object `{title, date, summary, content}` |

### Content Processing Flow

1. **Fetch** → HTTP GET with 30s timeout
2. **Pre-clean** → BeautifulSoup strips nav/footer/script/style tags + removes attributes
3. **AI Extract** → Send cleaned HTML to Infomaniak AI, parse JSON response
4. **Store** → Write to Odoo database

### Fallback Mechanisms

- **HTTP 403 (bot protection)** → Automatic fallback to Jina Reader API
- **PDF documents** → Text extracted via `pdfminer`, then sent to AI
- **Transient errors** → `RetryableJobError` with escalating retry (5min → 15min → 1hr)

## Codebase Map

```
newsassistant/
├── agents.md                 # THIS FILE - project-level guidance
├── docker-compose.yml        # Container setup (Odoo 18 + volumes)
├── odoo.conf                 # Odoo config (queue_job channels, workers)
├── .env                      # API keys (INFOMANIAK_AI_API_KEY, JINA_API_KEY)
├── news_source.csv           # Source URLs for import
└── addons/newsassistant/     # THE ADDON
    ├── __manifest__.py       # Dependencies: base, queue_job
    ├── README.md             # User-facing documentation
    ├── agents.md             # Addon-level coding standards & DoD
    ├── models/
    │   ├── news_source.py    # Source model + AI service + HTML cleaner + Stage 1
    │   ├── news_article.py   # Article model + Stage 2 extraction + Jina fallback
    │   └── news_article_stage.py  # Kanban stages (New, Relevant, Archived, Discarded)
    ├── views/
    │   ├── news_source_views.xml   # Source list/form views
    │   ├── news_article_views.xml  # Article kanban/form views
    │   └── menu.xml                # Menu structure
    ├── data/
    │   ├── news_article_stage_data.xml   # Default kanban stages
    │   ├── queue_job_data.xml            # Queue channel config
    │   ├── ir_cron_data.xml              # Daily scrape cron
    │   └── ir_config_parameter_data.xml  # Default product ID
    ├── demo/
    │   └── news_source_demo.xml    # Sample sources for testing
    ├── security/
    │   └── ir.model.access.csv     # Access rights
    └── tests/
        ├── test_news_source.py       # Source model tests
        ├── test_html_cleaner.py      # HTML pre-cleaning tests
        ├── test_url_normalization.py # URL dedup logic tests
        ├── test_scraping_pipeline.py # End-to-end pipeline tests (mocked)
        ├── test_queue_jobs.py        # Job creation tests with trap_jobs()
        └── test_kanban.py            # Stage workflow tests
```

## Key Technologies

### Infomaniak AI Services

Swiss-hosted, OpenAI-compatible AI API. Data stays in Switzerland (GDPR/FADP compliant).

| Item | Value |
|------|-------|
| Endpoint | `https://api.infomaniak.com/2/ai/{product_id}/openai/v1/chat/completions` |
| Default Product ID | `103794` (stored in `ir.config_parameter`) |
| Model | `qwen3` (Qwen3-VL-235B, 262K context window) |
| Auth | Bearer token via `INFOMANIAK_AI_API_KEY` env var |
| Timeout | 120 seconds |

**Request format** (OpenAI-compatible):
```python
payload = {
    "model": "qwen3",
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": cleaned_html},
    ],
    "temperature": 0.1,
}
```

**Important**: Prompts start with `/no_think` to disable qwen3's thinking mode (prevents `<think>...</think>` blocks in output).

### Jina Reader API

Headless browser service that bypasses bot protection (Cloudflare, etc.) and returns clean content.

| Item | Value |
|------|-------|
| Endpoint | `https://r.jina.ai/{target_url}` |
| Auth | Bearer token via `JINA_API_KEY` env var |
| Timeout | 60 seconds (longer due to browser rendering) |
| Output | Plain text (with `Accept: text/plain` header) |

**When used**: Automatic fallback when direct HTTP fetch returns 403.

### OCA queue_job

Background job processing with concurrency control.

| Item | Value |
|------|-------|
| Version | `18.0.3.0.0` |
| Config location | `[queue_job]` section in `odoo.conf` |
| Channel | `root.newsassistant` (capacity: 4 concurrent jobs) |
| Runner | Built-in (requires `workers >= 2`) |

**Configuration in odoo.conf**:
```ini
[options]
server_wide_modules = web,queue_job
workers = 2

[queue_job]
channels = root:4,root.newsassistant:4
```

**Creating jobs**:
```python
record.with_delay(
    channel="root.newsassistant",
    description="Human-readable job name",
)._method_name()
```

## Environment Variables

Required in `.env` file (loaded via docker-compose):

| Variable | Required | Purpose |
|----------|----------|---------|
| `INFOMANIAK_AI_API_KEY` | Yes | AI extraction API key |
| `JINA_API_KEY` | No | Fallback for bot-protected sites |
| `POSTGRES_PASSWORD` | Yes | Database connection |

**Verify they're set**:
```bash
docker exec odoo-newsassistant env | grep -E "(INFOMANIAK|JINA)"
```

## Development Workflow

### Running Tests

```bash
# Run all newsassistant tests
docker exec odoo-newsassistant odoo --test-tags newsassistant --stop-after-init -d newsassistant

# Run specific test class
docker exec odoo-newsassistant odoo --test-tags newsassistant.test_scraping_pipeline --stop-after-init -d newsassistant
```

### Restarting After Code Changes

```bash
cd /home/debian/projects/newsassistant
docker compose restart odoo-newsassistant
```

### Viewing Logs

```bash
docker logs -f odoo-newsassistant
```

### Manually Trigger Scraping

From Odoo UI: News Assistant → Sources → select source → "Scrape Now" button

Or via shell:
```python
# In Odoo shell
source = env['news.source'].browse(1)
source._scrape_listing()  # Runs synchronously (no queue)
```

### Testing Queue Jobs with trap_jobs()

```python
from odoo.addons.queue_job.tests.common import trap_jobs

def test_cron_creates_jobs(self):
    with trap_jobs() as trap:
        self.env["news.source"]._cron_scrape_all()
        trap.assert_jobs_count(expected_count)
        for job in trap.enqueued_jobs:
            self.assertEqual(job.method_name, "_scrape_listing")
```

### Mocking HTTP and AI Calls

```python
from unittest.mock import MagicMock, patch

def _make_mock_response(status_code=200, text="", json_data=None):
    response = MagicMock()
    response.status_code = status_code
    response.text = text
    response.content = text.encode("utf-8")
    response.headers = {"content-type": "text/html"}
    if json_data:
        response.json.return_value = json_data
    return response

# Mock HTTP GET
@patch("odoo.addons.newsassistant.models.news_source.requests.get")
def test_something(self, mock_get):
    mock_get.return_value = _make_mock_response(200, "<html>...</html>")

# Mock AI API (POST)
@patch("odoo.addons.newsassistant.models.news_source.requests.post")
def test_ai(self, mock_post):
    mock_post.return_value = _make_mock_response(
        200,
        json_data={"choices": [{"message": {"content": '{"title": "Test"}'}}]}
    )
```

## Troubleshooting

### Jobs stuck in "enqueued" state

**Cause**: Job runner not starting (workers < 2 or queue_job not in server_wide_modules)

**Fix**: Check `odoo.conf`:
```ini
server_wide_modules = web,queue_job
workers = 2
```

Then restart: `docker compose restart odoo-newsassistant`

### "Infomaniak AI API key not configured" error

**Cause**: Environment variable not passed to container

**Fix**: Verify `.env` file exists and docker-compose.yml has:
```yaml
environment:
  - INFOMANIAK_AI_API_KEY=${INFOMANIAK_AI_API_KEY}
```

### Source shows "Error" state after scraping

**Check**: Source record's `error_message` field for details.

**Common causes**:
- HTTP 404: Source URL changed
- AI parse error: Website structure changed dramatically
- Timeout: Website slow or blocking

### Articles not appearing after scrape

**Check**:
1. Source `last_scrape_date` updated? If not, Stage 1 failed.
2. Queue Jobs view: Are Stage 2 jobs pending/failed?
3. Article records exist but have error in `content` field?

### Tests fail with "queue_job not found"

**Cause**: Test running without OCA queue addons in path

**Fix**: Ensure `addons_path` in `odoo.conf` includes `/mnt/oca/queue`

## Data Models

| Model | Key Fields | Purpose |
|-------|------------|---------|
| `news.source` | `name`, `url`, `active`, `state`, `error_message`, `last_scrape_date` | Website to scrape |
| `news.article` | `title`, `url` (unique, indexed), `source_id`, `date`, `summary`, `content`, `stage_id` | Extracted article |
| `news.article.stage` | `name`, `sequence`, `fold` | Kanban column (New, Relevant, Archived, Discarded) |

## Definition of Done

Before marking work complete, verify:

- [ ] Code follows Odoo 18 conventions (see `addons/newsassistant/agents.md`)
- [ ] All external calls mocked in tests — no real HTTP/AI requests
- [ ] Tests pass: `odoo --test-tags newsassistant --stop-after-init`
- [ ] Queue jobs use `channel="root.newsassistant"` and have `description`
- [ ] Transient errors raise `RetryableJobError`, permanent errors are logged
- [ ] README.md updated if user-facing behavior changed

## Quick Reference

| Task | Command/Location |
|------|-----------------|
| Run tests | `docker exec odoo-newsassistant odoo --test-tags newsassistant --stop-after-init -d newsassistant` |
| View logs | `docker logs -f odoo-newsassistant` |
| Restart | `docker compose restart odoo-newsassistant` |
| Source model | `addons/newsassistant/models/news_source.py` |
| Article model | `addons/newsassistant/models/news_article.py` |
| AI call | `news.source._call_infomaniak_ai(system_prompt, content)` |
| Jina fallback | `news.article._fetch_via_jina()` |
| HTML cleaner | `news_source.clean_html(raw_html)` |
| URL normalizer | `news_source.normalize_url(url)` |
| JSON parser | `news_source.parse_ai_json(text, expect_array=True)` |

## Translations (i18n)

The module supports German (de) and French (fr) translations. Translation files are in `addons/newsassistant/i18n/`.

### Terminology

| English | German | French |
|---------|--------|--------|
| Article | Artikel | Article |
| Stage | Status | Étape |
| Source | Quelle | Source |
| Relevant | Relevant | Pertinent |
| Discarded | Verworfen | Rejeté |
| Scraped | Abgerufen | Collecté |
| Pending | Ausstehend | En attente |
| Skipped | Übersprungen | Ignoré |

### Installing Languages (First Time Setup)

Before translations can be used, the target languages must be installed in Odoo:

```bash
# Stop Odoo first
cd /home/debian/projects/newsassistant
docker compose stop odoo-newsassistant

# Load German and French languages
docker run --rm --network opencode \
  -v $(pwd)/addons:/mnt/extra-addons \
  -v $(pwd)/odoo.conf:/etc/odoo/odoo.conf:ro \
  -v /home/debian/shared/odoo-src/18.0/oca/web:/mnt/oca/web:ro \
  -v /home/debian/shared/odoo-src/18.0/oca/queue:/mnt/oca/queue:ro \
  -e HOST=postgres -e PORT=5432 -e USER=opencode -e PASSWORD= \
  odoo:18.0 odoo --load-language=de_DE,fr_FR -d newsassistant --stop-after-init

# Update module to load translations from .po files
docker run --rm --network opencode \
  -v $(pwd)/addons:/mnt/extra-addons \
  -v $(pwd)/odoo.conf:/etc/odoo/odoo.conf:ro \
  -v /home/debian/shared/odoo-src/18.0/oca/web:/mnt/oca/web:ro \
  -v /home/debian/shared/odoo-src/18.0/oca/queue:/mnt/oca/queue:ro \
  -e HOST=postgres -e PORT=5432 -e USER=opencode -e PASSWORD= \
  odoo:18.0 odoo -u newsassistant -d newsassistant --stop-after-init

# Start Odoo again
docker compose start odoo-newsassistant
```

### Updating Translations After Code Changes

When translatable strings change (new fields, labels, views, Python `_()` strings):

**1. Stop Odoo and update module:**
```bash
cd /home/debian/projects/newsassistant
docker compose stop odoo-newsassistant

docker run --rm --network opencode \
  -v $(pwd)/addons:/mnt/extra-addons \
  -v $(pwd)/odoo.conf:/etc/odoo/odoo.conf:ro \
  -v /home/debian/shared/odoo-src/18.0/oca/web:/mnt/oca/web:ro \
  -v /home/debian/shared/odoo-src/18.0/oca/queue:/mnt/oca/queue:ro \
  -e HOST=postgres -e PORT=5432 -e USER=opencode -e PASSWORD= \
  odoo:18.0 odoo -u newsassistant -d newsassistant --stop-after-init

docker compose start odoo-newsassistant
```

**2. Export fresh POT template:**
```bash
docker exec odoo-newsassistant odoo \
  --i18n-export=/tmp/newsassistant.pot \
  --modules=newsassistant \
  -d newsassistant \
  --stop-after-init

docker cp odoo-newsassistant:/tmp/newsassistant.pot /tmp/
```

**3. Update .po files with new strings:**

Compare the new POT with existing .po files. Add any new `msgid` entries and translate them.

**Important for Python `_()` strings (Odoo 18+):**

Python code translations require the `#. odoo-python` comment marker:
```po
#. module: newsassistant
#. odoo-python
#: code:addons/newsassistant/models/news_article.py:0
msgid "Re-fetch Started"
msgstr "Abruf gestartet"
```

The POT export includes this marker automatically. When manually adding translations, ensure the `#. odoo-python` line is present - without it, code translations won't load.

Python strings must use `_()` to be translatable:
```python
from odoo import _
# ...
"title": _("Re-fetch Started"),
"message": _("Re-fetching article in background..."),
```

**4. Reload translations:**
```bash
cd /home/debian/projects/newsassistant
docker compose stop odoo-newsassistant

docker run --rm --network opencode \
  -v $(pwd)/addons:/mnt/extra-addons \
  -v $(pwd)/odoo.conf:/etc/odoo/odoo.conf:ro \
  -v /home/debian/shared/odoo-src/18.0/oca/web:/mnt/oca/web:ro \
  -v /home/debian/shared/odoo-src/18.0/oca/queue:/mnt/oca/queue:ro \
  -e HOST=postgres -e PORT=5432 -e USER=opencode -e PASSWORD= \
  odoo:18.0 odoo -u newsassistant -d newsassistant --stop-after-init

docker compose start odoo-newsassistant
```

**5. Verify in Odoo:**

Switch user language to German/French in Preferences and verify all labels display correctly.

**Note:** The POT file is gitignored (generated on demand). Only the translated .po files are committed.
