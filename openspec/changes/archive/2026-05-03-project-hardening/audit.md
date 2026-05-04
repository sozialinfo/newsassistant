# Hardening Audit — newsassistant project

**Date:** 2026-05-03
**Odoo version:** 18.0 CE
**Modules:** newsassistant, newsassistant_blog, newsassistant_email, newsassistant_strategy_digest, newsassistant_website

---

## Category 1 — Manifest Integrity

### F1.1 newsassistant — `data/server_actions.xml` loaded after menus
**File:** `newsassistant/__manifest__.py:37`
`data/server_actions.xml` is listed after `views/menu.xml`, violating the required order (menus must be last).

### F1.2 newsassistant_blog — empty `ir.model.access.csv`
**File:** `newsassistant_blog/security/ir.model.access.csv`
The CSV file contains only the header row. Models `blog.post` (inherited with new field `news_article_id`) and the `res.config.settings` extension do not require new ACL rows, but `blog.post` inherits from `website_blog` — this is acceptable. However the empty file is misleading and should be reviewed.

### F1.3 newsassistant_email — empty `ir.model.access.csv`
**File:** `newsassistant_email/security/ir.model.access.csv`
The model `news.snapshot` is extended with `mail.thread` and `mail.alias.mixin` — no new models introduced. Empty file is acceptable but misleading.

### F1.4 newsassistant_website — empty `ir.model.access.csv`
**File:** `newsassistant_website/security/ir.model.access.csv`
Same pattern — no new models, but empty file.

### F1.5 newsassistant_blog — missing security XML with `noupdate="1"` for `ir_cron_data.xml`
**File:** `newsassistant_blog/data/ir_cron_data.xml:3`
Cron job correctly has `noupdate="1"`. ✓

### F1.6 newsassistant_strategy_digest — missing `noupdate="1"` on `ir.model.access.csv` not applicable (CSV never needs noupdate).
No issue.

### F1.7 newsassistant_strategy_digest — security XML missing (no `newsassistant_security.xml`)
The module uses `base.group_user` and `base.group_system` for access rules, but does not have module-specific security groups. Given the module extends `newsassistant`, this may be intentional. However, there are no record rules protecting `strategy.strategy` or `strategy.digest` records — any user can read/write all strategies.

### F1.8 All modules — `data/ir_cron_data.xml` references should all have `noupdate="1"` ✓
All cron files have `noupdate="1"`. ✓

### F1.9 newsassistant — `ir_config_parameter_data.xml` missing `noupdate="1"` on system parameters
**File:** `newsassistant/data/ir_config_parameter_data.xml:3`
`noupdate="1"` is set. ✓

### F1.10 newsassistant — queue_job_data.xml missing `noupdate="1"` wrapper
**File:** `newsassistant/data/queue_job_data.xml:2`
Uses `<odoo noupdate="1">` — correct. ✓

---

## Category 2 — Python Code Correctness

### F2.1 `import re` inside method body — news_source.py
**File:** `newsassistant/models/news_source.py:89`
`import re` is inside the `parse_ai_json()` function body. Must be moved to module top-level.

### F2.2 `import time`, `import os` inside method body — news_source.py
**File:** `newsassistant/models/news_source.py:349`
`import time` inside `_call_infomaniak_ai()`. Must be at module top-level.

### F2.3 `import os` inside method body — news_source.py
**File:** `newsassistant/models/news_source.py:315`
`import os` inside `_get_ai_api_key()`. Must be at module top-level.

### F2.4 `import threading` inside method body — news_snapshot.py
**File:** `newsassistant/models/news_snapshot.py:84`
`import threading` inside `create()`. Must be at module top-level.

### F2.5 `import re`, `from odoo.addons.queue_job...`, `from .news_source import parse_ai_json`, `from datetime import datetime` inside method body — news_snapshot.py
**File:** `newsassistant/models/news_snapshot.py:189,204,253`
Multiple imports inside `_extract_articles()`. Must be at module top-level.

### F2.6 `import re`, `from html import unescape`, `import re` inside method body — newsassistant_blog/models/news_article.py
**File:** `newsassistant_blog/models/news_article.py:412,499,500,663,664,801,802`
`import os`, `import re`, `from html import unescape` inside `_call_ai()`, `_parse_ai_json()`, `_evaluate_relevance()`, `_generate_teaser()`. Must be at module top-level.

### F2.7 `import re` inside method body — newsassistant_strategy_digest/models/strategy_digest.py
**File:** `newsassistant_strategy_digest/models/strategy_digest.py:323`
`import re` inside `action_generate_brief()`. Must be at module top-level.

