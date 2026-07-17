# Project Hardening Audit

**Date:** 2026-07-17
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

### newsassistant

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 1.1 | `__manifest__.py` | -- | Missing `maintainer` key | Add `"maintainer": "Verein sozialinfo.ch"` |
| 1.2 | `__manifest__.py` | -- | Missing `external_dependencies` for `requests`, `beautifulsoup4` | Add `"external_dependencies": {"python": ["requests", "beautifulsoup4"]}` |

### newsassistant_blog

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 1.3 | `__manifest__.py` | -- | No findings | -- |

### newsassistant_email

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 1.4 | `__manifest__.py` | 6-12 | `description` uses multi-line string, should be concise | Replace with single-line string |
| 1.5 | `__manifest__.py` | -- | Missing `images` key | Add `"images": ["static/description/icon.png"]` |

### newsassistant_strategy

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 1.6 | `__manifest__.py` | -- | Missing `sequence` key | Add `"sequence": 99` |

### newsassistant_strategy_digest

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 1.7 | `__manifest__.py` | 5-16 | `description` key is deprecated in Odoo 18 (duplicates README) | Remove `"description"` key |

### newsassistant_strategy_watch

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 1.8 | `README.md` | 3 | README version `18.0.1.0.0` does not match manifest `18.0.1.1.0` | Update README to `18.0.1.1.0` |
| 1.9 | `security/` | -- | Empty `security/` directory shipped | Remove the directory |

### newsassistant_website

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 1.10 | `__manifest__.py` | ~18 | Missing `external_dependencies` for `requests`, `PIL`, `markdown` | Add `"external_dependencies": {"python": ["markdown", "PIL", "requests"]}` |

---

## Category 2 — Python Code Correctness

### newsassistant

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 2.1 | `models/news_source.py` | 460-521 | **DEAD CODE** — 62 lines of duplicated method body after `return` statement | Remove lines 460-521 entirely |
| 2.2 | `tests/test_scraping_pipeline.py` | 9 | Import from non-existent module (`newsassistant_website` not guaranteed installed) | Guard import with try/except or move test |

### newsassistant_blog

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 2.3 | `models/news_article.py` | 498 | Lazy import inside method body (`parse_ai_json`) | Move to top-level import |
| 2.4 | `models/` | all | `_description` missing on all `_inherit` models | Add `_description` to each model class |
| 2.5 | `models/news_article.py` | 1059 | File is 1059 lines (refactoring opportunity) | Extract Pixabay and AI methods to separate files |

### newsassistant_email

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 2.6 | `models/news_snapshot_email.py` | 7-12 | Import order violation (third-party before Odoo) | Restructure imports per convention |
| 2.7 | `models/news_snapshot_email.py` | 102 | `message_new` missing `@api.model` decorator | Add `@api.model` |
| 2.8 | `models/news_snapshot_email.py` | 98-100 | Dead code: `_get_alias_model_name` (removed in Odoo 18) | Remove method entirely |
| 2.9 | `models/news_snapshot_email.py` | 201-360 | `_discover_articles_email` is 160 lines (exceeds 100) | Refactor into smaller methods |
| 2.10 | `models/news_snapshot_email.py` | 216-223 | Nested function `add_entry` inside method | Extract to standalone method |
| 2.11 | `models/news_snapshot_email.py` | 447 | `self.source_id` accessed before assignment | Use `self.env["news.source"]` directly |
| 2.12 | `models/news_snapshot_email.py` | 403,418 | Missing `sudo()` on news.source search/create | Use `self.env["news.source"].sudo()` |

### newsassistant_strategy

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 2.13 | `models/strategy_strategy.py` | 421-437 | Missing `@api.depends("is_plural")` on computed fields | Add decorator and import `api` |
| 2.14 | `models/strategy_strategy.py` | 14 | Unused import `html_to_markdown` | Remove line 14 |
| 2.15 | `models/strategy_strategy.py` | 394 | Unnecessary `_order = "id"` on transient model | Remove `_order` |

### newsassistant_strategy_digest

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 2.16 | `models/news_article.py` | 17-18 | Dead code: `AI_TIMEOUT`, `TRANSIENT_HTTP_CODES` never used | Remove lines 17-18 |
| 2.17 | `models/strategy_digest.py` | 18-19 | Dead code: `AI_TIMEOUT`, `TRANSIENT_HTTP_CODES` never used | Remove lines 18-19 |

