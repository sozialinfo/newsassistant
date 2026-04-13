## 1. Remove Old Infrastructure

- [x] 1.1 Delete `news.pipeline.monitor` model file (`models/pipeline_monitor.py`)
- [x] 1.2 Delete `news.source.log` model file (`models/news_source_log.py`)
- [x] 1.3 Delete `news.article.log` model file (`models/news_article_log.py`)
- [x] 1.4 Remove Pipeline Monitor views (`views/pipeline_monitor_views.xml`)
- [x] 1.5 Remove Pipeline Monitor menu item from `views/menu.xml`
- [x] 1.6 Remove old log model imports from `models/__init__.py`
- [x] 1.7 Remove old log model access rules from `security/ir.model.access.csv`

## 2. Create New Log Models

- [x] 2.1 Create `news.log` model (`models/news_log.py`) with fields: timestamp, level, category, message, duration, source_id, article_id, job_id, entry_ids
- [x] 2.2 Create `news.log.entry` model (`models/news_log_entry.py`) with fields: log_id, timestamp, level, message, duration, metadata
- [x] 2.3 Add new model imports to `models/__init__.py`
- [x] 2.4 Add access rules for `news.log` (admin read-only, system full)
- [x] 2.5 Add access rules for `news.log.entry` (admin read-only, system full)

## 3. Create Vacuum Rule

- [x] 3.1 Add `_transient_vacuum` method to `news.log.entry` model using ir.autovacuum pattern
- [x] 3.2 Configure vacuum to delete entries where parent log level is 'success' and older than 1 day

## 4. Modify LLM Integration

- [x] 4.1 Modify `_call_infomaniak_ai` to return dict with `content`, `usage`, and timing instead of just content string
- [x] 4.2 Update callers in `_scrape_listing` to handle new return format
- [x] 4.3 Update callers in `_fetch_and_extract` to handle new return format

## 5. Implement Logging in Pipeline

- [x] 5.1 Create helper method `_create_log` on `news.source` for creating log with entries
- [x] 5.2 Create helper method `_create_log` on `news.article` for creating log with entries
- [x] 5.3 Update `_scrape_listing` to create log entries for: start, Jina fetch, LLM call (with full metadata), parse result, completion
- [x] 5.4 Update `_fetch_and_extract` to create log entries for: start, Jina fetch, LLM call (with full metadata), parse result, completion
- [x] 5.5 Set log level based on final outcome (success/warning/error)
- [x] 5.6 Capture and pass job_id to log creation

## 6. Create Log Views

- [x] 6.1 Create `news.log` list view with columns: Timestamp, Level (badge), Category, Source, Article, Message, Duration
- [x] 6.2 Create `news.log` form view with summary fields and embedded entry list
- [x] 6.3 Create `news.log` search view with filters for source, article, level, category, date range
- [x] 6.4 Create `news.log` search view with group by options for source, level, category
- [x] 6.5 Create `news.log.entry` inline list view for embedding in log form
- [x] 6.6 Add metadata JSON viewer for log entries (modal or expandable)
- [x] 6.7 Configure `many2one_link` widget on source_id, article_id, job_id fields for navigation

## 7. Create Running Jobs View

- [x] 7.1 Create action for Running Jobs showing `queue.job` filtered to state='started' and newsassistant channel
- [x] 7.2 Add "Running Now" computed field or embedded view in Logs list (header section)

## 8. Update Source Views

- [x] 8.1 Rename "Scrape History" section to "Log" tab on source form
- [x] 8.2 Replace embedded `news.source.log` list with `news.log` filtered by source_id
- [x] 8.3 Add computed `is_scraping` Boolean field on `news.source` checking for running jobs
- [x] 8.4 Add scraping indicator badge to Sources list view

## 9. Update Article Views

- [x] 9.1 Rename "History" tab to "Log" tab on article form
- [x] 9.2 Replace embedded `news.article.log` list with `news.log` filtered by article_id
- [x] 9.3 Remove old extraction history group and error details group (now in unified log)

## 10. Update Menu Structure

- [x] 10.1 Add "Running Jobs" menu item (admin only, sequence 35)
- [x] 10.2 Add "Logs" menu item (admin only, sequence 40)
- [x] 10.3 Verify Pipeline Monitor menu item is removed (done in 1.5)

## 11. Update Manifest and Cleanup

- [x] 11.1 Remove deleted view files from `__manifest__.py` data list
- [x] 11.2 Add new view files to `__manifest__.py` data list
- [x] 11.3 Update module version in `__manifest__.py`

## 12. Testing

- [x] 12.1 Test listing scrape creates log with entries (including LLM metadata)
- [x] 12.2 Test article extraction creates log with entries (including LLM metadata)
- [x] 12.3 Test log level is set correctly for success/warning/error outcomes
- [x] 12.4 Test vacuum deletes success entries older than 1 day
- [x] 12.5 Test vacuum preserves error/warning entries
- [x] 12.6 Test is_scraping indicator shows during active job
- [x] 12.7 Test navigation links work (source, article, job from log)
- [x] 12.8 Test admin access to Logs and Running Jobs menus
- [x] 12.9 Test regular user cannot see Log tabs or admin menus