### F2.8 `import re` inside method body — newsassistant_strategy_digest/models/strategy_strategy.py
**File:** `newsassistant_strategy_digest/models/strategy_strategy.py:276`
`import re` inside `_parse_ai_json()`. Must be at module top-level.

### F2.9 `import re`, `import json` inside method body — newsassistant_strategy_digest/models/news_article.py
**File:** `newsassistant_strategy_digest/models/news_article.py:127`
`import re` inside `_parse_ai_json()`. Must be at module top-level.

### F2.10 `import os` inside method body — newsassistant_blog/models/news_article.py
**File:** `newsassistant_blog/models/news_article.py:412`
`import os` inside `_call_ai()`. Must be at module top-level.

### F2.11 `import base64`, `import mimetypes` inside method body — newsassistant_blog/models/news_article.py
**File:** `newsassistant_blog/models/news_article.py:850,851`
Inside `_create_header_image_attachment()`. Must be at module top-level.

### F2.12 `import base64` inside method body — newsassistant_blog/models/news_article.py
**File:** `newsassistant_blog/models/news_article.py:892`
Inside `_get_header_image_for_blog()`. Must be at module top-level.

### F2.13 `from urllib.parse import urlparse` inside method body — newsassistant_blog/models/news_article.py
**File:** `newsassistant_blog/models/news_article.py:956`
Inside `_create_blog_post()`. Must be at module top-level.

### F2.14 `from odoo import api, SUPERUSER_ID` inside method body — newsassistant_blog/models/news_article.py
**File:** `newsassistant_blog/models/news_article.py:527`
Inside `_cron_digest_all()` (a static method with `pass` body — dead code). Must be removed.

### F2.15 Dead method `_cron_digest_all()` — newsassistant_blog/models/news_article.py
**File:** `newsassistant_blog/models/news_article.py:520-531`
Method `_cron_digest_all()` contains only `pass` and a dead import. Must be removed.

### F2.16 `_compute_article_count()` uses per-record `search_count()` — news_source.py
**File:** `newsassistant/models/news_source.py:229-232`
`_compute_article_count`, `_compute_snapshot_count`, `_compute_log_count` all call `search_count()` per record in a loop — N+1 query pattern. Must be batched using single SQL query.

### F2.17 `@api.model_create_multi` missing on `news_source.py` — no `create()` override there, OK.

### F2.18 `from io import BytesIO` inside method body — newsassistant_website/models/image_utils.py
**File:** `newsassistant_website/models/image_utils.py:47`
Inside `validate_and_download_image()`. Must be at module top-level.

### F2.19 `from PIL import Image` inside method body — newsassistant_website/models/image_utils.py
**File:** `newsassistant_website/models/image_utils.py:51`
Conditional import for optional dependency — this is acceptable pattern (guarded by try/except). Mark as acceptable.

### F2.20 `from odoo.addons.newsassistant.models.news_source import normalize_url, parse_ai_json` inside method body — news_source_website.py
**File:** `newsassistant_website/models/news_source_website.py:89,362`
Inside `_scrape_listing()` and `_extract_articles_website()`. Must be at module top-level.

### F2.21 `import base64` inside method body — news_source_website.py
**File:** `newsassistant_website/models/news_source_website.py:368`
Inside `_extract_articles_website()`. Must be at module top-level.

### F2.22 AI call duplicated across 4 modules — DRY violation
`_call_ai()` / `_call_infomaniak_ai()` is copy-pasted in:
- `newsassistant/models/news_source.py`
- `newsassistant_blog/models/news_article.py`
- `newsassistant_strategy_digest/models/strategy_digest.py`
- `newsassistant_strategy_digest/models/news_article.py`

The base implementation lives in `news_source.py`. The `newsassistant_strategy_digest` and `newsassistant_blog` versions should call through to the base, or a shared mixin should be extracted. This is a Cat 10 concern too — refactor where the base method is accessible without circular import.

### F2.23 `_parse_ai_json()` duplicated in 3 places
Same pattern as above — `newsassistant_blog/models/news_article.py`, `newsassistant_strategy_digest/models/strategy_strategy.py`, `newsassistant_strategy_digest/models/news_article.py` all copy the same JSON parsing logic. The canonical version lives in `newsassistant/models/news_source.py` as `parse_ai_json()`.