### newsassistant_strategy_watch

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 2.18 | `models/news_article.py` | 11-12 | Dead code: `AI_TIMEOUT`, `TRANSIENT_HTTP_CODES` never used | Remove lines 11-12 |
| 2.19 | `models/news_article.py` | 151 | `json.JSONDecodeError` used without `import json` — will crash at runtime | Add `import json` |

### newsassistant_website

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 2.20 | `models/news_source_website.py` | 2-6 | Import block ordering: `logging` separated from other stdlib imports | Group all stdlib imports together |

---

## Category 3 — Security

### newsassistant

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 3.1 | `security/` | -- | No record rules defined | Add record rules for row-level isolation |
| 3.2 | `tests/` | -- | No `test_security.py` | Add security test file |

### newsassistant_blog

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 3.3 | `models/res_config_settings.py` | 22-26 | `newsfeed_pixabay_api_key` has no `groups=` restriction | Add `groups="newsassistant.newsassistant_group_admin"` |
| 3.4 | `models/news_article.py` | 871-877 | `json.dumps` instead of `json_scriptsafe.dumps` | Use `json_scriptsafe.dumps` |
| 3.5 | `security/` | -- | Empty `security/` directory | Remove empty directory |

### newsassistant_email

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 3.6 | `security/` | -- | **CRITICAL**: No `ir.model.access.csv` at all | Create security files with ACL entries |
| 3.7 | `data/mail_alias_data.xml` | 3-6 | Mail alias has no `alias_contact` restriction (defaults to "everyone") | Add `alias_contact="followers"` |

### newsassistant_strategy

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 3.8 | `security/ir.model.access.csv` | -- | No record rules on `strategy.strategy` | Add record rules |
| 3.9 | `security/ir.model.access.csv` | -- | No `noupdate` wrapper (CSV standard) | Ensure noupdate on groups |

### newsassistant_strategy_digest

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 3.10 | `models/news_article.py` | 47-51 | `strategy_reasoning` has no `groups=` restriction | Add `groups="newsassistant.newsassistant_group_admin"` |

### newsassistant_strategy_watch

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 3.11 | `models/news_article.py` | 38 | `strategy_watch_reasoning` has no `groups=` restriction | Add `groups="newsassistant.newsassistant_group_admin"` |

### newsassistant_website

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 3.12 | `security/` | -- | Empty `security/` directory | Remove the directory |

---

## Category 4 — XML / View Quality

### newsassistant

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 4.1 | All views | -- | No findings | -- |

### newsassistant_blog

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 4.2 | `views/res_config_settings_views.xml` | 16,33,37,47,58,96 | Inline CSS styles used | Replace with Odoo CSS classes |

### newsassistant_email

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 4.3 | `views/news_snapshot_views.xml` | 9 | View name does not follow convention | Rename to `news.snapshot.view.form.email.inherit` |

### newsassistant_strategy

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 4.4 | All views | -- | No findings | -- |

### newsassistant_strategy_digest

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 4.5 | All views | -- | No findings | -- |

### newsassistant_strategy_watch

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 4.6 | `demo/strategy_watch_demo.xml` | 2 | Missing `noupdate="1"` on demo data root tag | Change `<odoo>` to `<odoo noupdate="1">` |

### newsassistant_website

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 4.7 | All views | -- | No findings | -- |

---

## Category 5 — Performance

### newsassistant

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 5.1 | All models | -- | No findings (index=True on all relevant fields, batch compute used) | -- |

### newsassistant_blog

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 5.2 | All models | -- | No findings | -- |

### newsassistant_email

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 5.3 | `data/` | -- | `queue_job` channel `root.email_extraction` not defined in data files | Create `data/queue_job_email_data.xml` |
| 5.4 | `models/news_snapshot_email.py` | 378-390 | N+1 log entry creation in loop | Batch-create log entries |

### newsassistant_strategy

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 5.5 | `models/strategy_strategy.py` | 149-159 | `state` field missing `index=True` | Add `index=True` |
| 5.6 | `models/strategy_strategy.py` | 160-167 | `date_from`/`date_to` missing `index=True` | Add `index=True` |

