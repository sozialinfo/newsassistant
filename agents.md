# News Assistant — Agent Guidelines

## Project Overview

News Assistant is an Odoo 18 addon system that automatically scrapes news sources, extracts clean article content using AI, and presents articles in a kanban board for manual triage. The **Newsassistant Blog** extension addon adds AI-powered relevance triage and automatic blog publishing.

**Key insight**: The AI (Infomaniak AI Services) acts as a universal HTML-to-structured-data parser, eliminating the need for per-source CSS selector configurations. This makes the system resilient to website redesigns.

## Application Access

| Item | Value |
|------|-------|
| URL | http://localhost:8069 |
| Username | `admin` |
| Password | `admin` |
| Database | `newsassistant` |

### Key UI Locations

- **Articles Kanban**: News Assistant → Articles (triage view)
- **Sources List**: News Assistant → Sources (manage scraped websites)
- **Queue Jobs**: Settings → Technical → Queue → Jobs (monitor background jobs)
- **Scheduled Actions**: Settings → Technical → Automation → Scheduled Actions
- **Blog Settings**: Settings → News Assistant → Blog Settings (content strategy, teaser prompt, target blog, Pixabay key)
- **Blog Posts**: Website → Blog (published articles)

## Architecture

### Full Pipeline (Scrape → Triage → Publish)

```
ir.cron (daily — scrape)
    └─▶ news.source._cron_scrape_all()
            ├─▶ source_1.with_delay()._scrape_listing()     [Stage 1: discover URLs]
            │       ├─▶ article_A.with_delay()._fetch_and_extract()  [Stage 2: extract]
            │       └─▶ article_B.with_delay()._fetch_and_extract()
            └─▶ ...

ir.cron (daily — digest)
    └─▶ news.article._cron_digest_all_impl()
            ├─▶ article_A.with_delay()._digest_article()    [Stage 3: triage + publish]
            └─▶ article_B.with_delay()._digest_article()
```

### Three-Stage Pipeline

| Stage | Addon | Method | Input | Output |
|-------|-------|--------|-------|--------|
| **Stage 1** | newsassistant | `news.source._scrape_listing()` | Listing page URL | JSON array of `{title, url}` |
| **Stage 2** | newsassistant | `news.article._fetch_and_extract()` | Article URL | JSON object `{title, date, summary, content}` |
| **Stage 3** | newsassistant_blog | `news.article._digest_article()` | Scraped article | Relevance decision + optional blog post |

### Stage 3 Detail (Digest Pipeline)

```
_digest_article()
    ├─▶ _evaluate_relevance()   → "relevant" / "uncertain" / "discard"
    │       └─▶ _call_ai()      (temperature=0.1)
    ├─▶ [if discard]   → move to Discarded stage
    ├─▶ [if uncertain] → leave in New stage for human review
    └─▶ [if relevant]  → _handle_relevant()
            ├─▶ move to Relevant stage
            ├─▶ _generate_teaser()      → _call_ai() (temperature=0.7)
            └─▶ _create_blog_post()
                    └─▶ _get_header_image_for_blog()
                            ├─▶ article.header_image (if present)
                            └─▶ _search_pixabay() + _download_pixabay_image() (fallback)
```

### Content Processing Flow (Stages 1 & 2)

1. **Fetch** → `fetch_page()` via crawl4ai REST API (returns markdown + images dict)
2. **Pre-clean** → BeautifulSoup strips nav/footer/script/style tags + removes attributes
3. **AI Extract** → Send cleaned content to Infomaniak AI, parse JSON response
4. **Store** → Write to Odoo database

### Fallback Mechanisms

- **HTTP errors from crawl4ai** → `RetryableJobError` with escalating retry (5min → 15min → 1hr)
- **PDF documents** → Text extracted via `pdfminer`, then sent to AI
- **Transient errors** → `RetryableJobError` with escalating retry (5min → 15min → 1hr)
- **Missing header image** → Pixabay API search using article title as query

## Codebase Map