### F2.24 `_compute_is_scraping` in `news_source.py` has a logic error
**File:** `newsassistant/models/news_source.py:206-211`
When `not self.ids`, the method sets `is_scraping = False` in a loop but that block is actually unreachable if `self.ids` is empty (no iteration would happen anyway). Safe but misleading — can be simplified.

### F2.25 `NewsSource._get_ai_api_key()` raises `models.UserError` without import
**File:** `newsassistant/models/news_source.py:318`
`models.UserError` is incorrect — `UserError` is `odoo.exceptions.UserError`, not `models.UserError`. This will raise `AttributeError` at runtime. Must be fixed to use `from odoo.exceptions import UserError`.

---

## Category 3 — Security

### F3.1 Admin/manager groups have no default users added in security XML
**File:** `newsassistant/security/newsassistant_security.xml`
Groups `newsassistant_group_user` and `newsassistant_group_admin` exist but no users are added via `<field name="users" ...>`. Admin user (id=2) is added in `post-setup` via Makefile shell. This is acceptable for this project. However the hardening reference requires admin/manager groups to have default users added in security XML.

### F3.2 `strategy.strategy` and `strategy.digest` have no module-specific security groups
**File:** `newsassistant_strategy_digest/security/ir.model.access.csv`
Uses `base.group_user` (all internal users) for full CRUD on strategies and digests. Any internal user can delete strategies. Should use newsassistant group hierarchy.

### F3.3 `strategy.label` — read-only for users, but create/write/delete granted to `base.group_system`
**File:** `newsassistant_strategy_digest/security/ir.model.access.csv:2`
Regular users can only read labels, not create/edit. Labels are created only by AI distillation (system/admin). This is fine.

### F3.4 `fields.Html` without `sanitize=` — strategy_strategy.py prompt field
**File:** `newsassistant_strategy_digest/models/strategy_strategy.py:83`
`prompt = fields.Html(...)` has no explicit `sanitize=` declaration. Must add `sanitize=True`.

### F3.5 `fields.Html` — `strategy.digest.brief` without explicit sanitize
**File:** `newsassistant_strategy_digest/models/strategy_digest.py:59`
`brief = fields.Html(...)` missing explicit `sanitize=` declaration. Must add `sanitize=True`.

### F3.6 No `test_security.py` in any module
None of the 5 modules has a `test_security.py` file. The reference requires a dedicated security test file per module (group hierarchy, per-role CRUD, record rule enforcement). Must be added to at least `newsassistant` (the base module).

---

## Category 4 — XML / View Quality

### F4.1 `news_source_views.xml` — missing action record in file (action defined in menu.xml)
**File:** `newsassistant/views/menu.xml:4-18`
The `news_source_action` is defined inside `menu.xml` rather than in `news_source_views.xml`. This is a minor structural issue but deviates from the convention that actions should live in the view file.

### F4.2 `strategy_digest_views.xml` — `strategy_digest_action` lacks search view
**File:** `newsassistant_strategy_digest/views/strategy_digest_views.xml:96`
The list/form action for `strategy.digest` has no search view defined. A search view should be added.

### F4.3 Form views missing `<chatter/>` on models with `mail.thread`
**File:** `newsassistant_email/models/news_snapshot_email.py:84`
`news.snapshot` inherits `mail.thread` in the email module, but `news_snapshot_views.xml` has no chatter widget. Must add `<chatter/>` to the snapshot form view.

### F4.4 `news_source_view_form` — empty `<header>` element
**File:** `newsassistant/views/news_source_views.xml:35-36`
`<header></header>` is empty. Should be removed or contain buttons/statusbar.

### F4.5 `strategy_digest_views.xml` — `<div class="alert alert-info">` missing `role="alert"`
**File:** `newsassistant_strategy_digest/views/strategy_digest_views.xml:42`
Alert div is missing `role="alert"` attribute.

---

## Category 5 — Performance

### F5.1 `_compute_article_count`, `_compute_snapshot_count`, `_compute_log_count` — N+1 queries
**File:** `newsassistant/models/news_source.py:229-245`
Three separate `search_count()` calls in loops — each issues one SQL query per record. Must be refactored to batch SQL.

### F5.2 `_compute_blog_post_count` in newsassistant_blog — uses `len(blog_post_ids)` per record
**File:** `newsassistant_blog/models/news_article.py:55-57`
Uses `len(article.blog_post_ids)` per record — triggers per-record SQL. Should use batched `read_group`.

### F5.3 `_compute_created_article_count` in news_log.py — uses `len()` on M2M
**File:** `newsassistant/models/news_log.py:85-87`
Uses `len(log.created_article_ids)` per record. Should use `read_group`.

