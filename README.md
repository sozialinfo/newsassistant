# News Assistant

Automated news monitoring for Odoo, AI extraction, and content curation.

News Assistant monitors websites and email newsletters, uses AI to extract clean structured content,
and presents articles in a kanban board for triage. Optional extensions add AI-powered relevance
scoring, automatic blog publishing, and strategic intelligence briefs.

---

## Addons

| Addon | Description | Required? |
|---|---|---|
| `newsassistant` | Base: shared models, kanban UI, logging, security groups | Yes |
| `newsassistant_website` | Scrapes news websites via crawl4ai + AI | Optional |
| `newsassistant_email` | Captures inbound email newsletters via mail alias | Optional |
| `newsassistant_blog` | AI triage (relevant/uncertain/discard) + blog publishing | Optional |
| `newsassistant_strategy` | Strategy Base: shared strategy model for strategy ecosystem | Optional |
| `newsassistant_strategy_digest` | Strategy labels, article evaluation, executive PDF briefs | Optional |
| `newsassistant_strategy_watch` | Strategy Watch: flag articles with strategic watch relevance | Optional |

Each addon has its own `README.md` with detailed field references, configuration tables, and
technical notes.

---

## Prerequisites

- **Docker** and **Docker Compose**
- **API keys** (see Environment below)

---

## Quick Start — Local Development

```bash
git clone https://github.com/sozialinfo/newsassistant newsassistant
cd newsassistant
cp .env.example .env
# Edit .env with your API keys
docker compose up -d
```

After the container starts, the Odoo instance is available on the port configured in `odoo.conf` (default: 8069).

### Environment

```ini
# .env
INFOMANIAK_AI_API_KEY=your-infomaniak-key   # required — all AI calls
PIXABAY_API_KEY=your-pixabay-key            # optional — blog header images
CRAWL4AI_API_TOKEN=your-crawl4ai-token      # optional — crawl4ai auth (production)
```

| Variable | Required | Purpose |
|---|---|---|
| `INFOMANIAK_AI_API_KEY` | Yes | AI extraction, triage, digest, strategy evaluation |
| `POSTGRES_PASSWORD` | Yes | Postgres connection (empty string if no password) |
| `PIXABAY_API_KEY` | No | Fallback blog header images (also settable via Odoo Settings UI) |
| `CRAWL4AI_API_TOKEN` | No | Token to authenticate with crawl4ai (production) |

---

## Production Deployment

Two patterns depending on whether you are setting up everything from scratch or adding
crawl4ai to an existing Odoo server.

### Pattern 1: Full stack (Odoo + crawl4ai together)

Run the full stack on a single host. Use a dedicated Postgres instance (container or managed).
Adapt `docker-compose.yml` as needed — typical adjustments:

- Use your own Postgres connection details (host, port, user, password).
- Pin specific image tags instead of `:latest`.
- Set `CRAWL4AI_API_TOKEN` to secure the crawl4ai endpoint.

### Pattern 2: crawl4ai as a standalone service

If you already have an Odoo server (or want to share one crawl4ai instance across multiple
services), deploy crawl4ai behind a reverse proxy with token authentication:

```yaml
# docker-compose.crawl4ai.yml
services:
  crawl4ai:
    image: unclecode/crawl4ai:latest
    container_name: crawl4ai
    shm_size: 1g
    restart: unless-stopped
    expose:
      - "11235"
    environment:
      - CRAWL4AI_API_TOKEN=${CRAWL4AI_API_TOKEN}
    networks:
      - crawl4ai-net

  caddy:
    image: caddy:latest
    container_name: caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
    networks:
      - crawl4ai-net

volumes:
  caddy_data:

networks:
  crawl4ai-net:
```

Example `Caddyfile` — requires an `Authorization` header with the token:

```
crawl4ai.example.com {
    @health path /health
    handle @health {
        reverse_proxy crawl4ai:11235
    }
    @noauth not header Authorization *
    handle @noauth {
        respond 401
    }
    reverse_proxy crawl4ai:11235
}
```

The token is set via `CRAWL4AI_API_TOKEN`. Clients must send it as a Bearer token in the
`Authorization` header. In Odoo, set the crawl4ai endpoint URL and token in **Settings →
Technical → System Parameters**:

| Key | Value |
|---|---|
| `newsassistant.crawl4ai_endpoint` | `https://crawl4ai.example.com` |
| `newsassistant.crawl4ai_api_token` | `<your-token>` |

---

## Common Tasks

All commands use native Docker / Docker Compose — no `make` needed.

| Task | Command |
|---|---|
| Start services | `docker compose up -d` |
| Stop services | `docker compose down` |
| Restart Odoo | `docker compose restart odoo` |
| Follow Odoo logs | `docker compose logs -f odoo` |
| Open a shell | `docker compose exec odoo odoo shell -d newsassistant` |
| Init modules in a fresh DB | `docker compose run --rm odoo odoo -d newsassistant -i <modules> --stop-after-init` |
| Run all tests | `docker compose run --rm odoo odoo -d test_newsassistant_\`date +%s\` -i <modules> --test-enable --test-tags=/newsassistant --stop-after-init` |
| Run single module tests | `docker compose run --rm odoo odoo -d test_newsassistant_\`date +%s\` -i <module> --test-enable --test-tags=/<module> --stop-after-init` |
| Export translations | `docker compose exec odoo odoo -d newsassistant --modules=<module> --i18n-export=/tmp/<module>.pot --stop-after-init` |
| Send test email | `python scripts/sendmail.py test@example.ch newsassistant` |

**Rebuild from scratch** (drop DB → init → start):

```bash
docker compose down
docker compose exec postgres psql -U odoo -d postgres -c 'DROP DATABASE IF EXISTS "newsassistant";'
docker compose run --rm odoo odoo -d newsassistant -i newsassistant,newsassistant_website,newsassistant_email,newsassistant_blog,newsassistant_strategy,newsassistant_strategy_digest,newsassistant_strategy_watch --stop-after-init
docker compose up -d
```

---

## Upgrading after code changes

After any model, view, or data change, upgrade the affected module(s):

```bash
docker compose run --rm odoo odoo -u newsassistant -d newsassistant --stop-after-init

docker compose restart odoo
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
Then `docker compose restart odoo`.

### "Infomaniak AI API key not configured"

**Cause:** `INFOMANIAK_AI_API_KEY` not passed to the container.

**Fix:** Check `.env` has the key and `docker-compose.yml` passes it via `--env-file`.
Verify with: `docker compose exec odoo env | grep INFOMANIAK`

### Source shows "Error" after scraping

Open the source record and read the `error_message` field. Common causes:

| Error | Cause |
|---|---|
| HTTP 404 | Source URL has changed — update the URL |
| AI parse error | Page returned unexpected structure — check the log entries |
| Timeout | Website is slow or blocking — crawl4ai retry may help |

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