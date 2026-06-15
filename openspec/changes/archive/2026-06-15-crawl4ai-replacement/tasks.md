## 1. Docker Setup

- [x] 1.1 Add crawl4ai service to docker-compose.yml
- [x] 1.2 Remove JINA_API_KEY env var from docker-compose.yml

## 2. Backend Implementation

- [x] 2.1 Create `crawl4ai_utils.py` with `fetch_page()` calling crawl4ai REST API
- [x] 2.2 Create `res_config_settings.py` with crawl4ai URL field
- [x] 2.3 Create `views/res_config_settings_views.xml` for settings UI
- [x] 2.4 Update `models/__init__.py` — add new model imports
- [x] 2.5 Update `news_source_website.py` — change import from jina_utils to crawl4ai_utils
- [x] 2.6 Delete `jina_utils.py`
- [x] 2.7 Update `__manifest__.py` — add new data files

## 3. Tests

- [x] 3.1 Create `test_crawl4ai_utils.py` with mocked crawl4ai responses
- [x] 3.2 Delete `test_jina_utils.py`
- [x] 3.3 Update `test_website_scraping.py` — change mock patches from jina_utils to crawl4ai_utils

## 4. Documentation

- [x] 4.1 Update `README.md` — replace JINA_API_KEY docs with crawl4ai setup
- [x] 4.2 Update `agents.md` — replace jina references with crawl4ai
- [x] 4.3 Update `.env.example` — remove JINA_API_KEY entry
- [x] 4.4 Update `__manifest__.py` version bump

## 5. Deployment

- [x] 5.1 Pull and start the crawl4ai container
- [x] 5.2 Upgrade the newsassistant_website module
- [x] 5.3 Restart Odoo and smoke test
