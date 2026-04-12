# News Assistant — Agent Guidelines

## Definition of Done

A task or feature is considered **done** when ALL of the following criteria are met:

### Code Quality
- [ ] Code follows Odoo 18 coding standards and conventions
- [ ] No hardcoded values — configuration via system parameters or environment variables
- [ ] Proper error handling: transient errors raise `RetryableJobError`, permanent errors are logged
- [ ] Logging at appropriate levels (info for normal flow, warning for recoverable issues, exception for failures)
- [ ] No unused imports, no dead code

### Testing
- [ ] Unit tests exist for all new/modified functionality
- [ ] Tests run within Odoo's standard framework (`TransactionCase` or `HttpCase`)
- [ ] All external HTTP calls and AI API calls are mocked — no real network requests in tests
- [ ] Queue job creation is tested using `trap_jobs()` from `queue_job.tests.common`
- [ ] All tests pass: `odoo --test-tags newsassistant --stop-after-init`
- [ ] Edge cases covered: empty responses, malformed JSON, HTTP errors, missing config

### Functionality
- [ ] Feature works end-to-end in the Odoo UI
- [ ] Kanban view displays articles correctly with title, source, date, and summary
- [ ] Drag-and-drop between stages works
- [ ] Source error states are visible and recoverable
- [ ] Deduplication prevents duplicate article creation

### Documentation
- [ ] README.md is up to date with any new features or config changes
- [ ] Code has docstrings on all public methods
- [ ] Complex logic has inline comments explaining the "why"

## Coding Standards

### Python
- Follow PEP 8 and Odoo's coding guidelines
- Use `_logger` for logging (not `print`)
- Prefix private methods with `_` (e.g., `_scrape_listing`, `_fetch_and_extract`)
- Use `self.ensure_one()` in methods that operate on a single record
- Use `fields.Datetime.now()` instead of `datetime.now()`

### XML
- Use 4-space indentation
- Use `noupdate="1"` for data that should not be overwritten on module update
- Use meaningful XML IDs with module prefix pattern

### Queue Jobs
- Always specify `channel="root.newsassistant"` when calling `with_delay()`
- Always provide a human-readable `description` for jobs
- Raise `RetryableJobError` for transient failures (timeout, 5xx, rate limit)
- Do NOT retry permanent failures (404, 403, malformed content)

### AI Integration
- Always pre-clean HTML before sending to the AI (strip nav, footer, script, style)
- Always instruct the AI to return JSON only, no markdown
- Always handle the case where AI returns invalid JSON
- Always strip markdown code fences from AI responses before parsing

## Test Patterns

### Model Tests
```python
from odoo.tests.common import TransactionCase

class TestNewsSource(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.source = cls.env["news.source"].create({
            "name": "Test Source",
            "url": "https://example.com/news",
        })
```

### Queue Job Tests
```python
from odoo.tests.common import TransactionCase
from odoo.addons.queue_job.tests.common import trap_jobs

class TestQueueJobs(TransactionCase):
    def test_cron_creates_jobs(self):
        with trap_jobs() as trap:
            self.env["news.source"]._cron_scrape_all()
            trap.assert_jobs_count(expected_count, only=self.env["news.source"]._scrape_listing)
```

### Mocking HTTP and AI
```python
from unittest.mock import patch, MagicMock

def _mock_requests_get(url, **kwargs):
    response = MagicMock()
    response.status_code = 200
    response.text = "<html>...</html>"
    return response

with patch("odoo.addons.newsassistant.models.news_source.requests.get", side_effect=_mock_requests_get):
    # test code
```

## Project Structure

```
addons/newsassistant/
├── __init__.py
├── __manifest__.py
├── README.md
├── agents.md
├── models/
│   ├── __init__.py
│   ├── news_article_stage.py
│   ├── news_source.py          # includes AI service + HTML cleaner + scraping logic
│   └── news_article.py         # includes fetch_and_extract logic
├── views/
│   ├── news_source_views.xml
│   ├── news_article_views.xml
│   └── menu.xml
├── data/
│   ├── news_article_stage_data.xml
│   ├── queue_job_data.xml
│   ├── ir_cron_data.xml
│   └── ir_config_parameter_data.xml
├── demo/
│   └── news_source_demo.xml
├── security/
│   └── ir.model.access.csv
├── static/
│   └── description/
└── tests/
    ├── __init__.py
    ├── test_news_source.py
    ├── test_html_cleaner.py
    ├── test_url_normalization.py
    ├── test_scraping_pipeline.py
    ├── test_queue_jobs.py
    └── test_kanban.py
```
