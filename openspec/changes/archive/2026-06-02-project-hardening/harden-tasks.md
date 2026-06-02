# Hardening Tasks

**Change:** project-hardening
**Based on audit:** audit.md
**Zero tolerance:** every task must be completed before the infrastructure section.

---

## Module: newsassistant

### Category 1 — Manifest Integrity
- [x] T1.1: Move `"data/server_actions.xml"` in `__manifest__.py` data list to after `"data/queue_job_data.xml"` (before views block)
- [x] T1.2: Delete dead `data/ir_cron_data.xml` (references method in newsassistant_website, website module has its own cron)

### Category 2 — Python Code Correctness
- [ ] T2.1: Remove duplicate `import time` at line 372 in `models/news_source.py`
- [x] T2.2: Refactor direct SQL in `_compute_is_scraping` and `_compute_job_count` in `models/news_source.py` to use ORM; add comment about OCA internals dependency if ORM insufficient
- [x] T2.3: Refactor direct SQL in `_compute_job_count` and `action_view_jobs` in `models/news_article.py` to use ORM
- [x] T2.4: Replace direct SQL on `news_article_news_log_rel` in `models/news_log.py:_compute_created_article_count` with ORM
- [x] T2.5: Replace N+1 `_compute_article_count` in `models/news_snapshot.py` with `read_group` pattern
- [x] T2.6: Change `UserError` to `ValidationError` for missing AI API key in `models/news_source.py`
- [x] T2.7: Narrow `except (ValueError, Exception)` in `models/news_snapshot.py` to `except Exception as e:`

### Category 3 — Security
- [x] T3.1: Restrict `news.source` ACL for user group to read+write only (`1,1,0,0`); keep full CRUD for admin via separate row
- [x] T3.2: Restrict `news.article` ACL for user group to read+write only (`1,1,0,0`)
- [x] T3.3: Restrict `news.article.stage` ACL for user group to read only (`1,0,0,0`)
- [x] T3.4: Add ACL row for `news.snapshot` granting admin group read access (`1,0,0,0`)
- [x] T3.5: Wrap server actions in `data/server_actions.xml` with `noupdate="1"`

### Category 4 — XML / View Quality
- [x] T4.1: Move `button_box` from `<sheet>` to `<header>` in `views/news_source_views.xml`
- [x] T4.2: Move `button_box` from `<sheet>` to `<header>` in `views/news_article_views.xml`
- [x] T4.3: Move `button_box` from `<sheet>` to `<header>` in `views/news_log_views.xml`

### Category 7 — Maintainability
- [x] T7.1: Add docstrings to `action_view_logs`, `action_view_snapshots`, `action_view_jobs` in `models/news_source.py`
- [x] T7.2: Add docstrings to `_compute_snapshot_count`, `_compute_job_count`, `action_view_snapshot`, `action_view_jobs` in `models/news_article.py`
- [x] T7.3: Add class docstring to `models/news_article_stage.py`
- [x] T7.4: Add docstrings to `_compute_created_article_count`, `action_view_created_articles` in `models/news_log.py`

### Category 8 — Documentation
- [x] T8.1: Fix `README.md` testing section — replace `make test-module` with actual `docker exec` commands

### Category 9 — Tooling Compliance
- [x] T9.1: Remove `__pycache__/` dirs from git tracking, add to `.gitignore`
- [x] T9.2: Remove stub `tests/test_header_image.py` (dead test)

### Category 10 — Standard Pattern Compliance
- [x] T10.1: Extract `_call_infomaniak_ai` from model into `models/ai_service.py` as standalone class/function (improves testability)

---

## Module: newsassistant_blog

### Category 2 — Python Code Correctness
- [ ] T2b.1: Fix `"teaser": False` to `"teaser": ""` at lines 342, 380 in `models/news_article.py`
- [ ] T2b.2: Unify `_call_ai` with core `_call_infomaniak_ai` (add `temperature` parameter to core); remove duplicate in blog module
- [ ] T2b.3: Replace `_parse_ai_json` with import of `parse_ai_json` from `odoo.addons.newsassistant.models.news_source` (with `expect_array=False`)
- [ ] T2b.4: Extract duplicated content-cleaning block into `_clean_article_content(max_chars=None)` helper
- [ ] T2b.5: Split `_call_ai` into `_build_ai_payload()` and `_parse_ai_response()` helpers (resolved if T2b.2 done)

