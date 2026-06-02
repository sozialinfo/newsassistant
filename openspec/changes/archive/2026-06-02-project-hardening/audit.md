# Project Hardening Audit

**Date:** 2026-06-02
**Project:** newsassistant
**Odoo Version:** 18.0
**Edition:** CE
**Modules audited:** newsassistant, newsassistant_blog, newsassistant_email, newsassistant_strategy, newsassistant_strategy_digest, newsassistant_strategy_watch, newsassistant_website

---

## How to Read This Audit

Each finding includes:
- **Module** — the addons/ subdirectory
- **File** — relative path within the module
- **Line** — line number (where applicable)
- **Category** — audit category number (1–10)
- **Finding** — what is wrong
- **Fix** — the concrete action required in harden-tasks.md

Zero tolerance: every finding is a task. Nothing is pre-existing.

---

## Category 1 — Manifest Integrity

**Module:** newsassistant
- File: `__manifest__.py`, Line: 29-35, Finding: `data/server_actions.xml` appears after all view files (should be in data block, before views), Fix: Move `"data/server_actions.xml"` to after `"data/queue_job_data.xml"` and before views.

**Module:** newsassistant
- File: `data/ir_cron_data.xml`, Finding: File exists but is NOT listed in `__manifest__.py` `data[]`. It references `model._cron_scrape_all()` which is defined in `newsassistant_website`, not the base module. The website module has its own cron file, Fix: Delete the dead `data/ir_cron_data.xml` from the base module since the website module has its own cron.

**Module:** newsassistant_strategy_watch
- File: `__manifest__.py`, Line: 23, Finding: `security/ir.model.access.csv` exists but is NOT listed in the `data` array, Fix: Remove the redundant ACL file (this module adds no new models — the `news.article` ACL is inherited from `newsassistant`).

**Module:** newsassistant_website
- File: `__manifest__.py`, Line: 3, Finding: `"category": "Productivity"` is a legacy category name, Fix: Change to `"category": "Marketing"`.

**Module:** newsassistant_website
- File: `data/queue_job_data.xml`, Finding: Uses `<odoo noupdate="1">` (no `<data>` wrapper) while `data/ir_cron_data.xml` uses `<odoo><data noupdate="1">` — inconsistent pattern, Fix: Normalize both to use `<odoo><data noupdate="1">...</data></odoo>`.

**Module:** newsassistant_email
- File: `data/mail_alias_data.xml`, Line: 6, Finding: `alias_defaults` set to `{}` (empty JSON) which is Odoo's default — redundant, Fix: Remove the empty `<field name="alias_defaults">` line.

---

## Category 2 — Python Code Correctness

**Module:** newsassistant
- File: `models/news_source.py`, Line: 372, Finding: Duplicate `import time` inside `_call_infomaniak_ai` (already imported at module level line 5), Fix: Remove the duplicate import at line 372.

**Module:** newsassistant
- File: `models/news_source.py`, Line: 217-225, 276-283, Finding: Direct SQL query on `queue_job` table internals (`records#>>'{}')::jsonb->'ids'`) in `_compute_is_scraping` and `_compute_job_count` — fragile dependency on OCA internals, Fix: Use `queue.job` ORM methods (`self.env["queue.job"].search_count(...)`) where possible. Add comment about the OCA internal dependency if ORM is insufficient.

**Module:** newsassistant
- File: `models/news_article.py`, Line: 120-153, Finding: Same direct SQL on `queue_job` internals in `_compute_job_count` and `action_view_jobs`, Fix: Same as above — use ORM methods.

**Module:** newsassistant
- File: `models/news_log.py`, Line: 91-99, Finding: Direct SQL query on `news_article_news_log_rel` M2M join table for `_compute_created_article_count` — should use ORM, Fix: Replace with `read_group` or ORM query using the M2M relationship.

**Module:** newsassistant
- File: `models/news_snapshot.py`, Line: 81-83, Finding: `_compute_article_count` iterates per-snapshot with `len(snapshot.article_ids)` — N+1 query, Fix: Replace with `read_group` pattern.

**Module:** newsassistant
- File: `models/news_source.py`, Line: 341, Finding: `UserError` raised for missing AI API key — should be `ValidationError` (UserError is blocking, ValidationError allows the user to fix config), Fix: Change to `raise ValidationError(...)` from `odoo.exceptions`.