```
newsassistant/                # project root = git repo root
├── agents.md                 # THIS FILE - project-level guidance
├── docker-compose.yml        # Container setup (Odoo 18 + volumes)
├── odoo.conf                 # Odoo config (queue_job channels, workers)
├── .env                      # API keys (INFOMANIAK_AI_API_KEY)
├── news_source.csv           # Source URLs for import
├── newsassistant/            # Core addon v18.0.2.1.0 — scraping & triage kanban
│   ├── __manifest__.py       # Dependencies: base, queue_job
│   ├── README.md             # User-facing documentation
│   ├── agents.md             # Addon-level coding standards & DoD
│   ├── models/
│   │   ├── news_source.py    # Source model + AI service + HTML cleaner + Stage 1
│   │   ├── news_article.py   # Article model + Stage 2 extraction
│   │   ├── news_article_stage.py  # Kanban stages
│   │   ├── news_log.py       # Unified operation log
│   │   └── news_log_entry.py # Detail entries per log (LLM request/response metadata)
│   ├── views/
│   │   ├── news_source_views.xml   # Source list/form views
│   │   ├── news_article_views.xml  # Article kanban/form views
│   │   └── menu.xml                # Menu structure
│   ├── data/
│   │   ├── news_article_stage_data.xml   # Default kanban stages
│   │   ├── queue_job_data.xml            # Queue channel config
│   │   ├── ir_cron_data.xml              # Daily scrape cron
│   │   └── ir_config_parameter_data.xml  # Default product ID
│   ├── demo/
│   │   └── news_source_demo.xml    # Sample sources for testing
│   ├── security/
│   │   └── ir.model.access.csv     # Access rights
│   └── tests/
│       ├── test_news_source.py       # Source model tests
│       ├── test_html_cleaner.py      # HTML pre-cleaning tests
│       ├── test_url_normalization.py # URL dedup logic tests
│       ├── test_scraping_pipeline.py # End-to-end pipeline tests (mocked)
│       ├── test_queue_jobs.py        # Job creation tests with trap_jobs()
│       ├── test_kanban.py            # Stage workflow tests
│       ├── test_article_state.py     # Article state machine tests
│       └── test_header_image.py      # Header image selection tests
└── newsassistant_blog/       # Extension addon v18.0.1.0.0 — digest & blog publishing
    ├── __manifest__.py       # Dependencies: newsassistant, website_blog
    ├── models/
    │   ├── news_article.py   # Extends news.article: digest pipeline + Pixabay
    │   ├── blog_post.py      # Extends blog.post: adds news_article_id backlink
    │   ├── news_log.py       # Extends news.log: adds "digest" category
    │   └── res_config_settings.py  # Blog settings (strategy, blog, Pixabay key)
    ├── views/
    │   ├── news_article_views.xml      # Digest state + teaser in article views
    │   ├── blog_post_views.xml         # Source article link in blog post views
    │   ├── res_config_settings_views.xml  # Blog settings UI
    │   └── menu.xml                    # Additional menu items
    ├── data/
    │   ├── ir_config_parameter_data.xml  # Default prompts
    │   └── ir_cron_data.xml              # Daily digest cron
    ├── security/
    │   └── ir.model.access.csv
    └── tests/
        ├── test_blog_header_image.py   # Blog header image logic tests
        └── test_pixabay.py             # Pixabay API integration tests
```

## Key Technologies

### Infomaniak AI Services

Swiss-hosted, OpenAI-compatible AI API. Data stays in Switzerland (GDPR/FADP compliant).

| Item | Value |
|------|-------|
| Endpoint | `https://api.infomaniak.com/2/ai/{product_id}/openai/v1/chat/completions` |
| Default Product ID | `103794` (stored in `ir.config_parameter` as `newsassistant.infomaniak_product_id`) |
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
    "temperature": 0.1,  # 0.7 for teaser generation
}
```

**Important**: Prompts start with `/no_think` to disable qwen3's thinking mode (prevents `<think>...</think>` blocks in output).

### crawl4ai (Self-Hosted)

Headless browser service (Chromium) that bypasses bot protection (Cloudflare, etc.) and returns clean content + image metadata. Runs as a Docker container alongside Odoo. The **primary** fetch mechanism for all page fetching.

| Item | Value |
|------|-------|
| Endpoint | `POST http://crawl4ai:11235/crawl` (configurable via Settings UI) |
| Auth | None (internal Docker network) |
| Timeout | 120 seconds |
| Output | JSON with `results[0].markdown` and `results[0].media.images` |
| Payload | `{"urls": [target_url]}` |

**`fetch_page(url)` signature** (module-level function in `crawl4ai_utils.py`):
```python
content, images_dict = fetch_page(url)
# content: cleaned markdown string (truncated to 30000 chars)
# images_dict: {alt: src, ...} from crawl4ai's image extraction
```

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

### Pixabay API

Image search service used as fallback when articles lack a suitable header image.

| Item | Value |
|------|-------|
| Endpoint | `https://pixabay.com/api/` |
| Auth | API key via Settings UI → stored as `newsassistant_blog.pixabay_api_key` in `ir.config_parameter` |
| Timeout | 15 seconds |
| Filters | `image_type=photo`, `orientation=horizontal`, `min_width=1000`, `min_height=400` |

## Environment Variables

Required in `.env` file (loaded via docker-compose):

