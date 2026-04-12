## 1. Project Setup & Configuration

- [x] 1.1 Create addon scaffold: `addons/newsassistant/` with `__init__.py`, `__manifest__.py`, and standard subdirectories (`models/`, `views/`, `data/`, `demo/`, `tests/`, `static/description/`)
- [x] 1.2 Create `.env` file at project root with `INFOMANIAK_AI_API_KEY=aDvbaRabNHdS7SFKDFA7cC6z_OnLtSA6fsO0trEKAN-dgNlmV_viiB_lH2XDbv8W7lCdMQi5nf5U7I3s` and add `.env` to `.gitignore`
- [x] 1.3 Update `docker-compose.yml`: add volume mount for OCA queue addons (`/home/debian/shared/odoo-src/18.0/oca/queue:/mnt/oca/queue:ro`), pass `INFOMANIAK_AI_API_KEY` from `.env` to container environment
- [x] 1.4 Update `odoo.conf`: add `/mnt/oca/queue` to `addons_path`, add `server_wide_modules = web,queue_job`, add `[queue_job]` section with `channels = root:4,root.newsassistant:4`
- [x] 1.5 Write `__manifest__.py` with module metadata, dependencies (`base`, `queue_job`), data files, demo files, and external dependencies

## 2. Data Models

- [x] 2.1 Create `news.article.stage` model with fields: `name` (Char, required, translate=True), `sequence` (Integer), `fold` (Boolean, default False)
- [x] 2.2 Create `news.source` model with fields: `name`, `url`, `active`, `last_scrape_date`, `state` (selection ok/error), `error_message`, `article_count` (computed). Add `_scrape_listing()` method stub
- [x] 2.3 Create `news.article` model with fields: `title`, `source_id`, `url` (indexed), `date`, `summary`, `content`, `stage_id` (default to "New" stage), `scrape_date`. Add `_fetch_and_extract()` method stub and URL normalization helper
- [x] 2.4 Create `models/__init__.py` importing all models; create `__init__.py` in root importing models

## 3. Data & Demo Data

- [x] 3.1 Create `data/news_article_stage_data.xml` with default stages: New (seq 10), Relevant (seq 20), Archived (seq 30, fold), Discarded (seq 40, fold)
- [x] 3.2 Create `data/queue_job_data.xml` with channel definition (`root.newsassistant`) and job function registrations for `_scrape_listing` and `_fetch_and_extract` with retry pattern `{1: 300, 3: 900, 5: 3600}`
- [x] 3.3 Create `data/ir_cron_data.xml` with daily cron job calling `news.source._cron_scrape_all()`
- [x] 3.4 Create `data/ir_config_parameter_data.xml` with default `newsassistant.infomaniak_product_id` = `103794`
- [x] 3.5 Create `demo/news_source_demo.xml` with 8+ sources from `news_source.csv` covering diverse CMS types (Drupal, WordPress, TYPO3, others)

## 4. Views & Menus

- [x] 4.1 Create `views/news_source_views.xml` with list view and form view for `news.source`
- [x] 4.2 Create `views/news_article_views.xml` with kanban view (grouped by stage_id, cards showing title/source/date/summary), list view, and form view for `news.article`
- [x] 4.3 Create `views/menu.xml` with top-level "News Assistant" menu, sub-menus for Articles (default, kanban) and Sources (list), and search views with filters for source, stage, and date

## 5. Security

- [x] 5.1 Create `security/ir.model.access.csv` with CRUD access for all three models (news.source, news.article, news.article.stage) for base.group_user

## 6. Core Scraping Logic

- [x] 6.1 Create `models/ai_service.py` (or mixin) with `_call_infomaniak_ai(prompt, html_content)` method: reads API key from env, product ID from ir.config_parameter, calls the chat completions endpoint, parses JSON response, raises UserError if API key missing, raises RetryableJobError on transient AI errors
- [x] 6.2 Create `models/html_cleaner.py` (or mixin) with `_clean_html(raw_html)` method: uses BeautifulSoup to strip nav/header/footer/aside/form/script/style tags, removes all attributes, truncates to 30,000 chars
- [x] 6.3 Implement `news.source._cron_scrape_all()`: iterate active sources, call `source.with_delay()._scrape_listing()` for each
- [x] 6.4 Implement `news.source._scrape_listing()`: HTTP GET source URL, pre-clean HTML, call AI Stage 1 prompt, parse JSON response to get article URLs/titles, normalize URLs, filter out duplicates, create `news.article` stubs and call `article.with_delay()._fetch_and_extract()` for each new article. Update `last_scrape_date` and `state`. Handle errors (set state=error on permanent failures, raise RetryableJobError on transient)
- [x] 6.5 Implement `news.article._fetch_and_extract()`: HTTP GET article URL, pre-clean HTML, call AI Stage 2 prompt, parse JSON response, update article record with title, date, summary, content, scrape_date. Handle errors (RetryableJobError on transient, log and skip on permanent)
- [x] 6.6 Implement URL normalization helper: strip trailing slashes, strip URL fragments, normalize for dedup comparison

## 7. Documentation

- [x] 7.1 Create `addons/newsassistant/README.md` with module overview, prerequisites, installation steps, configuration (API key, odoo.conf, docker-compose), usage guide, and technical architecture description
- [x] 7.2 Create `addons/newsassistant/agents.md` with definition of done checklist, coding standards, testing requirements, and quality criteria

## 8. Unit Tests

- [x] 8.1 Create `tests/__init__.py` and `tests/test_news_source.py`: test source CRUD, computed article_count, error state tracking, state recovery
- [x] 8.2 Create `tests/test_html_cleaner.py`: test tag stripping, attribute removal, truncation
- [x] 8.3 Create `tests/test_url_normalization.py`: test trailing slash stripping, fragment removal, dedup matching
- [x] 8.4 Create `tests/test_scraping_pipeline.py`: test Stage 1 (mock HTTP + mock AI response), test Stage 2 (mock HTTP + mock AI response), test deduplication skips known URLs, test error handling for HTTP failures and malformed AI responses
- [x] 8.5 Create `tests/test_queue_jobs.py`: test cron fan-out creates correct jobs (using trap_jobs), test _scrape_listing creates article jobs (using trap_jobs), test RetryableJobError raised on transient errors
- [x] 8.6 Create `tests/test_kanban.py`: test default stage assignment, test stage model data, test article creation defaults

## 9. Integration & Install

- [x] 9.1 Restart Docker container with updated config (docker-compose, odoo.conf)
- [x] 9.2 Install `queue_job` module
- [x] 9.3 Install `newsassistant` module with demo data
- [x] 9.4 Run the full test suite and fix any failures
- [x] 9.5 Verify kanban view loads correctly with demo sources visible