---

## Category 6 — Structural Completeness

### F6.1 `newsassistant_strategy_digest` missing `static/description/icon.png`
Module has no `static/description/` directory. Must create icon.

### F6.2 `newsassistant_email` missing `static/description/icon.png`
Module has no static directory at all. Must create icon.

### F6.3 `newsassistant_website` missing `static/description/icon.png` (has static/description)
No static directory found. Must create icon.

### F6.4 `newsassistant` missing `res.config.settings` field for Infomaniak product ID
The `newsassistant.infomaniak_product_id` parameter exists as a data record but is not surfaced in `res.config.settings`. Users cannot change it from the UI. Should add a settings field.

---

## Category 7 — Maintainability

### F7.1 `_cron_digest_all()` is dead code
**File:** `newsassistant_blog/models/news_article.py:520-531`
Static method with no body (only `pass`) and unreachable imports. Must be removed.

### F7.2 `NewsLog.category` in base module is missing `"digest"` value
**File:** `newsassistant/models/news_log.py:30-37`
`news_log.py` defines `category` with values `listing`, `extraction`, `email`. The `newsassistant_blog` module adds `digest` via `selection_add`. But the `_create_snapshot_log` in `news_snapshot.py` only uses `extraction`. The log in `newsassistant_email` uses `email`. This is architecturally correct.

### F7.3 `news_snapshot._extract_articles()` — 180+ line method
**File:** `newsassistant/models/news_snapshot.py:101-286`
Method is ~180 lines. Exceeds the 100-line limit. Must be refactored by extracting logical sub-steps.

### F7.4 `newsassistant_blog/news_article._digest_article()` — complex multi-step method
**File:** `newsassistant_blog/models/news_article.py:553-638`
Method orchestrates evaluation → discard/uncertain/shortlist. Already delegates to private methods — structurally OK. ~85 lines. Within limit.

### F7.5 `news_source._call_infomaniak_ai()` — 96 lines
**File:** `newsassistant/models/news_source.py:330-427`
Method is ~97 lines. Close to limit but acceptable. Not flagged.

### F7.6 `strategy_strategy._do_distill_prompt()` — ~120 lines
**File:** `newsassistant_strategy_digest/models/strategy_strategy.py:323-464`
Method is ~140 lines. Exceeds 100-line limit. Must be refactored.

---

## Category 8 — Documentation

### F8.1 `newsassistant_blog` missing `README.md`
Module has no README file at all. Must be created.

### F8.2 `newsassistant_email` missing `README.md`
Module has no README file at all. Must be created.

### F8.3 `newsassistant_website` missing `README.md`
Module has no README file at all. Must be created.

### F8.4 `newsassistant_strategy_digest` missing `README.md`
Module has no README file at all. Must be created.

### F8.5 `newsassistant` README references wrong model table
**File:** `newsassistant/README.md:162`
Table only mentions 3 models but module actually defines 5 (news.source, news.article, news.article.stage, news.snapshot, news.log, news.log.entry). Must be updated.

### F8.6 `newsassistant` README references wrong test command
**File:** `newsassistant/README.md:185`
Uses `odoo --test-tags` with deprecated syntax. Should be updated to current format.

---

## Category 9 — Tooling Compliance

### F9.1 No `.pre-commit-config.yaml` found
No pre-commit configuration found. Nothing to run. ✓ (skipped)

### F9.2 No `*.pot` files committed ✓
### F9.3 No `en.po` files ✓
### F9.4 No `*.rej` files ✓

---

## Category 10 — Standard Pattern Compliance

### F10.1 Custom HTML sanitization function `sanitize_email_html()` in newsassistant_email
**File:** `newsassistant_email/models/news_snapshot_email.py:35-77`
Implements custom HTML sanitization. Odoo provides `odoo.tools.mail.html_sanitize()`. However, the custom function performs email-specific sanitization (tracking pixel removal, 1×1 image removal) that `html_sanitize` does not cover. This is a justified custom implementation — NOT a flag.

### F10.2 `parse_ai_json()` / `_parse_ai_json()` duplicated — should use shared utility
**File:** Multiple files
`newsassistant/models/news_source.py:76` defines `parse_ai_json()` as a module-level function. `newsassistant_blog` and `newsassistant_strategy_digest` duplicate this as a method. Should import and use the base function.

### F10.3 `clean_html()` in news_source.py — custom but distinct from standard sanitize
**File:** `newsassistant/models/news_source.py:43-72`
Custom HTML cleaner for LLM consumption. Not a reimplementation of `html_sanitize` — serves a different purpose. Acceptable.

