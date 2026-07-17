# Hardening Tasks

**Change:** project-hardening
**Based on audit:** audit.md
**Zero tolerance:** every task must be completed before the infrastructure section.

---

## Module: newsassistant

### Category 1 — Manifest Integrity
- [ ] Add `"maintainer": "Verein sozialinfo.ch"` to `__manifest__.py`
- [ ] Add `"external_dependencies": {"python": ["requests", "beautifulsoup4"]}` to `__manifest__.py`

### Category 2 — Python Code Correctness
- [ ] Remove dead code in `models/news_source.py` lines 460-521 (duplicated method body after return)
- [ ] Guard import in `tests/test_scraping_pipeline.py:9` with try/except or move the test that depends on `newsassistant_website`

### Category 3 — Security
- [ ] Add record rules for row-level isolation on user-owned data in `security/`
- [ ] Add `tests/test_security.py` with tests for group hierarchy, per-role CRUD, and AccessError enforcement

### Category 4 — XML / View Quality
- [ ] No findings

### Category 5 — Performance
- [ ] No findings

### Category 6 — Structural Completeness
- [ ] No findings

### Category 7 — Maintainability
- [ ] Remove dead code in `models/news_source.py` lines 460-521 (duplicated after return)
- [ ] Fix `models/news_log_entry.py:73-91` — `@api.autovacuum` returns string, change to return None or integer count

### Category 8 — Documentation
- [ ] No findings

### Category 9 — Tooling Compliance
- [ ] No findings

### Category 10 — Standard Pattern Compliance
- [ ] No findings (custom log model is justified for LLM metadata storage)

---

## Module: newsassistant_blog

### Category 1 — Manifest Integrity
- [ ] No findings

### Category 2 — Python Code Correctness
- [ ] Move lazy import in `models/news_article.py:498` (`parse_ai_json` from inside method body) to top-level import
- [ ] Add `_description` to each `_inherit` model class: `news_article.py`, `blog_post.py`, `news_log.py`, `res_config_settings.py`
- [ ] Extract Pixabay-related methods and AI-related methods from `models/news_article.py` (1059 lines) into separate utility files

### Category 3 — Security
- [ ] Add `groups="newsassistant.newsassistant_group_admin"` to `newsfeed_pixabay_api_key` field in `models/res_config_settings.py:22-26`
- [ ] Replace `json.dumps` with `json_scriptsafe.dumps` in `models/news_article.py:871-877`
- [ ] Remove empty `security/` directory

### Category 4 — XML / View Quality
- [ ] Replace inline CSS styles in `views/res_config_settings_views.xml` (lines 16,33,37,47,58,96) with Odoo CSS classes

### Category 5 — Performance
- [ ] No findings

### Category 6 — Structural Completeness
- [ ] No findings

### Category 7 — Maintainability
- [ ] Extract nested `add_entry` function in `models/news_article.py:546-554` to a helper method
- [ ] Create single generic helper method for config parameter getters (DRY violation in `_get_content_strategy`, `_get_teaser_prompt`, `_get_target_blog` at lines 100-171)
- [ ] Move `digest_state` write in `models/news_article.py:594` to after handlers complete successfully

### Category 8 — Documentation
- [ ] Expand `_create_digest_log` docstring in `models/news_article.py:1025` to document all parameters

### Category 9 — Tooling Compliance
- [ ] Add `__pycache__/` to `.gitignore` and remove `models/__pycache__/` from version control

### Category 10 — Standard Pattern Compliance
- [ ] Refactor `_set_blog_cover_properties` in `models/news_article.py:864-877` to use standard `website.cover_properties.mixin` approach
- [ ] Add `@api.model` decorator to `_cron_digest_all_impl` in `models/news_article.py:506`

---

## Module: newsassistant_email

### Category 1 — Manifest Integrity
- [ ] Replace multi-line `description` in `__manifest__.py:6-12` with concise single-line string
- [ ] Add `"images": ["static/description/icon.png"]` to `__manifest__.py`

### Category 2 — Python Code Correctness
- [ ] Restructure imports in `models/news_snapshot_email.py:7-12` (third-party after stdlib, before Odoo)
- [ ] Add `@api.model` decorator to `message_new` in `models/news_snapshot_email.py:102`
- [ ] Remove dead code `_get_alias_model_name` in `models/news_snapshot_email.py:98-100`
- [ ] Refactor `_discover_articles_email` (160 lines, lines 201-360) into smaller methods
- [ ] Extract nested `add_entry` function (lines 216-223) to standalone method
- [ ] Fix `_ai_get_source_name` (line 447) to use `self.env["news.source"]` instead of `self.source_id`
- [ ] Use `self.env["news.source"].sudo()` for search/create in `_get_or_create_email_source` (lines 403,418)

### Category 3 — Security
- [ ] **CRITICAL**: Create `security/ir.model.access.csv` with ACL entries for all models
- [ ] Add `alias_contact="followers"` to mail alias record in `data/mail_alias_data.xml:3-6`

### Category 4 — XML / View Quality
- [ ] Rename view in `views/news_snapshot_views.xml:9` to follow naming convention