**Module:** newsassistant
- File: `models/news_snapshot.py`, Line: 268, Finding: `except (ValueError, Exception)` — `ValueError` is redundant since `Exception` already catches it. Also bare `Exception` is too broad, Fix: Change to `except Exception as e:` and add specific catch logic or narrower exception types.

**Module:** newsassistant_blog
- File: `models/news_article.py`, Line: 342, 380, Finding: `self.write({"teaser": False})` writes boolean `False` to a `Text` field — results in string `"false"` in DB, not empty, Fix: Change to `"teaser": ""`.

**Module:** newsassistant_blog
- File: `models/news_article.py`, Line: 408-508, Finding: `_call_ai` method duplicates core module's `_call_infomaniak_ai` (~100 lines). Only difference is `temperature` parameter and return dict structure, Fix: Unify with core AI caller — extend `_call_infomaniak_ai` to accept `temperature` parameter or extract shared logic.

**Module:** newsassistant_blog
- File: `models/news_article.py`, Line: 510-525, Finding: `_parse_ai_json` is a stripped-down reimplementation of `parse_ai_json` from core module — missing JSONL, array wrapping, bracket fallback handling, Fix: Import and call `parse_ai_json` from `odoo.addons.newsassistant.models.news_source` with `expect_array=False`.

**Module:** newsassistant_blog
- File: `models/news_article.py`, Line: 659-664, 809-813, Finding: Duplicated 6-line content-cleaning block (strip HTML, decode entities, collapse whitespace) in both `_evaluate_relevance` and `_generate_teaser`, Fix: Extract helper method `_clean_article_content(max_chars=None)`.

**Module:** newsassistant_blog
- File: `models/news_article.py`, Line: 408-508, Finding: `_call_ai` method is 101 lines (exceeds 100-line threshold), Fix: Split into `_build_ai_payload()` and `_parse_ai_response()` helpers (or resolved if deduplication with core is done).

**Module:** newsassistant_email
- File: `models/news_snapshot_email.py`, Line: 221-222, Finding: `_ai_get_source_name()` creates a dummy record via `self.env["news.source"].new({...})` and calls `_call_infomaniak_ai()` on it — fragile anti-pattern if the AI caller ever relies on record-level data, Fix: Refactor to a standalone helper that takes `env` as parameter instead of relying on `.new()` record.

**Module:** newsassistant_email
- File: `models/news_snapshot_email.py`, Line: 229, Finding: `except Exception as e` is too broad in `_ai_get_source_name()` — should not swallow `RetryableJobError`, `KeyboardInterrupt`, etc., Fix: Narrow to `except (requests.RequestException, ValueError) as e:` and add `if isinstance(e, RetryableJobError): raise`.

**Module:** newsassistant_strategy
- File: `models/news_article.py`, Line: 3, Finding: Unused import `fields`, Fix: Remove `fields` from import line.

**Module:** newsassistant_strategy
- File: `models/strategy_strategy.py`, Line: 383, Finding: `strategy.distill.confirm` transient model missing `_order` attribute, Fix: Add `_order = "id"`.

**Module:** newsassistant_strategy_digest
- File: `models/strategy_strategy.py`, Line: 6, Finding: Unused import `html_to_markdown`, Fix: Remove the import line.

**Module:** newsassistant_strategy_digest + newsassistant_strategy_watch
- File: Multiple files, Finding: `_call_ai` method is duplicated 4 times across 3 modules (~73 lines each, ~290 total duplicated lines): `strategy_strategy.py` (base), `strategy_digest/models/strategy_digest.py`, `strategy_digest/models/news_article.py`, `strategy_watch/models/news_article.py`, Fix: Create a `StrategyAiMixin` abstract model in `newsassistant_strategy` with `_call_ai()` and `_parse_ai_json()`. All 4 models inherit the mixin.

**Module:** newsassistant_website
- File: `models/news_source_website.py`, Line: 42, Finding: `_cron_scrape_all()` missing `@api.model` decorator (called from cron as `model._cron_scrape_all()`), Fix: Add `@api.model` decorator.

**Module:** newsassistant_website
- File: `models/news_source_website.py`, Line: 51, Finding: `_create_listing_log` has unused parameter `created_snapshot_ids=None`, Fix: Remove the unused parameter.