### newsassistant_strategy_digest

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 5.7 | All models | -- | No findings | -- |

### newsassistant_strategy_watch

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 5.8 | All models | -- | No findings | -- |

### newsassistant_website

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 5.9 | All models | -- | No findings | -- |

---

## Category 6 — Structural Completeness

### newsassistant

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 6.1 | -- | -- | icon.png and migration scripts present, demo data exists | No findings |

### newsassistant_blog

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 6.2 | -- | -- | icon.png present, demo data exists | No findings |

### newsassistant_email

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 6.3 | `data/` | -- | `queue_job` channel `root.email_extraction` not defined in data files | Create `data/queue_job_email_data.xml` |
| 6.4 | `models/res_config_settings.py` | 14-22 | `set_values` does not create alias if it doesn't exist | Add creation logic |

### newsassistant_strategy

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 6.5 | `migrations/` | -- | No migration scripts for version 18.0.1.2.0 | Add pre/end migration scripts |

### newsassistant_strategy_digest

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 6.6 | -- | -- | Migration directory exists, icon.png present | No findings |

### newsassistant_strategy_watch

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 6.7 | `demo/strategy_watch_demo.xml` | 2 | Missing `noupdate="1"` on demo data | Add `noupdate="1"` |
| 6.8 | `migrations/` | -- | No migration scripts for version 18.0.1.1.0 | Add migration script |

### newsassistant_website

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 6.9 | `migrations/` | -- | No migration scripts for version 18.0.2.1.0 | Add migration scripts for future changes |

---

## Category 7 — Maintainability

### newsassistant

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 7.1 | `models/news_source.py` | 460-521 | Dead code (duplicated after return) | Remove |
| 7.2 | `models/news_log_entry.py` | 73-91 | `@api.autovacuum` returns string instead of None | Return None or integer count |

### newsassistant_blog

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 7.3 | `models/news_article.py` | 546-554 | Nested `add_entry` function in `_digest_article` | Extract to helper method |
| 7.4 | `models/news_article.py` | 100-171 | DRY violation: 3 identical config getter methods | Create single generic helper |
| 7.5 | `models/news_article.py` | 594 | `digest_state` set to `processed` before handlers complete | Move write after success |

### newsassistant_email

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 7.6 | `models/news_snapshot_email.py` | 362-392 | `_create_discovery_log` duplicates base module's `_create_snapshot_log` | Refactor to accept category param |
| 7.7 | `models/news_snapshot_email.py` | 169 | Bare `except Exception` in `message_new` | Narrow exception handling |

### newsassistant_strategy

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 7.8 | `models/strategy_strategy.py` | 187 | Misleading docstring on `action_activate` | Fix to match actual behavior |
| 7.9 | `models/strategy_strategy.py` | 439 | Missing docstring on `action_confirm_distill` | Add docstring |

### newsassistant_strategy_digest

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 7.10 | `models/strategy_digest.py` | 248-249 | Duplicate regex for stripping thinking blocks (should use `_parse_ai_json`) | Add comment or refactor |

### newsassistant_strategy_watch

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 7.11 | `models/strategy_strategy.py` | 41 | `action_distill_watch_prompt` missing docstring | Add docstring |
| 7.12 | `models/news_article.py` | 181 | Missing comment explaining why `_evaluate_strategies` is called | Add explanatory comment |

### newsassistant_website

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 7.13 | `models/news_source_website.py` | 266-396 | `_discover_articles_website()` is 130 lines (exceeds 100) | Extract sub-methods |
| 7.14 | `models/news_source_website.py` | 73-104,398-428 | Duplicate log-creation code | Extract shared utility function |

---

## Category 8 — Documentation

### newsassistant

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 8.1 | `README.md` | -- | README present and comprehensive | No findings |

### newsassistant_blog

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 8.2 | `models/news_article.py` | 1025 | `_create_digest_log` docstring missing parameter docs | Expand docstring |

### newsassistant_email

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 8.3 | `README.md` | 113 | Missing configuration explanation for `INFOMANIAK_AI_API_KEY` | Add explanation |
| 8.4 | `models/news_snapshot_email.py` | 362 | Minimal docstring on `_create_discovery_log` | Expand with Args/Returns |