### F10.4 `html_to_markdown()` in utils.py — custom utility
**File:** `newsassistant/models/utils.py:15`
Custom Markdown converter. No standard Odoo equivalent. Acceptable.

---

## Summary of Findings

| ID | Category | Severity | File | Description |
|----|----------|----------|------|-------------|
| F1.1 | Manifest | Medium | newsassistant/__manifest__.py | server_actions.xml loaded after menu.xml |
| F2.1 | Python | High | news_source.py | `import re` inside function body |
| F2.2 | Python | High | news_source.py | `import time` inside method body |
| F2.3 | Python | High | news_source.py | `import os` inside method body |
| F2.4 | Python | High | news_snapshot.py | `import threading` inside create() |
| F2.5 | Python | High | news_snapshot.py | Multiple imports inside method bodies |
| F2.6 | Python | High | newsassistant_blog/news_article.py | Multiple imports inside method bodies |
| F2.7 | Python | High | strategy_digest.py | `import re` inside method body |
| F2.8 | Python | High | strategy_strategy.py | `import re` inside method body |
| F2.9 | Python | High | newsassistant_strategy_digest/news_article.py | `import re` inside method body |
| F2.10 | Python | High | newsassistant_blog/news_article.py | `import os` inside method body |
| F2.11 | Python | High | newsassistant_blog/news_article.py | `import base64`, `import mimetypes` inside method |
| F2.12 | Python | High | newsassistant_blog/news_article.py | `import base64` inside method body |
| F2.13 | Python | High | newsassistant_blog/news_article.py | `from urllib.parse import urlparse` inside method |
| F2.14 | Python | High | newsassistant_blog/news_article.py | Dead import inside dead method |
| F2.15 | Python | High | newsassistant_blog/news_article.py | Dead method `_cron_digest_all()` |
| F2.16 | Python | Medium | news_source.py | N+1 query in compute methods |
| F2.18 | Python | High | image_utils.py | `from io import BytesIO` inside method body |
| F2.20 | Python | High | news_source_website.py | Imports inside method bodies |
| F2.21 | Python | High | news_source_website.py | `import base64` inside method body |
| F2.22 | Python | Medium | Multiple | AI call duplicated across 4 modules |
| F2.23 | Python | Medium | Multiple | `_parse_ai_json` duplicated across 3 modules |
| F2.25 | Python | Critical | news_source.py | `models.UserError` — AttributeError at runtime |
| F3.2 | Security | Medium | strategy_digest/security | No module-specific groups for strategy models |
| F3.4 | Security | High | strategy_strategy.py | `fields.Html` missing `sanitize=` |
| F3.5 | Security | High | strategy_digest.py | `fields.Html` missing `sanitize=` |
| F3.6 | Security | High | All modules | No `test_security.py` |
| F4.3 | XML | Medium | news_snapshot_views.xml | Missing `<chatter/>` for mail.thread |
| F4.4 | XML | Low | news_source_views.xml | Empty `<header>` element |
| F4.5 | XML | Low | strategy_digest_views.xml | Alert div missing `role="alert"` |
| F5.1 | Performance | High | news_source.py | N+1 query in count computes |
| F5.2 | Performance | Medium | newsassistant_blog/news_article.py | Per-record M2M count |
| F5.3 | Performance | Medium | news_log.py | Per-record M2M count |
| F6.1 | Structural | Medium | newsassistant_strategy_digest | Missing icon.png |
| F6.2 | Structural | Medium | newsassistant_email | Missing icon.png |
| F6.3 | Structural | Medium | newsassistant_website | Missing icon.png |
| F6.4 | Structural | Low | newsassistant | Infomaniak product ID not in settings UI |
| F7.1 | Maintainability | Medium | newsassistant_blog/news_article.py | Dead code |
| F7.3 | Maintainability | Medium | news_snapshot.py | Method >100 lines |
| F7.6 | Maintainability | Medium | strategy_strategy.py | Method >100 lines |
| F8.1 | Documentation | High | newsassistant_blog | Missing README.md |
| F8.2 | Documentation | High | newsassistant_email | Missing README.md |
| F8.3 | Documentation | High | newsassistant_website | Missing README.md |
| F8.4 | Documentation | High | newsassistant_strategy_digest | Missing README.md |
| F8.5 | Documentation | Low | newsassistant/README.md | Incomplete model table |
| F10.2 | Standard | Medium | Multiple | `_parse_ai_json` should use shared base function |
