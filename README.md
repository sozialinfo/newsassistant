# News Assistant

Automated news monitoring, AI extraction, and content curation.

News Assistant monitors websites and email newsletters, uses AI to extract clean structured content,
and presents articles in a kanban board for triage. Optional extensions add AI-powered relevance
scoring, automatic blog publishing, and strategic intelligence briefs.

The core insight: AI acts as a **universal HTML-to-structured-data parser** — no per-source CSS
selectors, no breakage when websites redesign.

---

## Addons

| Addon | Description | Required? |
|---|---|---|
| `newsassistant` | Base: shared models, kanban UI, logging, security groups | Yes |
| `newsassistant_website` | Scrapes news websites via Jina Reader + AI | Optional |
| `newsassistant_email` | Captures inbound email newsletters via mail alias | Optional |
| `newsassistant_blog` | AI triage (relevant/uncertain/discard) + blog publishing | Optional |
| `newsassistant_strategy_digest` | Strategy labels, article evaluation, executive PDF briefs | Optional |

Each addon has its own `README.md` with detailed field references, configuration tables, and
technical notes.

---

## Prerequisites

- **Docker** and **Docker Compose**
- **External Postgres** container named `postgres` on the `opencode` Docker network (user `opencode`, no password)
- **OCA addons** cloned on the host:
  - `/home/debian/shared/odoo-src/18.0/oca/web`
  - `/home/debian/shared/odoo-src/18.0/oca/queue`
- **API keys** (see Setup below)

---

## Setup

### 1. Create `.env`

```bash
cp .env.example .env   # if it exists, otherwise create manually
```

```ini
# .env
INFOMANIAK_AI_API_KEY=your-infomaniak-key   # required — all AI calls
JINA_API_KEY=your-jina-key                  # required — website scraping
PIXABAY_API_KEY=your-pixabay-key            # optional — blog header images
```

| Variable | Required | Purpose |
|---|---|---|
| `INFOMANIAK_AI_API_KEY` | Yes | AI extraction, triage, digest, strategy evaluation |
| `JINA_API_KEY` | Yes | Headless-browser page fetching (bypasses bot protection) |
| `POSTGRES_PASSWORD` | Yes | Postgres connection (empty string if no password) |
| `PIXABAY_API_KEY` | No | Fallback blog header images (also settable via Odoo Settings UI) |

### 2. Build the database from scratch

```bash
make rebuild
```

This drops any existing `newsassistant` database, initialises all modules, starts the container,
applies post-setup (admin language, security groups, Pixabay key), and runs a smoke test.

---

## Make targets

```bash
make rebuild        # Full clean slate: drop DB → init → start → post-setup → smoke test
make init           # Init all modules into a fresh DB (no start)
make start          # docker compose up -d
make down           # docker compose down
make restart        # Reload Python/views only — NOT sufficient after model/view/data changes
make logs           # Follow container logs
make shell          # Open an Odoo interactive shell
```

### Testing

```bash
make test                          # Run all module test suites
make test-module MODULE=newsassistant_blog   # Run a single module's tests
```

### Translations

```bash
make i18n-update    # Export fresh .pot files for all modules to /tmp/
make i18n-install   # Reload de_CH / de_DE / fr_FR translations into the running instance
```

### Email testing

```bash
make sendmail test@example.ch   # Inject a test HTML newsletter from that address
```

---

## Upgrading after code changes

A plain `make restart` reloads Python files but does **not** apply new fields, updated views, or
data file changes. After any model, view, or data change, upgrade the affected module(s):

```bash
make down

docker run --rm --network opencode \
  -v $(pwd):/mnt/extra-addons \
  -v $(pwd)/odoo.conf:/etc/odoo/odoo.conf:ro \
  -v /home/debian/shared/odoo-src/18.0/oca/web:/mnt/oca/web:ro \
  -v /home/debian/shared/odoo-src/18.0/oca/queue:/mnt/oca/queue:ro \
  --env-file $(pwd)/.env \
  odoo:18.0 odoo -u newsassistant -d newsassistant --stop-after-init

make start
```

Replace `newsassistant` with the addon you changed (e.g. `newsassistant_blog`). Upgrading an
addon automatically upgrades its dependencies.

---

## Configuration

After a fresh install, most defaults work out of the box. The following require manual setup:

### Blog publishing (`newsassistant_blog`)

Go to **News Assistant → Configuration → Settings**:

| Setting | Description |
|---|---|
| Content Strategy | Prompt defining what is "relevant" vs. "uncertain" vs. "discard" |
| Teaser Prompt | Style and length instructions for AI-generated teasers |
| Target Blog | Odoo blog where curated articles are published |
| Pixabay API Key | Fallback image source when articles have no header image |
| Stage mappings | Which kanban stages map to Shortlist / Published / Discard |

### Email capture (`newsassistant_email`)

Go to **News Assistant → Configuration → Settings**:

| Setting | Description |
|---|---|
| Email Alias | Alias name for the inbound address (e.g. `newsassistant` → `newsassistant@yourdomain.com`) |

The alias requires a valid Odoo mail domain configured in Settings → Technical → Email → Outgoing.

### Strategy digest (`newsassistant_strategy_digest`)

Go to **Strategy Digest → Configuration → Strategies**:

1. Create a strategy, upload PDF documents or add a description.
2. Click **Distill Prompt** to generate labels and an AI evaluation prompt.
3. Set the strategy state to **Active** — the hourly cron will then label new articles automatically.

### Infomaniak AI Product ID

Default: `103794`. Change at Settings → Technical → Parameters → System Parameters,
key `newsassistant.infomaniak_product_id`.

---

## Troubleshooting

### Jobs stuck in "enqueued" state

**Cause:** The queue runner is not starting.

**Fix:** Ensure `odoo.conf` has:
```ini
server_wide_modules = web,queue_job
workers = 2
```
Then `make restart`.

### "Infomaniak AI API key not configured"

**Cause:** `INFOMANIAK_AI_API_KEY` not passed to the container.

**Fix:** Check `.env` has the key and `docker-compose.yml` passes it via `--env-file`.
Verify with: `docker exec odoo-newsassistant env | grep INFOMANIAK`

### Source shows "Error" after scraping

Open the source record and read the `error_message` field. Common causes:

| Error | Cause |
|---|---|
| HTTP 404 | Source URL has changed — update the URL |
| AI parse error | Page returned unexpected structure — check the log entries |
| Timeout | Website is slow or blocking — Jina fallback may help |

### Articles not appearing after scraping

1. Check the source's `last_scrape_date` — if not updated, Stage 1 failed (see log).
2. Check Settings → Technical → Queue → Jobs for failed Stage 2 jobs.
3. Check the article record's `state` field and `news.log` for error details.

### Articles not being digested / blog posts not created

1. Confirm **Content Strategy** and **Target Blog** are set in Blog Settings.
2. Check Settings → Technical → Queue → Jobs for failed digest jobs.
3. Check News Assistant → Logs, category "digest", for AI response details.

### Pixabay images not appearing on blog posts

1. Check that the Pixabay API key is set (Settings → News Assistant → Blog Settings).
2. Check the article's `header_image` field — if it is populated, Pixabay is not used (article image takes priority).

---

## License

The project is licensed under **AGPL-3** (see `LICENSE`).  
Individual addons declare **LGPL-3** in their `__manifest__.py`.
