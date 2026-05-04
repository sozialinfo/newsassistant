# Hardening Tasks — newsassistant project

Generated from audit.md. Each task references the finding ID.

---

## Code Quality Tasks

### T01 — Fix `models.UserError` AttributeError (F2.25) [CRITICAL]
**File:** `newsassistant/models/news_source.py`
`_get_ai_api_key()` raises `models.UserError` which is incorrect. Add `from odoo.exceptions import UserError` to the import block and change the raise to `raise UserError(...)`.

### T02 — Move all in-body imports to module top-level: news_source.py (F2.1, F2.2, F2.3)
**File:** `newsassistant/models/news_source.py`
Move `import re`, `import time`, `import os` from inside function/method bodies to module top-level.

### T03 — Move all in-body imports to module top-level: news_snapshot.py (F2.4, F2.5)
**File:** `newsassistant/models/news_snapshot.py`
Move `import threading`, `from odoo.addons.queue_job.exception import RetryableJobError`, `from .news_source import parse_ai_json`, `from datetime import datetime` from method bodies to module top-level.

### T04 — Move all in-body imports to module top-level: newsassistant_blog/news_article.py (F2.6, F2.10, F2.11, F2.12, F2.13, F2.14)
**File:** `newsassistant_blog/models/news_article.py`
Move `import os`, `import re`, `from html import unescape`, `import base64`, `import mimetypes`, `from urllib.parse import urlparse`, `from odoo import api, SUPERUSER_ID` from method bodies to module top-level.

### T05 — Move all in-body imports to module top-level: strategy_digest.py (F2.7)
**File:** `newsassistant_strategy_digest/models/strategy_digest.py`
Move `import re` from method body to module top-level.

### T06 — Move all in-body imports to module top-level: strategy_strategy.py (F2.8)
**File:** `newsassistant_strategy_digest/models/strategy_strategy.py`
Move `import re` from `_parse_ai_json()` body to module top-level.

### T07 — Move all in-body imports to module top-level: newsassistant_strategy_digest/news_article.py (F2.9)
**File:** `newsassistant_strategy_digest/models/news_article.py`
Move `import re` from `_parse_ai_json()` body to module top-level.

### T08 — Move all in-body imports to module top-level: image_utils.py (F2.18)
**File:** `newsassistant_website/models/image_utils.py`
Move `from io import BytesIO` from method body to module top-level (keep `from PIL import Image` inside try/except for optional dependency).

### T09 — Move all in-body imports to module top-level: news_source_website.py (F2.20, F2.21)
**File:** `newsassistant_website/models/news_source_website.py`
Move `from odoo.addons.newsassistant.models.news_source import normalize_url, parse_ai_json` and `import base64` from method bodies to module top-level.

### T10 — Remove dead method `_cron_digest_all()` (F2.15, F7.1)
**File:** `newsassistant_blog/models/news_article.py:520-531`
Remove the dead `_cron_digest_all()` static method and its internal imports entirely.

### T11 — Fix `models.UserError` import in news_source.py (part of T01)
Already handled in T01.

### T12 — Add `sanitize=True` to `fields.Html` in strategy_strategy.py (F3.4)
**File:** `newsassistant_strategy_digest/models/strategy_strategy.py:83`
Change `prompt = fields.Html(...)` to `prompt = fields.Html(sanitize=True, ...)`.

### T13 — Add `sanitize=True` to `fields.Html` in strategy_digest.py (F3.5)
**File:** `newsassistant_strategy_digest/models/strategy_digest.py:59`
Change `brief = fields.Html(...)` to `brief = fields.Html(sanitize=True, ...)`.

### T14 — Fix N+1 query: batch `_compute_article_count`, `_compute_snapshot_count`, `_compute_log_count` (F5.1, F2.16)
**File:** `newsassistant/models/news_source.py:229-245`
Replace per-record `search_count()` loops with batched SQL using `read_group` or a single SQL query per compute method.

### T15 — Fix N+1 query: batch `_compute_blog_post_count` (F5.2)
**File:** `newsassistant_blog/models/news_article.py:55-57`
Replace `len(article.blog_post_ids)` loop with `read_group`.

### T16 — Fix N+1 query: batch `_compute_created_article_count` (F5.3)
**File:** `newsassistant/models/news_log.py:85-87`
Replace `len(log.created_article_ids)` loop with `read_group`.

### T17 — Refactor `_extract_articles()` method (>100 lines) (F7.3)
**File:** `newsassistant/models/news_snapshot.py:101-286`
Extract sub-steps into private methods:
- `_extract_articles_call_ai()` — AI call
- `_extract_articles_parse_response()` — JSON parsing
- `_extract_articles_create_article()` — record creation
Preserve all behavior exactly.

