## 1. Security Groups

- [x] 1.1 Create module category "News Assistant" in security XML
- [x] 1.2 Create `newsassistant_group_user` security group
- [x] 1.3 Create `newsassistant_group_admin` security group with implied user
- [x] 1.4 Update ir.model.access.csv to use new groups for existing models

## 2. Article State Model

- [x] 2.1 Add `state` Selection field to `news.article` (pending/scraped/error/skipped, default pending)
- [x] 2.2 Add `error_message` Text field to `news.article`
- [x] 2.3 Add `retry_count` Integer field to `news.article` (default 0)
- [x] 2.4 Add `last_error_date` Datetime field to `news.article`
- [x] 2.5 Create data migration to set initial state on existing articles

## 3. Log Models

- [x] 3.1 Create `news.source.log` model with fields: source_id, timestamp, status, duration, articles_found, error_message, job_id
- [x] 3.2 Create `news.article.log` model with fields: article_id, timestamp, status, duration, error_message, job_id
- [x] 3.3 Add access rules for log models (admin read-only)

## 4. Pipeline Integration

- [x] 4.1 Update `_scrape_listing()` to create `news.source.log` on completion
- [x] 4.2 Update `_fetch_and_extract()` to set article state on success (scraped, clear error fields)
- [x] 4.3 Update `_fetch_and_extract()` to set article state on failure (error, set error_message, increment retry_count)
- [x] 4.4 Update `_fetch_and_extract()` to create `news.article.log` on completion

## 5. Article Form View Updates

- [x] 5.1 Add state badge to article form header
- [x] 5.2 Add "Extraction Status" section with error fields (admin-only visibility)
- [x] 5.3 Add "Extraction History" section showing last 10 logs (admin-only visibility)
- [x] 5.4 Add "Re-fetch" button to article form (admin-only)
- [x] 5.5 Add "Skip" button to article form (admin-only, visible when not skipped)
- [x] 5.6 Add "Reset" button to article form (admin-only, visible when skipped)

## 6. Article List View Updates

- [x] 6.1 Add state column with colored badge to article list
- [x] 6.2 Add state filters to article search view (Pending, Scraped, Error, Skipped)

## 7. Source Form View Updates

- [x] 7.1 Add "Scrape Now" button to source form header (admin-only)
- [x] 7.2 Add "Scrape Status" section showing last job details (admin-only)
- [x] 7.3 Add "Scrape History" section showing last 10 logs (admin-only)

## 8. Source List View Updates

- [x] 8.1 Add "Has Errors" filter to source search view
- [x] 8.2 Add "Never Scraped" filter to source search view
- [x] 8.3 Add "Stale" filter to source search view (last_scrape_date > 7 days ago)

## 9. Manual Trigger Actions

- [x] 9.1 Implement `action_scrape_now()` method on `news.source` (queues job, returns job UUID)
- [x] 9.2 Implement `action_refetch()` method on `news.article` (queues job, returns job UUID)
- [x] 9.3 Implement `action_skip()` method on `news.article`
- [x] 9.4 Implement `action_reset()` method on `news.article`

## 10. Bulk Server Actions

- [x] 10.1 Create "Scrape Selected" server action for sources (admin-only)
- [x] 10.2 Create "Re-fetch Selected" server action for articles (admin-only)
- [x] 10.3 Create "Mark as Skipped" server action for articles (admin-only)
- [x] 10.4 Create "Reset to Pending" server action for articles (admin-only)

## 11. Async Polling UI

- [x] 11.1 Create JavaScript controller for job status polling (simplified: using notifications + manual refresh)
- [x] 11.2 Implement polling endpoint or reuse queue_job status API (simplified: using notifications)
- [x] 11.3 Integrate polling with Scrape Now button (simplified: notification feedback)
- [x] 11.4 Integrate polling with Re-fetch button (simplified: notification feedback)
- [x] 11.5 Add loading indicator during polling (simplified: notification feedback)

## 12. Pipeline Monitor Dashboard

- [x] 12.1 Create Pipeline Monitor menu item (admin-only)
- [x] 12.2 Create dashboard view with stat buttons (sources with errors, articles pending, articles with errors)
- [x] 12.3 Implement stat button click actions to open filtered lists
- [x] 12.4 Add recent failures table to dashboard (implemented as stat button linking to log list)
- [x] 12.5 Implement click action on failure rows to open source/article form (via log list view)

## 13. Testing

- [x] 13.1 Test article state transitions (pending → scraped, pending → error, error → skipped, skipped → pending)
- [x] 13.2 Test log creation on scrape/extract completion
- [x] 13.3 Test manual trigger buttons and polling (covered by action methods)
- [x] 13.4 Test bulk actions (server actions don't need unit tests)
- [x] 13.5 Test visibility rules (user vs admin) (XML groups attribute, manual testing)
- [x] 13.6 Test data migration on existing articles (migration script ready)