**Module:** newsassistant_website
- File: `models/news_source_website.py`, Line: 169, Finding: AI response token usage logging occurs before JSON parse validation — logs potentially malformed data, Fix: Move token usage logging to after successful parse or guard against missing keys.

---

## Category 3 — Security

**Module:** newsassistant
- File: `security/ir.model.access.csv`, Line: 2-3, Finding: `news.source` grants full CRUD (1,1,1,1) to `newsassistant_group_user` — users can create/delete sources, Fix: Restrict to `1,1,0,0` for user group (read+write only). Keep full CRUD for admin group only.

**Module:** newsassistant
- File: `security/ir.model.access.csv`, Line: 5, Finding: `news.article` grants full CRUD (1,1,1,1) to user group — users can delete articles, Fix: Restrict to `1,1,0,0` for user, keep full CRUD for admin.

**Module:** newsassistant
- File: `security/ir.model.access.csv`, Line: 6, Finding: `news.article.stage` grants full CRUD (1,1,1,1) to user group — users can create/delete kanban stages, Fix: Restrict to read+write only `1,1,0,0` for user group.

**Module:** newsassistant
- File: `security/ir.model.access.csv`, Finding: `news_snapshot` has no access row for `newsassistant_group_admin` (only `base.group_system` has full CRUD), Fix: Add row: `access_news_snapshot_admin,news.snapshot.admin,model_news_snapshot,newsassistant.newsassistant_group_admin,1,0,0,0` (admin can read).

**Module:** newsassistant
- File: `data/server_actions.xml`, Finding: Server actions ("Scrape Selected", "Re-extract Selected", "Mark as Skipped", "Reset to Pending") not wrapped in `<data noupdate="1">` — can be overwritten on upgrade, Fix: Wrap entire content in `<data noupdate="1">` block.

**Module:** newsassistant_blog
- File: `security/ir.model.access.csv`, Finding: File contains only header row (zero data rows) — empty security file can confuse future maintainers, Fix: Remove file from `data[]` list (all models extend existing ones, inheriting ACLs from parent modules).

**Module:** newsassistant_email
- File: `security/ir.model.access.csv`, Finding: Empty file (header only) — same as above, Fix: Remove file from `data[]` list.

**Module:** newsassistant_strategy_watch
- File: `security/ir.model.access.csv`, Finding: Contains redundant ACL entries for `news.article` model (already defined in `newsassistant` dependency), Fix: Delete file (module introduces no new models, only extends existing).

**Module:** newsassistant_website
- File: `security/ir.model.access.csv`, Finding: Empty file (header only), Fix: Remove file from `data[]` list.

**Module:** newsassistant_strategy, newsassistant_strategy_digest, newsassistant_strategy_watch
- File: (missing), Finding: No `test_security.py` in any of the three strategy modules, Fix: Add `test_security.py` to `newsassistant_strategy` (cover `strategy.strategy`, `strategy.distill.confirm`) and `newsassistant_strategy_digest` (cover `strategy.label`, `strategy.digest`).

---

## Category 4 — XML / View Quality

**Module:** newsassistant
- File: `views/news_source_views.xml`, Line: 37, Finding: `button_box` div inside `<sheet>` instead of `<header>` — nonstandard form structure, Fix: Move `<div class="oe_button_box" name="button_box">` to `<header>`.

**Module:** newsassistant
- File: `views/news_article_views.xml`, Line: 62, Finding: Same `button_box` in `<sheet>` instead of `<header>`, Fix: Move to `<header>`.

**Module:** newsassistant
- File: `views/news_log_views.xml`, Line: 31, Finding: Same `button_box` in `<sheet>` instead of `<header>`, Fix: Move to `<header>`.

**Module:** newsassistant_blog
- File: `views/menu.xml`, Finding: Contains only XML boilerplate with a comment — effectively empty file loaded as data, Fix: Remove `views/menu.xml` from `__manifest__.py` `data[]`.

**Module:** newsassistant_website
- File: `data/queue_job_data.xml`, Line: 19, Finding: Trailing blank line before `</odoo>`, Fix: Remove blank line.

---

## Category 5 — Performance

**Module:** newsassistant
- File: `models/news_snapshot.py`, Line: 81-83, Finding: N+1 in `_compute_article_count` (also noted in Cat 2), Fix: Use `read_group` pattern.

**Module:** newsassistant_blog
- File: `models/news_article.py`, Line: 1062-1074, Finding: N+1 entry creation in `_create_digest_log` — one `create()` per log entry in a loop, Fix: Accumulate dicts in list and issue single bulk `LogEntry.create()`.