### newsassistant_strategy

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 8.5 | `README.md` | 3 | README version `18.0.1.0.0` does not match manifest `18.0.1.2.0` | Update version |
| 8.6 | `README.md` | -- | Missing "Usage" section | Add usage section |
| 8.7 | `README.md` | 27 | Documents `prompt` field that does not exist in base module | Clarify it's added by sister modules |

### newsassistant_strategy_digest

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 8.8 | `README.md` | -- | README present and comprehensive | No findings |

### newsassistant_strategy_watch

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 8.9 | `README.md` | 3 | README version mismatch with manifest | Update to match |

### newsassistant_website

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 8.10 | `README.md` | 19 | Mentions PDF support via pdfminer but no PDF code exists | Remove misleading reference |

---

## Category 9 — Tooling Compliance

### newsassistant

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 9.1 | -- | -- | No `.pot`, `en.po`, encoding pragmas, or `.rej` files | No findings |

### newsassistant_blog

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 9.2 | `models/__pycache__/` | -- | `__pycache__` directory present (should not be committed) | Add to `.gitignore` and remove |

### newsassistant_email

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 9.3 | -- | -- | No `.pot`, `en.po`, encoding pragmas, or `.rej` files | No findings |

### newsassistant_strategy

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 9.4 | -- | -- | No issues | No findings |

### newsassistant_strategy_digest

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 9.5 | `__pycache__/` | -- | `__pycache__` directories present | Add to `.gitignore` |

### newsassistant_strategy_watch

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 9.6 | `i18n/fr.po`, `i18n/de.po` | multiple | Stale/incorrect translation entries referencing non-existent records | Regenerate PO files |

### newsassistant_website

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 9.7 | -- | -- | No `.pot`, `en.po`, encoding pragmas, or `.rej` files | No findings |

---

## Category 10 — Standard Pattern Compliance

### newsassistant

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 10.1 | `models/news_log.py` | -- | Custom log model instead of `mail.thread` — justified (LLM metadata) | No fix needed |

### newsassistant_blog

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 10.2 | `models/news_article.py` | 864-877 | `_set_blog_cover_properties` reimplements `website.cover_properties.mixin` | Use standard mixin approach |
| 10.3 | `models/news_article.py` | 506 | `_cron_digest_all_impl` missing `@api.model` | Add `@api.model` decorator |

### newsassistant_email

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 10.4 | `models/news_snapshot_email.py` | 89 | Wrong mixin: `mail.alias.mixin` instead of `mail.alias.mixin.optional` | Change to optional variant |
| 10.5 | `models/news_snapshot_email.py` | 92-96 | `_alias_get_creation_values` redundant if mixin changed | Remove if switching to optional |

### newsassistant_strategy

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 10.6 | `models/strategy_strategy.py` | 134-138 | No `mail.thread` inheritance on model with state lifecycle | Add `mail.thread` + `tracking=True` |

### newsassistant_strategy_digest

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 10.7 | `models/news_article.py` | 53-61 | Delegate pattern inconsistent with `strategy.digest` (which inherits mixin) | Add comment explaining delegation |

### newsassistant_strategy_watch

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 10.8 | `models/news_article.py` | 11-12 | Dead constants duplicated from base module | Remove (same as 2.18) |

### newsassistant_website

| # | File | Line | Finding | Fix |
|---|------|------|---------|-----|
| 10.9 | All models | -- | No reimplementation of standard mixins | No findings |

---

## Summary

| Category | Findings | Tasks Generated |
|---|---|---|
| 1 — Manifest Integrity | 10 | 10 |
| 2 — Python Code Correctness | 20 | 20 |
| 3 — Security | 12 | 12 |
| 4 — XML / View Quality | 4 | 4 |
| 5 — Performance | 6 | 6 |
| 6 — Structural Completeness | 7 | 7 |
| 7 — Maintainability | 14 | 14 |
| 8 — Documentation | 10 | 10 |
| 9 — Tooling Compliance | 4 | 4 |
| 10 — Standard Pattern Compliance | 8 | 8 |
| **Total** | **95** | **95** |