### Category 5 — Performance
- [ ] Create `data/queue_job_email_data.xml` defining `root.email_extraction` queue_job channel
- [ ] Batch-create log entries in `_create_discovery_log` (lines 378-390) instead of individual creates in loop

### Category 6 — Structural Completeness
- [ ] Create `data/queue_job_email_data.xml` defining `root.email_extraction` channel
- [ ] Add creation logic in `models/res_config_settings.py:14-22` for when alias doesn't exist yet

### Category 7 — Maintainability
- [ ] Refactor `_create_discovery_log` (lines 362-392) to accept category parameter instead of duplicating base module's `_create_snapshot_log`
- [ ] Narrow exception handling in `message_new` (line 169) from bare `except Exception` to specific exceptions

### Category 8 — Documentation
- [ ] Add configuration explanation for `INFOMANIAK_AI_API_KEY` in `README.md:113`
- [ ] Expand `_create_discovery_log` docstring with Args/Returns sections

### Category 9 — Tooling Compliance
- [ ] No findings

### Category 10 — Standard Pattern Compliance
- [ ] Change `mail.alias.mixin` to `mail.alias.mixin.optional` in `models/news_snapshot_email.py:89`
- [ ] Remove `_alias_get_creation_values` method (lines 92-96) if switching to optional mixin

---

## Module: newsassistant_strategy

### Category 1 — Manifest Integrity
- [ ] Add `"sequence": 99` to `__manifest__.py`

### Category 2 — Python Code Correctness
- [ ] Add `@api.depends("is_plural")` decorator to `_compute_confirm_text` in `models/strategy_strategy.py:421-437` and add `api` to imports
- [ ] Remove unused import `html_to_markdown` in `models/strategy_strategy.py:14`
- [ ] Remove unnecessary `_order = "id"` from transient model `StrategyDistillConfirm` in `models/strategy_strategy.py:394`

### Category 3 — Security
- [ ] Add record rules for `strategy.strategy` in `security/strategy_record_rules.xml`
- [ ] Ensure `noupdate="1"` on security groups

### Category 4 — XML / View Quality
- [ ] No findings

### Category 5 — Performance
- [ ] Add `index=True` to `state` field in `models/strategy_strategy.py:149-159`
- [ ] Add `index=True` to `date_from` and `date_to` fields in `models/strategy_strategy.py:160-167`

### Category 6 — Structural Completeness
- [ ] Add migration scripts for version 18.0.1.2.0 in `migrations/` directory

### Category 7 — Maintainability
- [ ] Fix misleading docstring on `action_activate` in `models/strategy_strategy.py:187` to match actual behavior
- [ ] Add docstring to `action_confirm_distill` in `models/strategy_strategy.py:439`

### Category 8 — Documentation
- [ ] Update README.md version from `18.0.1.0.0` to `18.0.1.2.0` (line 3)
- [ ] Add "Usage" section to README.md
- [ ] Clarify in README.md:27 that `prompt` field is added by sister modules, not defined in base

### Category 9 — Tooling Compliance
- [ ] No findings

### Category 10 — Standard Pattern Compliance
- [ ] Add `mail.thread` inheritance to `StrategyStrategy` model (line 134-138) and `tracking=True` on `state` field

---

## Module: newsassistant_strategy_digest

### Category 1 — Manifest Integrity
- [ ] Remove deprecated `description` key from `__manifest__.py:5-16` (duplicates README)

### Category 2 — Python Code Correctness
- [ ] Remove dead code (`AI_TIMEOUT`, `TRANSIENT_HTTP_CODES`) in `models/news_article.py:17-18`
- [ ] Remove dead code (`AI_TIMEOUT`, `TRANSIENT_HTTP_CODES`) in `models/strategy_digest.py:18-19`

### Category 3 — Security
- [ ] Add `groups="newsassistant.newsassistant_group_admin"` to `strategy_reasoning` field in `models/news_article.py:47-51`

### Category 4 — XML / View Quality
- [ ] No findings

### Category 5 — Performance
- [ ] No findings

### Category 6 — Structural Completeness
- [ ] No findings

### Category 7 — Maintainability
- [ ] Add comment explaining duplicated regex for stripping thinking blocks in `models/strategy_digest.py:248-249`

### Category 8 — Documentation
- [ ] No findings

### Category 9 — Tooling Compliance
- [ ] Add `__pycache__/` to `.gitignore` and remove cached files

### Category 10 — Standard Pattern Compliance
- [ ] Add comment explaining why `news.article` uses delegation instead of mixin inheritance (lines 53-61)

---

## Module: newsassistant_strategy_watch

### Category 1 — Manifest Integrity
- [ ] Update README.md version from `18.0.1.0.0` to `18.0.1.1.0` (line 3)
- [ ] Remove empty `security/` directory

### Category 2 — Python Code Correctness
- [ ] Remove dead code (`AI_TIMEOUT`, `TRANSIENT_HTTP_CODES`) in `models/news_article.py:11-12`
- [ ] Add `import json` in `models/news_article.py` (line 151 uses `json.JSONDecodeError`)