### Category 3 — Security
- [ ] T3b.1: Remove empty `security/ir.model.access.csv` from `__manifest__.py` `data[]` (no new models, all ACLs inherited)

### Category 4 — XML / View Quality
- [ ] T4b.1: Remove empty `views/menu.xml` from `__manifest__.py` `data[]`

### Category 5 — Performance
- [ ] T5b.1: Batch log entry creation in `_create_digest_log` — accumulate dicts and use single bulk `LogEntry.create()`

### Category 7 — Maintainability
- [x] T7b.1: Move `trap_jobs` and `UserError` imports to module level in `tests/test_digest_pipeline.py`
- [x] T7b.2: Move `time`, `fields`, `patch` imports to module level in `tests/test_pipeline_stages.py`
- [ ] T7b.3: Add docstring to inner `add_entry` function in `models/news_article.py:_digest_article`

### Category 8 — Documentation
- [ ] T8b.1: Fix `README.md` line 127 — Pixabay key is Settings UI only, not env var

---

## Module: newsassistant_email

### Category 1 — Manifest Integrity
- [ ] T1e.1: Remove redundant empty `alias_defaults` field from `data/mail_alias_data.xml`

### Category 2 — Python Code Correctness
- [ ] T2e.1: Refactor `_ai_get_source_name()` `.new()` anti-pattern to standalone helper taking `env` parameter
- [x] T2e.2: Narrow `except Exception` in `_ai_get_source_name()` and add `RetryableJobError` re-raise

### Category 3 — Security
- [x] T3e.1: Remove empty `security/ir.model.access.csv` from `data[]`

### Category 6 — Structural Completeness
- [x] T6e.1: Remove outer `<data>` wrapper from `demo/email_source_demo.xml` (legacy pattern, not needed in Odoo 18)

### Category 7 — Maintainability
- [ ] T7e.1: Handle empty alias_name in `res_config_settings.set_values()` — disable alias or keep old name with warning
- [ ] T7e.2: Add `@patch.object` mock for `_ai_get_source_name` in `tests/test_email_inbound.py:test_snapshot_creation_enqueues_extraction`

### Category 8 — Documentation
- [ ] T8e.1: Fix `README.md` Line 32 — `_extract_articles_email()` → `_extract_articles()`
- [ ] T8e.2: Fix `README.md` references to `make sendmail` and `make test-module` — use actual docker commands

---

## Module: newsassistant_strategy

### Category 2 — Python Code Correctness
- [ ] T2s.1: Remove unused `fields` import from `models/news_article.py`
- [ ] T2s.2: Add `_order = "id"` to `strategy.distill.confirm` transient model

### Category 3 — Security
- [x] T3s.1: Add `tests/test_security.py` for `strategy.strategy` and `strategy.distill.confirm` models

### Category 5 — Performance
- [x] T5s.1: Add `index=True` to `strategy.strategy.name` field

### Category 7 — Maintainability
- [x] T7s.1: Add docstring to `_compute_confirm_text` method
- [x] T7s.2: Add docstring to `action_confirm_distill` method

### Category 8 — Documentation
- [x] T8s.1: Create `README.md` with required sections

### Category 9 — Tooling Compliance
- [x] T9s.1: Fix `i18n/de.po` header — module name from `newsassistant_strategy_digest` to `newsassistant_strategy`
- [x] T9s.2: Fix `i18n/fr.po` header — module name from `newsassistant_strategy_digest` to `newsassistant_strategy`
- [x] T9s.3: Regenerate proper PO files with translations specific to `newsassistant_strategy` module (currently copies of digest translations)

