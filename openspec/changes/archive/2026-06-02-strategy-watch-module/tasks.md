## 1. Create `newsassistant_strategy` Base Module

- [x] 1.1 Create module directory structure (`__init__.py`, `__manifest__.py`, `models/`, `views/`, `security/`, `data/`, `demo/`, `tests/`, `i18n/`, `static/description/`)
- [x] 1.2 Create `__manifest__.py` with depends on `newsassistant` + `queue_job`, version `18.0.1.0.0`
- [x] 1.3 Move `strategy.strategy` model from `newsassistant_strategy_digest/models/strategy_strategy.py` to base (without `prompt` field — only shared fields: name, state, dates, description, document_ids, label_ids, plus `_call_ai`, `_parse_ai_json`, `_extract_pdf_text`, `_is_active_for_period`, `_distill_gather_content`, `_distill_call_ai`, `_distill_save_labels_prompt`, distill confirm wizard)
- [x] 1.4 Move `strategy.label` model from `newsassistant_strategy_digest/models/strategy_label.py` to base (name, color, unique constraint)
- [x] 1.5 Create base `strategy_strategy_views.xml`: form with statusbar, date/description/documents notebook pages, empty "Prompt" tab shell with instructional banner, list view, search view, distill confirm wizard view
- [x] 1.6 Create base `strategy_label_views.xml`: list and form views for labels
- [x] 1.7 Create `menu.xml`: "Strategy" root under News Assistant, "Strategies" submenu, "Strategy Labels" submenu under Strategy
- [x] 1.8 Create `security/ir.model.access.csv` with user/admin ACLs for strategy.strategy, strategy.label, strategy.distill.confirm
- [x] 1.9 Move `demo/strategy_strategy_demo.xml` and `demo/strategy_label_demo.xml` from digest module
- [x] 1.10 Move `i18n/de.po` and `i18n/fr.po` files from digest module (update module references)
- [x] 1.11 Move strategy-related tests from digest module to base: `test_strategy_label.py`, `test_strategy_strategy.py`
- [x] 1.12 Add `newsassistant_strategy` to `depends` in `newsassistant_strategy_digest/__manifest__.py`

## 2. Refactor `newsassistant_strategy_digest` to Inherit from Base

- [x] 2.1 Remove `strategy.strategy` model `_name` definition from digest — replace with `_inherit = "strategy.strategy"`, rename `prompt` field to `digest_prompt`
- [x] 2.2 Remove `strategy.label` model from digest — already in base
- [x] 2.3 Remove duplicate `_call_ai`, `_parse_ai_json`, `_extract_pdf_text`, `_is_active_for_period`, `_distill_gather_content`, `_distill_call_ai`, `_distill_save_labels_prompt`, distill confirm wizard, `_do_distill_prompt` from digest module's strategy file
- [x] 2.4 Add `action_distill_digest_prompt()` and `_distill_digest_prompt()` to digest module's strategy extension (own distillation logic, own `_DISTILL_SYSTEM_PROMPT`)
- [x] 2.5 Update digest `strategy_strategy_views.xml`: remove full form/list/search views, replace with inherit view that injects "Digest Prompt" section into Prompt tab
- [x] 2.6 Update digest `menu.xml`: change "Strategy Digest" root to "Digest" submenu under `newsassistant_strategy.menu_strategy_root`
- [x] 2.7 Update digest `security/ir.model.access.csv` — remove strategy.strategy and strategy.label entries (now in base)
- [x] 2.8 Remove digest `views/strategy_label_views.xml` — now in base
- [x] 2.9 Update digest `news_article.py`: change `strategy.prompt` references to `strategy.digest_prompt`, update `_evaluate_strategy_labels()` to override base no-op
- [x] 2.10 Update digest `news_article_views.xml`: remove standalone Strategy tab (keep Strategy tab content but ensure it xpath-extends correctly), update strategy strategy form extension
- [x] 2.11 Update digest demo files — remove strategy_strategy and strategy_label demo (now in base)
- [x] 2.12 Remove digest files for strategy_label model and strategy_strategy tests (moved to base)
- [x] 2.13 Add base's `_evaluate_strategies()` dispatch method with no-op `_evaluate_strategy_labels()` that digest overrides

## 3. Create `newsassistant_strategy_watch` Module

- [x] 3.1 Create module directory structure
- [x] 3.2 Create `__manifest__.py` (version `18.0.1.0.0`, depends on `newsassistant_strategy`, `newsassistant`)
- [x] 3.3 Create `models/strategy_strategy.py`: inherit `strategy.strategy`, add `watch_prompt` Html field, add `_DISTILL_WATCH_SYSTEM_PROMPT` constant, add `action_distill_watch_prompt()`, `_distill_watch_prompt()`, `_do_distill_watch_prompt()` with own `_call_ai` and `_parse_ai_json`
- [x] 3.4 Create `models/news_article.py`: inherit `news.article`, add `strategy_watch` Boolean (default False), `strategy_watch_state` Selection (pending/processed), `strategy_watch_reasoning` Text, `_evaluate_strategy_watch()` (override base no-op), `action_reevaluate_strategy_watch()`
- [x] 3.5 Create `views/strategy_strategy_views.xml`: inherit base form to inject "Watch Prompt" section with field + Distill button into Prompt tab
- [x] 3.6 Create `views/news_article_views.xml`: extend kanban to add `boolean_favorite` star (top-right corner), extend search with watch filters, extend form with "Watch" tab
- [x] 3.7 Create `views/menu.xml`: "Watch" submenu under `newsassistant_strategy.menu_strategy_root`
- [x] 3.8 Create `security/ir.model.access.csv` (no new models to expose, but file required)
- [x] 3.9 Create `tests/test_strategy_watch.py`: test watch distillation, article evaluation, kanban star display, manual re-evaluation, cron dispatch

## 4. Cleanup and Integration

- [x] 4.1 Update `newsassistant_strategy_digest/__manifest__.py` version to `18.0.3.0.0`
- [x] 4.2 Remove empty/unused files from digest module
- [x] 4.3 Update models/__init__.py in all three modules
- [x] 4.4 Verify all module `__manifest__.py` data file lists are correct
- [x] 4.5 Run existing tests to verify no regressions
- [x] 4.6 Upgrade all modules and smoke test