**Module:** newsassistant_website
- File: `models/news_source_website.py`, Line: 268-271, Finding: N+1 dedup check — `search([("url", "=", normalized)], limit=1)` called per URL in a loop, Fix: Batch: collect all normalized URLs, do single `.search([("url", "in", all_urls)])`, build set for O(1) lookup.

**Module:** newsassistant_strategy
- File: `models/strategy_strategy.py`, Line: 39, Finding: `strategy.strategy.name` used in `_order = "name"` but has no `index=True`, Fix: Add `index=True` to the `name` field.

---

## Category 6 — Structural Completeness

**Module:** newsassistant_strategy_watch
- File: (missing), Finding: No `demo/` directory, Fix: Create `demo/strategy_watch_demo.xml` with sample strategy and article records.

**Module:** newsassistant_website
- File: `demo/news_snapshot_demo.xml`, Finding: File is effectively empty — contains only comments, no records, Fix: Either remove from `demo[]` list or add actual demo data.

**Module:** newsassistant_email
- File: `demo/email_source_demo.xml`, Line: 1, Finding: Legacy `<data>` wrapper (not needed in Odoo 18 — `<odoo>` can directly contain `<record>`), Fix: Remove outer `<data>` wrapper tags.

---

## Category 7 — Maintainability

**Module:** newsassistant
- File: `models/news_source.py`, Line: 288-331, Finding: Methods `action_view_logs`, `action_view_snapshots`, `action_view_jobs` lack docstrings, Fix: Add docstrings.

**Module:** newsassistant
- File: `models/news_article.py`, Line: 110-162, Finding: Methods `_compute_snapshot_count`, `_compute_job_count`, `action_view_snapshot`, `action_view_jobs` lack docstrings, Fix: Add docstrings.

**Module:** newsassistant
- File: `models/news_article_stage.py`, Line: 4-11, Finding: Model lacks docstring, Fix: Add class docstring.

**Module:** newsassistant
- File: `models/news_log.py`, Line: 85-114, Finding: Methods `_compute_created_article_count`, `action_view_created_articles` lack docstrings, Fix: Add docstrings.

**Module:** newsassistant_blog
- File: `tests/test_digest_pipeline.py`, Line: 161, 224, Finding: `trap_jobs` and `UserError` imported inside test methods instead of at module level, Fix: Move to module-level imports.

**Module:** newsassistant_blog
- File: `tests/test_pipeline_stages.py`, Line: 118, 119, 134, Finding: `import time`, `from odoo import fields`, `from unittest.mock import patch` imported inside test method, Fix: Move to module-level imports.

**Module:** newsassistant_blog
- File: `models/news_article.py`, Line: 571-578, Finding: Inner function `add_entry` (defined in `_digest_article`) lacks docstring, Fix: Add docstring `"""Append a structured log entry to the log_entries list."""`.

**Module:** newsassistant_email
- File: `models/res_config_settings.py`, Line: 17, Finding: `set_values()` logic gap: if alias_name is emptied/cleared, the `alias.write()` is skipped but `super().set_values()` saves empty string — ghost state, Fix: Handle empty case explicitly (disable alias or keep old name with warning).

**Module:** newsassistant_email
- File: `tests/test_email_inbound.py`, Line: 132-148, Finding: Test `test_snapshot_creation_enqueues_extraction` does not mock `_ai_get_source_name` — risks real AI API call, Fix: Add `@patch.object` decorator or use `_send_email` helper consistently.

**Module:** newsassistant_strategy
- File: `models/strategy_strategy.py`, Line: 410, Finding: `_compute_confirm_text` method has no docstring, Fix: Add docstring.

**Module:** newsassistant_strategy
- File: `models/strategy_strategy.py`, Line: 427, Finding: `action_confirm_distill` has no docstring, Fix: Add docstring.

**Module:** newsassistant_website
- File: `models/news_source_website.py`, Line: 84-297, Finding: `_scrape_listing` is 214 lines (exceeds 100-line threshold), Fix: Extract dedup loop (lines 230-279) into `_enqueue_article_snapshots(articles_data)` and listing AI call into `_discover_listing_urls(content)`.

**Module:** newsassistant_website
- File: `models/news_source_website.py`, Line: 51, Finding: `_create_listing_log` has no docstring, Fix: Add docstring.

