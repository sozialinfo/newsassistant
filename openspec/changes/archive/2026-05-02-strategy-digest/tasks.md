## 1. Module Scaffold

- [x] 1.1 Create `addons/newsassistant_strategy_digest/` directory structure (`models/`, `views/`, `data/`, `demo/`, `security/`, `i18n/`, `tests/`, `report/`, `static/description/`)
- [x] 1.2 Create `__manifest__.py` with correct name, version, depends (`newsassistant`, `queue_job`), data/security/demo/report file lists
- [x] 1.3 Create `__init__.py` and `models/__init__.py`

## 2. Strategy Label Model

- [x] 2.1 Create `models/strategy_label.py` with `strategy.label` model: `name` (Char, required, translate), `color` (Integer, randint default), unique name constraint
- [x] 2.2 Create `views/strategy_label_views.xml` with list view (editable top, name + color_picker), form view, window action
- [x] 2.3 Add security rules in `security/ir.model.access.csv`: read for `base.group_user`, full CRUD for `base.group_system`
- [x] 2.4 Add Configuration menu item "Strategy Labels" under the existing News Assistant Configuration menu

## 3. Strategy Model

- [x] 3.1 Create `models/strategy_strategy.py` with `strategy.strategy` model: `name`, `date_from`, `date_to`, `document_ids` (M2M ir.attachment), `label_ids` (M2M strategy.label), `description` (Text), `prompt` (Text, readonly)
- [x] 3.2 Add `_is_active_for_period(date_from, date_to)` helper on `strategy.strategy` to check date overlap (None dates = eternal)
- [x] 3.3 Add `action_distill_prompt()` method: extract PDF text via pdfminer, concatenate with description + label names, call AI, save to `prompt`
- [x] 3.4 Add `_extract_pdf_text(attachment)` helper using `pdfminer.high_level.extract_text` on BytesIO from attachment.datas
- [x] 3.5 Create `views/strategy_strategy_views.xml` with form view (all fields, Distill Prompt button), list view, search view, window action
- [x] 3.6 Add security rules for `strategy.strategy` in `ir.model.access.csv`
- [x] 3.7 Add demo data: 2 sample strategies with labels in `demo/strategy_strategy_demo.xml`

## 4. Article Inheritance — Labels and Evaluation State

- [x] 4.1 Create `models/news_article.py` with `_inherit = "news.article"`: add `strategy_label_ids` (M2M → strategy.label), `strategy_eval_state` (Selection pending/processed, default pending, readonly, indexed)
- [x] 4.2 Add `action_reevaluate_strategy_labels()` method: reset `strategy_eval_state` to pending, queue `_evaluate_strategy_labels()` via with_delay
- [x] 4.3 Add `_cron_strategy_eval_impl()`: find articles state=scraped, strategy_eval_state=pending, queue evaluation job per article
- [x] 4.4 Add `_evaluate_strategy_labels()` queue job method: for each active strategy with non-empty prompt, call AI, assign matching labels, set strategy_eval_state=processed
- [x] 4.5 Add `_evaluate_against_strategy(strategy)` helper: build AI prompt from strategy.prompt + article content, call AI, parse JSON response, return list of label names to assign
- [x] 4.6 Reuse `_call_ai` and `_parse_ai_json` from `newsassistant_blog` by importing from `odoo.addons.newsassistant_blog.models.news_article` OR duplicate minimal versions in this module (prefer duplication to avoid cross-module dependency)
- [x] 4.7 Create `data/ir_cron_data.xml` with cron record: `_cron_strategy_eval_impl`, interval 1 hour, active

## 5. Article Views — Label Chips and Filter

- [x] 5.1 Create `views/news_article_views.xml` with `_inherit` of existing kanban view: add `strategy_label_ids` widget (many2many_tags with color) to kanban card
- [x] 5.2 Extend the existing article search view to add `strategy_label_ids` filter field
- [x] 5.3 Extend the existing article form view to add `strategy_label_ids` field and "Re-evaluate Strategy Labels" button
- [x] 5.4 Extend the existing article list view to add `strategy_label_ids` column (optional show)