| Variable | Required | Purpose |
|----------|----------|---------|
| `INFOMANIAK_AI_API_KEY` | Yes | AI extraction API key (Stages 1, 2, 3) |
| `CRAWL4AI_URL` | No | crawl4ai server URL (default: http://crawl4ai:11235, configurable via Settings UI) |
| `POSTGRES_PASSWORD` | Yes | Database connection |

**Pixabay API key** is configured via the Odoo Settings UI (not an env var), stored as `ir.config_parameter` key `newsassistant_blog.pixabay_api_key`.

**Verify env vars are set**:
```bash
docker exec odoo-newsassistant env | grep -E "(INFOMANIAK|CRAWL4AI)"
```

## Development Workflow

### Running Tests

```bash
# Run all newsassistant tests
docker exec odoo-newsassistant odoo --test-tags newsassistant --stop-after-init -d newsassistant

# Run all newsassistant_blog tests
docker exec odoo-newsassistant odoo --test-tags newsassistant_blog --stop-after-init -d newsassistant

# Run specific test class
docker exec odoo-newsassistant odoo --test-tags newsassistant.test_scraping_pipeline --stop-after-init -d newsassistant
```

### Upgrading After Code Changes

After any code change (models, views, data files), always upgrade the affected module(s) so Odoo applies schema migrations and reloads views:

```bash
cd /home/debian/projects/newsassistant
docker compose stop odoo-newsassistant

# Upgrade newsassistant
docker compose run --rm odoo odoo -u newsassistant -d newsassistant --stop-after-init

# Or upgrade the blog extension (also upgrades its dependency newsassistant)
docker compose run --rm odoo odoo -u newsassistant_blog -d newsassistant --stop-after-init

docker compose start odoo-newsassistant
```

A plain restart (`docker compose restart`) is **not sufficient** — it reloads Python files but does not apply new fields, updated views, or data file changes.

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

### Manually Trigger Digest

From Odoo UI: Article form → "Digest Now" button, or list view → Action → "Digest Selected"

Or via shell:
```python
# In Odoo shell
article = env['news.article'].browse(1)
article._digest_article()  # Runs synchronously (no queue)
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

# Mock fetch_page (crawl4ai — returns tuple)
@patch("odoo.addons.newsassistant.models.news_source.fetch_page")
def test_something(self, mock_fetch):
    mock_fetch.return_value = ("<html>...</html>", {})

# Mock AI API (POST) — newsassistant addon
@patch("odoo.addons.newsassistant.models.news_source.requests.post")
def test_ai(self, mock_post):
    mock_post.return_value = _make_mock_response(
        200,
        json_data={"choices": [{"message": {"content": '{"title": "Test"}'}}]}
    )

# Mock AI API (POST) — newsassistant_blog addon
@patch("odoo.addons.newsassistant_blog.models.news_article.requests.post")
def test_digest_ai(self, mock_post):
    mock_post.return_value = _make_mock_response(
        200,
        json_data={"choices": [{"message": {"content": '{"decision": "relevant", "reasoning": "Test"}'}}]}
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

### Articles not being digested / blog posts not created

**Check**:
1. Settings → News Assistant → Blog Settings: Is Content Strategy configured?
2. Settings → News Assistant → Blog Settings: Is Target Blog set?
3. Queue Jobs view: Are Stage 3 digest jobs pending/failed?
4. News → Logs: Check digest log entries for error messages.

### Pixabay images not appearing on blog posts

**Check**:
1. Settings → News Assistant → Blog Settings: Is Pixabay API Key set?
2. Article `header_image` field — if populated, Pixabay is not used (article image takes priority).

### Tests fail with "queue_job not found"

**Cause**: Test running without OCA queue addons in path

**Fix**: Ensure `addons_path` in `odoo.conf` includes `/mnt/oca/queue`

## Data Models

### newsassistant addon

| Model | Key Fields | Purpose |
|-------|------------|---------|
| `news.source` | `name`, `url`, `active`, `state`, `error_message`, `last_scrape_date` | Website to scrape |
| `news.article` | `title`, `url` (unique, indexed), `source_id`, `date`, `summary`, `content`, `stage_id`, `state` (pending/scraped/error/skipped), `header_image`, `header_image_filename` | Extracted article |
| `news.article.stage` | `name`, `sequence`, `fold` | Kanban column (New, Relevant, Archived, Discarded) |
| `news.log` | `timestamp`, `level`, `category` (listing/extraction/digest), `message`, `duration`, `source_id`, `article_id`, `job_id`, `created_article_ids` | Operation log summary |
| `news.log.entry` | `log_id`, `timestamp`, `level`, `message`, `duration`, `metadata` (JSON) | Detail step within a log; stores LLM request/response data |

### newsassistant_blog addon (extends above)

| Model | Added Fields | Purpose |
|-------|-------------|---------|
| `news.article` (extended) | `digest_state` (pending/processed), `teaser`, `blog_post_ids` (O2M), `blog_post_count` | Digest pipeline state and teaser text |
| `blog.post` (extended) | `news_article_id` (M2O → news.article, unique) | Backlink to source article |
| `news.log` (extended) | `category` += `"digest"` | Enables digest log records |
| `res.config.settings` (extended) | `newsfeed_content_strategy`, `newsfeed_teaser_prompt`, `newsfeed_blog_id`, `newsfeed_pixabay_api_key` | Blog configuration UI |

## Definition of Done

Before marking work complete, verify:

- [ ] Module upgraded after code changes (`odoo -u <module> -d newsassistant --stop-after-init`)
- [ ] Code follows Odoo 18 conventions (see `addons/newsassistant/agents.md`)
- [ ] All external calls mocked in tests — no real HTTP/AI requests
- [ ] Tests pass: `odoo --test-tags newsassistant --stop-after-init` and `odoo --test-tags newsassistant_blog --stop-after-init`
- [ ] Queue jobs use `channel="root.newsassistant"` and have `description`
- [ ] Transient errors raise `RetryableJobError`, permanent errors are logged
- [ ] README.md updated if user-facing behavior changed
- [ ] agents.md updated

## Quick Reference

| Task | Command/Location |
|------|-----------------|
| Run newsassistant tests | `docker exec odoo-newsassistant odoo --test-tags newsassistant --stop-after-init -d newsassistant` |
| Run newsassistant_blog tests | `docker exec odoo-newsassistant odoo --test-tags newsassistant_blog --stop-after-init -d newsassistant` |
| View logs | `docker logs -f odoo-newsassistant` |
| Restart (view/Python-only) | `docker compose restart odoo-newsassistant` |
| Upgrade after model/view changes | `docker compose stop && docker run ... odoo -u newsassistant -d newsassistant --stop-after-init && docker compose start` |
| Source model | `newsassistant/models/news_source.py` |
| Article model (scrape) | `newsassistant/models/news_article.py` |
| Article model (digest) | `newsassistant_blog/models/news_article.py` |
| Blog post model | `newsassistant_blog/models/blog_post.py` |
| Settings model | `newsassistant_blog/models/res_config_settings.py` |
| AI call (scraping) | `news.source._call_infomaniak_ai(system_prompt, content)` |
| AI call (digest) | `news.article._call_ai(system_prompt, content, temperature=0.1)` |
| Page fetch | `fetch_page(url)` → `(content, images_dict)` in `news_source.py` |
| HTML cleaner | `news_source.clean_html(raw_html)` |
| URL normalizer | `news_source.normalize_url(url)` |
| JSON parser (scraping) | `news_source.parse_ai_json(text, expect_array=True)` |
| JSON parser (digest) | `news.article._parse_ai_json(raw_text)` |
| Digest pipeline entry | `news.article._cron_digest_all_impl()` |
| Evaluate relevance | `news.article._evaluate_relevance(content_strategy, ...)` |
| Generate teaser | `news.article._generate_teaser(log_entries, add_entry)` |
| Create blog post | `news.article._create_blog_post(teaser, ...)` |
| Pixabay search | `news.article._search_pixabay(query)` |

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
| Digest | Digest | Digest |
| Teaser | Teaser | Accroche |

### Installing Languages (First Time Setup)

Before translations can be used, the target languages must be installed in Odoo:

```bash
# Stop Odoo first
cd /home/debian/projects/newsassistant
docker compose stop odoo-newsassistant

# Load German and French languages
docker compose run --rm odoo odoo --load-language=de_DE,fr_FR -d newsassistant --stop-after-init

# Update module to load translations from .po files
docker compose run --rm odoo odoo -u newsassistant -d newsassistant --stop-after-init

# Start Odoo again
docker compose start odoo-newsassistant
```

### Updating Translations After Code Changes

When translatable strings change (new fields, labels, views, Python `_()` strings):

**1. Stop Odoo and update module:**
```bash
cd /home/debian/projects/newsassistant
docker compose stop odoo-newsassistant

docker compose run --rm odoo odoo -u newsassistant -d newsassistant --stop-after-init

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

docker compose run --rm odoo odoo -u newsassistant -d newsassistant --stop-after-init

docker compose start odoo-newsassistant
```

**5. Verify in Odoo:**

Switch user language to German/French in Preferences and verify all labels display correctly.

**Note:** The POT file is gitignored (generated on demand). Only the translated .po files are committed.