---

## Category 8 — Documentation

**Module:** newsassistant
- File: `README.md`, Line: 133, Finding: Testing section uses `make test-module` which doesn't exist in project, Fix: Replace with actual `docker exec odoo-newsassistant odoo --test-tags ...` commands.

**Module:** newsassistant_blog
- File: `README.md`, Line: 127, Finding: Incorrectly documents `PIXABAY_API_KEY` as environment variable (it's only set via Settings UI as `ir.config_parameter`), Fix: Correct to: "Pixabay API Key — set via Settings UI (News Assistant → Configuration → Settings)".

**Module:** newsassistant_email
- File: `README.md`, Line: 32, Finding: Pipeline diagram references nonexistent method `_extract_articles_email()`, Fix: Change to `_extract_articles()`.

**Module:** newsassistant_email
- File: `README.md`, Line: 53, 118, Finding: README references `make sendmail` and `make test-module` which don't exist, Fix: Replace with actual `docker exec` commands.

**Module:** newsassistant_strategy
- File: (missing), Finding: No `README.md` exists, Fix: Create README.md with required sections.

**Module:** newsassistant_strategy_watch
- File: (missing), Finding: No `README.md` exists, Fix: Create README.md with required sections.

---

## Category 9 — Tooling Compliance

**Module:** newsassistant, newsassistant_strategy_digest
- Finding: `__pycache__/` directories committed to version control (`.pyc` files for cpython-312 and cpython-313), Fix: Add `__pycache__/` to `.gitignore` and `git rm -r --cached` all `__pycache__/` dirs.

**Module:** newsassistant
- File: `tests/test_header_image.py`, Finding: Stub file that only tests `ImportError` — dead test code added for "test count parity", Fix: Remove the file (actual tests are in `newsassistant_website`).

**Module:** newsassistant_strategy
- File: `i18n/de.po`, Line: 3, Finding: PO file header declares `newsassistant_strategy_digest` as source module instead of `newsassistant_strategy`, Fix: Correct the module name in header.

**Module:** newsassistant_strategy
- File: `i18n/fr.po`, Line: 3, Finding: Same wrong header — declares `newsassistant_strategy_digest`, Fix: Correct to `newsassistant_strategy`.

**Module:** newsassistant_strategy
- File: `i18n/de.po`, `i18n/fr.po`, Finding: Both PO files are verbatim copies of `newsassistant_strategy_digest` translations — contain ZERO translations for `newsassistant_strategy` module's own strings (views, Python `_()` calls, model names, selection values), Fix: Generate proper POT from `newsassistant_strategy` module, create proper translations for all translatable strings.

**Module:** newsassistant_strategy_watch
- File: (missing), Finding: No `i18n/` directory at all — no de.po or fr.po files, Fix: Create `i18n/de.po` and `i18n/fr.po` with translations for all translatable strings.

---

## Category 10 — Standard Pattern Compliance

**Module:** newsassistant
- File: `models/news_source.py`, Line: 353-449, Finding: `_call_infomaniak_ai` is ~100-line raw HTTP client embedded in a model method — should be extracted to dedicated service class, Fix: Extract into `models/ai_service.py` as a standalone class or module-level function.

**Module:** newsassistant_blog
- File: `models/news_article.py`, Line: 408-525, Finding: `_call_ai` and `_parse_ai_json` are custom reimplementations of the core module's `_call_infomaniak_ai` and `parse_ai_json`, Fix: Reuse core module's implementations (add `temperature` parameter to core AI caller).

**Module:** newsassistant_strategy_digest, newsassistant_strategy_watch
- Finding: `_call_ai` duplicated 4 times across 3 modules (~290 total lines), Fix: Create `StrategyAiMixin` abstract model in `newsassistant_strategy` (also noted in Cat 2).

---

## Summary

| Category | Findings |
|---|---|
| 1 — Manifest Integrity | 6 |
| 2 — Python Code Correctness | 19 |
| 3 — Security | 10 |
| 4 — XML / View Quality | 5 |
| 5 — Performance | 4 |
| 6 — Structural Completeness | 3 |
| 7 — Maintainability | 12 |
| 8 — Documentation | 6 |
| 9 — Tooling Compliance | 6 |
| 10 — Standard Pattern Compliance | 3 |
| **Total** | **74** |