### T18 — Refactor `_do_distill_prompt()` method (>100 lines) (F7.6)
**File:** `newsassistant_strategy_digest/models/strategy_strategy.py:323-464`
Extract sub-steps into private methods:
- `_distill_gather_content()` — gather PDF + description text
- `_distill_call_ai()` — AI call
- `_distill_parse_response()` — JSON parsing
- `_distill_save_labels_prompt()` — save labels and prompt
Preserve all behavior exactly.

### T19 — Fix manifest data load order: move server_actions.xml before menu.xml (F1.1)
**File:** `newsassistant/__manifest__.py`
Move `"data/server_actions.xml"` to appear before `"views/menu.xml"` in the data list.

### T20 — Remove empty `<header>` from news_source_view_form (F4.4)
**File:** `newsassistant/views/news_source_views.xml:35-36`
Remove the empty `<header></header>` block from the source form view.

### T21 — Add `role="alert"` to alert div in strategy_digest_views.xml (F4.5)
**File:** `newsassistant_strategy_digest/views/strategy_digest_views.xml:42`
Add `role="alert"` to the info alert div.

### T22 — Add `<chatter/>` to news_snapshot form view (F4.3)
**File:** `newsassistant/views/news_snapshot_views.xml`
Since `news.snapshot` inherits `mail.thread` (in newsassistant_email), add a chatter to the snapshot form view via an inherited view in `newsassistant_email`.

### T23 — Use module-specific security groups for strategy models (F3.2)
**File:** `newsassistant_strategy_digest/security/ir.model.access.csv`
Replace `base.group_user` with `newsassistant.newsassistant_group_user` and `newsassistant.newsassistant_group_admin` for strategy models, to align with the module's group hierarchy.

### T24 — Add settings field for Infomaniak product ID (F6.4)
**File:** `newsassistant/models/res_config_settings.py` and `views/res_config_settings_views.xml`
Add `newsassistant_infomaniak_product_id` field to `res.config.settings` with `config_parameter="newsassistant.infomaniak_product_id"`.

---

## Documentation Tasks

### T25 — Create README.md for newsassistant_blog (F8.1)
Create `newsassistant_blog/README.md` with all 7 required sections.

### T26 — Create README.md for newsassistant_email (F8.2)
Create `newsassistant_email/README.md` with all 7 required sections.

### T27 — Create README.md for newsassistant_website (F8.3)
Create `newsassistant_website/README.md` with all 7 required sections.

### T28 — Create README.md for newsassistant_strategy_digest (F8.4)
Create `newsassistant_strategy_digest/README.md` with all 7 required sections.

### T29 — Update newsassistant README.md model table (F8.5)
**File:** `newsassistant/README.md`
Add `news.snapshot`, `news.log`, `news.log.entry` to the models table.

---

## Security Tasks

### T30 — Add test_security.py to newsassistant (F3.6)
Create `newsassistant/tests/test_security.py` testing:
- Group hierarchy: Admin implies User
- Per-role CRUD on news.source, news.article, news.snapshot, news.log
- AccessError for unauthorized operations

---

## Structural Tasks

### T31 — Create icon.png for newsassistant_strategy_digest (F6.1)
Generate a 128×128 PNG icon using the module's initials (SD) and place at `newsassistant_strategy_digest/static/description/icon.png`.

### T32 — Create icon.png for newsassistant_email (F6.2)
Generate a 128×128 PNG icon using the module's initials (E) and place at `newsassistant_email/static/description/icon.png`.

### T33 — Create icon.png for newsassistant_website (F6.3)
Generate a 128×128 PNG icon using the module's initials (W) and place at `newsassistant_website/static/description/icon.png`.

---

## Infrastructure Tasks (mandatory — execute last)

### T-INF-1 — Version bump all modified manifests
- newsassistant: bump patch (code quality only) → `18.0.3.0.1`
- newsassistant_blog: bump patch → `18.0.1.0.1`
- newsassistant_email: bump patch → `18.0.1.0.1`
- newsassistant_strategy_digest: bump patch → `18.0.1.0.1`
- newsassistant_website: bump patch → `18.0.1.0.1`

### T-INF-2 — Fresh instance rebuild
```bash
make rebuild
```

### T-INF-3 — Run tests (all must be green)
```bash
make test
```

### T-INF-4 — Run coverage (must be ≥ 80%)
```bash
make test-coverage
```
Write additional tests if below threshold.

### T-INF-5 — Install DE+FR translations
```bash
make i18n-install
```

### T-INF-6 — Switch admin/demo users to German
```bash
docker compose exec -T odoo odoo shell -d newsassistant -c /etc/odoo/odoo.conf --http-port=18069 <<'EOF'
env['res.users'].search([('login', 'in', ['admin', 'demo'])]).write({'lang': 'de_CH'})
env.cr.commit()
EOF
```

### T-INF-7 — Smoke test
```bash
make smoke
```