### Category 10 — Standard Pattern Compliance
- [ ] T10s.1: Create `StrategyAiMixin` abstract model in `newsassistant_strategy` with shared `_call_ai()` and `_parse_ai_json()` — then remove duplicates from all 4 downstream models

---

## Module: newsassistant_strategy_digest

### Category 2 — Python Code Correctness
- [ ] T2d.1: Remove unused `html_to_markdown` import from `models/strategy_strategy.py`

### Category 3 — Security
- [x] T3d.1: Add `tests/test_security.py` for `strategy.label` and `strategy.digest` models

### Category 9 — Tooling Compliance
- [x] T9d.1: Remove `__pycache__/` dirs from git tracking, remove stale `.pyc` file without corresponding `.py` source

---

## Module: newsassistant_strategy_watch

### Category 1 — Manifest Integrity
- [x] T1w.1: Remove redundant `security/ir.model.access.csv` (and its reference)

### Category 3 — Security
- [x] T3w.1: Add `tests/test_security.py` for extended `news.article` fields / `strategy_strategy` model

### Category 6 — Structural Completeness
- [x] T6w.1: Create `demo/strategy_watch_demo.xml` with sample strategy and article records

### Category 8 — Documentation
- [x] T8w.1: Create `README.md` with required sections

### Category 9 — Tooling Compliance
- [x] T9w.1: Create `i18n/de.po` and `i18n/fr.po` with translations for all translatable strings

---

## Module: newsassistant_website

### Category 1 — Manifest Integrity
- [ ] T1web.1: Change `category` from `"Productivity"` to `"Marketing"`
- [x] T1web.2: Normalize `data/queue_job_data.xml` to use `<odoo><data noupdate="1">...</data></odoo>` pattern

### Category 2 — Python Code Correctness
- [ ] T2web.1: Add `@api.model` decorator to `_cron_scrape_all()`
- [x] T2web.2: Remove unused `created_snapshot_ids` parameter from `_create_listing_log`
- [x] T2web.3: Move token usage logging in `_scrape_listing` to after successful JSON parse

### Category 3 — Security
- [x] T3web.1: Remove empty `security/ir.model.access.csv` from `data[]`

### Category 4 — XML / View Quality
- [x] T4web.1: Remove trailing blank line in `data/queue_job_data.xml`

### Category 5 — Performance
- [ ] T5web.1: Batch dedup check in `_scrape_listing` — collect all URLs, single `.search([("url", "in", all_urls)])`, build O(1) lookup set

### Category 6 — Structural Completeness
- [ ] T6web.1: Remove empty `demo/news_snapshot_demo.xml` from `demo[]` list (or populate with actual data)

### Category 7 — Maintainability
- [ ] T7web.1: Break `_scrape_listing` (214 lines) into smaller methods: `_discover_listing_urls(content)` and `_enqueue_article_snapshots(articles_data)`
- [x] T7web.2: Add docstring to `_create_listing_log`

---

## Mandatory Infrastructure (always last, regardless of audit findings)

### Version Bump
- [ ] Increment patch version in __manifest__.py for every modified module (minor bump if new fields/models added)

### Fresh Instance
- [ ] Rebuild fresh instance with demo data: `make rebuild-demo`

### Module Installation
- [ ] Verify all modules install without errors (`docker compose logs --tail 100`)

### Tests
- [ ] Run full test suite — all tests must be green: `make test`
- [ ] Run coverage — must be >= 80% across all modules: `make test-coverage`

### Translations
- [ ] Install French: `docker exec odoo-newsassistant odoo -d newsassistant -l fr_FR --i18n-overwrite --stop-after-init -c /etc/odoo/odoo.conf`
- [ ] Install German: `docker exec odoo-newsassistant odoo -d newsassistant -l de_DE --i18n-overwrite --stop-after-init -c /etc/odoo/odoo.conf`
- [ ] Install module translations for all modules

### User Language
- [ ] Switch admin/demo users to German via Odoo shell

### Smoke Test
- [ ] Run smoke test: `make smoke`

### Final Report
- [ ] Report login URL: https://newsassistant.opencode.socialcloud.ch/web/login, admin/admin, German UI