## 6. Strategy Digest Model

- [x] 6.1 Create `models/strategy_digest.py` with `strategy.digest` model: `name`, `date_from` (required), `date_to` (required), `strategy_ids` (M2M → strategy.strategy), `article_ids` (M2M → news.article), `brief` (Html), `state` (Selection draft/done, default draft)
- [x] 6.2 Add `_get_active_strategies_for_period()`: returns strategies whose date range overlaps the digest period (None dates = always active)
- [x] 6.3 Add `_get_articles_for_period()`: returns articles with date in period and strategy_label_ids not empty
- [x] 6.4 Add `action_generate_brief()`: resolve strategies + articles, build AI prompt in user language, call AI, store HTML in brief, set state=done, populate strategy_ids and article_ids
- [x] 6.5 Add `_build_brief_prompt(strategies, articles, lang)` helper: constructs the AI system prompt instructing executive summary + detailed analysis with footnotes, in the user's language
- [x] 6.6 Add constraint: date_from required and date_to required (SQL or Python)
- [x] 6.7 Add security rules for `strategy.digest` in `ir.model.access.csv`

## 7. Strategy Digest Views and Menu

- [x] 7.1 Create `views/strategy_digest_views.xml` with form view (name, dates, state, Generate Brief button, brief Html field, strategy_ids, article_ids), list view (name, date_from, date_to, state), window action
- [x] 7.2 Create `views/menu.xml` with new "Strategy Digest" top-level menu (or sub-menu under News Assistant) containing: Articles (reuse existing action), Strategies, Digest, and Configuration → Strategy Labels

## 8. QWeb PDF Report

- [x] 8.1 Create `report/strategy_digest_report.xml` with `ir.actions.report` record: model=strategy.digest, report_type=qweb-pdf, NO paperformat_id set (inherits company default)
- [x] 8.2 Create `report/strategy_digest_report_template.xml` with QWeb template: `t-call="web.html_container"` → `t-call="web.external_layout"` → digest name/period header, brief content, sources list
- [x] 8.3 Bind report to Print menu via `binding_model_id` and `binding_type=report`

## 9. Demo Data

- [x] 9.1 Create `demo/strategy_label_demo.xml` with 3–4 sample strategy labels (e.g. Innovation, Risk, Sustainability, Digitalisation)
- [x] 9.2 Create `demo/strategy_digest_demo.xml` with 1 sample digest record (draft state, no brief — user generates)

## 10. Tests

- [x] 10.1 Create `tests/__init__.py` and `tests/test_strategy_label.py`: test label creation, uniqueness constraint, M2M assignment to article
- [x] 10.2 Create `tests/test_strategy_strategy.py`: test model creation, `_is_active_for_period` with all date combinations (none/from-only/to-only/range), `_extract_pdf_text` with mocked pdfminer, `action_distill_prompt` with mocked `_call_ai`
- [x] 10.3 Create `tests/test_news_article.py`: test `strategy_eval_state` default, `action_reevaluate_strategy_labels`, `_evaluate_against_strategy` with mocked `_call_ai`, `_cron_strategy_eval_impl` with trap_jobs
- [x] 10.4 Create `tests/test_strategy_digest.py`: test model creation, `_get_active_strategies_for_period`, `_get_articles_for_period`, `action_generate_brief` with mocked `_call_ai`, UserError on empty article set
- [x] 10.5 Create `tests/test_report.py`: test PDF report renders without error for a digest record

## 11. Translations

- [x] 11.1 Extract POT from running instance and create `i18n/de.po` with complete German translations
- [x] 11.2 Create `i18n/fr.po` with complete French translations
- [x] 11.3 Install translations and verify