### Category 3 — Security
- [ ] Add `groups="newsassistant.newsassistant_group_admin"` to `strategy_watch_reasoning` field in `models/news_article.py:38`

### Category 4 — XML / View Quality
- [ ] Add `noupdate="1"` to demo data root tag in `demo/strategy_watch_demo.xml:2`

### Category 5 — Performance
- [ ] No findings

### Category 6 — Structural Completeness
- [ ] Add `noupdate="1"` to demo data in `demo/strategy_watch_demo.xml:2`
- [ ] Add migration script for version 18.0.1.1.0

### Category 7 — Maintainability
- [ ] Add docstring to `action_distill_watch_prompt` in `models/strategy_strategy.py:41`
- [ ] Add explanatory comment in `models/news_article.py:181` on why `_evaluate_strategies` is called

### Category 8 — Documentation
- [ ] Update README.md version from `18.0.1.0.0` to `18.0.1.1.0` (line 3)

### Category 9 — Tooling Compliance
- [ ] Regenerate PO files (`i18n/fr.po`, `i18n/de.po`) to remove stale translation entries referencing non-existent records

### Category 10 — Standard Pattern Compliance
- [ ] Remove dead constants `AI_TIMEOUT`, `TRANSIENT_HTTP_CODES` from `models/news_article.py:11-12` (duplicated from base)

---

## Module: newsassistant_website

### Category 1 — Manifest Integrity
- [ ] Add `"external_dependencies": {"python": ["markdown", "PIL", "requests"]}` to `__manifest__.py`

### Category 2 — Python Code Correctness
- [ ] Group all stdlib imports together in `models/news_source_website.py:2-6`

### Category 3 — Security
- [ ] Remove empty `security/` directory

### Category 4 — XML / View Quality
- [ ] No findings

### Category 5 — Performance
- [ ] No findings

### Category 6 — Structural Completeness
- [ ] No findings

### Category 7 — Maintainability
- [ ] Extract sub-methods from `_discover_articles_website()` (130 lines, lines 266-396): `_call_discovery_ai`, `_parse_discovery_response`, `_enqueue_article_fetches`
- [ ] Extract shared utility function for duplicate log-creation code (`_create_listing_log` and `_create_discovery_log`)

### Category 8 — Documentation
- [ ] Remove misleading PDF support reference from `README.md:19` (no PDF code exists in module)

### Category 9 — Tooling Compliance
- [ ] No findings

### Category 10 — Standard Pattern Compliance
- [ ] No findings

---

## Mandatory Infrastructure (always last, regardless of audit findings)

### Version Bump
- [ ] Increment patch version in `__manifest__.py` for every modified module (minor bump if new fields/models were added during hardening)

### Pre-commit (if .pre-commit-config.yaml exists)
- [ ] Run pre-commit on all files and fix every failure: `pre-commit run --all-files`

### Fresh Instance
- [ ] Rebuild fresh instance with demo data: `make rebuild-demo` (or manual docker run if no Makefile)

### Module Installation
- [ ] Verify all modules install without errors
- [ ] Check container logs for any startup warnings or errors: `docker compose logs --tail 100`

### Tests
- [ ] Run full test suite — all tests must be green: `make test` (or docker run equivalent)
- [ ] Run coverage — must be ≥ 80% across all modules: `make test-coverage`. Write additional tests if coverage is below threshold.

### Translations
- [ ] Install French language: `docker exec odoo-newsassistant odoo -d newsassistant -l fr_FR --i18n-overwrite --stop-after-init -c /etc/odoo/odoo.conf`
- [ ] Install German language: `docker exec odoo-newsassistant odoo -d newsassistant -l de_DE --i18n-overwrite --stop-after-init -c /etc/odoo/odoo.conf`
- [ ] Install module translations for all modules: `docker exec odoo-newsassistant odoo -d newsassistant -u newsassistant,newsassistant_blog,newsassistant_email,newsassistant_strategy,newsassistant_strategy_digest,newsassistant_strategy_watch,newsassistant_website -l de_DE,fr_FR --i18n-overwrite --stop-after-init -c /etc/odoo/odoo.conf`

### User Language
- [ ] Switch admin and demo users to German (de_DE) via Odoo shell:
      ```
      docker compose exec -T odoo odoo shell -d newsassistant -c /etc/odoo/odoo.conf --http-port=18069 <<'EOF'
      env['res.users'].search([('login', 'in', ['admin', 'demo'])]).write({'lang': 'de_DE'})
      env.cr.commit()
      EOF
      ```

### Smoke Test
- [ ] Run smoke test: `make smoke` (or two-curl check if no Makefile: login page returns 200, CSS assets return 200)

### Visual Verification
- [ ] Use Playwright to verify UI renders correctly: login, member detail form, image_1920 rendering, kanban avatars, CSS assets (HTTP 200)

### Final Report
- [ ] Report login URL to user: https://newsassistant.opencode.socialcloud.ch/web/login - Credentials: admin / admin - UI language: German (de_DE) - French also installed.
- [ ] List any issues that could NOT be resolved during this hardening run, with concrete proposed next steps for each.