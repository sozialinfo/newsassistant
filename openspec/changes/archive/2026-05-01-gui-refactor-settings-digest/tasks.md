## 1. Digest — Blog Tab

- [x] 1.1 Remove `invisible="not teaser"` from Blog tab in `newsassistant_blog/views/news_article_views.xml`

## 2. Settings — Consolidation

- [x] 2.1 Change `inherit_id` in `newsassistant_blog/views/res_config_settings_views.xml` from `base.res_config_settings_view_form` to `newsassistant.res_config_settings_view_form_newsassistant`
- [x] 2.2 Replace `<app name="newsassistant_blog">` wrapper with `<xpath expr="//app[@name='newsassistant']" position="inside">` to inject blocks into the News Assistant app block
- [x] 2.3 Remove the `action_newsassistant_blog_settings` action record (no longer needed)
- [x] 2.4 Remove the "Blog Settings" menu item from `newsassistant_blog/views/menu.xml`

## 3. Settings — Prompt Layout

- [x] 3.1 In the Content Strategy block: wrap label in `<label class="o_form_label d-block mb4">` on own line, add `w-100` class and `style="width: 100%"` to parent div and field
- [x] 3.2 In the Teaser Generation block: same layout fixes for the teaser prompt field

## 4. Settings — Relevance Criteria Help Text

- [x] 4.1 Update `help=` on the Relevance Criteria `<setting>` to explain Relevant → auto-publish, Uncertain → Shortlist for human review, Discard → Discard stage and skipped

## 5. News Source — Computed Fields

- [x] 5.1 Add `snapshot_count = fields.Integer(compute="_compute_snapshot_count")` to `news.source` model
- [x] 5.2 Add `log_count = fields.Integer(compute="_compute_log_count")` to `news.source` model
- [x] 5.3 Add `active_job_count = fields.Integer(compute="_compute_active_job_count")` to `news.source` model
- [x] 5.4 Implement `_compute_snapshot_count` method using `search_count`
- [x] 5.5 Implement `_compute_log_count` method using `search_count`
- [x] 5.6 Implement `_compute_active_job_count` method using SQL on `queue_job` table

## 6. News Source — Action Methods

- [x] 6.1 Implement `action_view_logs` method returning filtered `news.log` list action
- [x] 6.2 Implement `action_view_snapshots` method returning filtered `news.snapshot` list action
- [x] 6.3 Implement `action_view_active_jobs` method using SQL to get job UUIDs, returning filtered `queue.job` list action

## 7. News Source — Form View

- [x] 7.1 Remove the Snapshots tab from the notebook in `newsassistant/views/news_source_views.xml`
- [x] 7.2 Remove the Log tab from the notebook in `newsassistant/views/news_source_views.xml`
- [x] 7.3 Remove the now-empty `<notebook>` element
- [x] 7.4 Add Logs smart button (admin only) to `oe_button_box`
- [x] 7.5 Add Snapshots smart button (all users) to `oe_button_box`
- [x] 7.6 Add Active Jobs smart button (system admin, hidden when count=0) to `oe_button_box`

## 8. News Article — Queue Job Button

- [x] 8.1 Add `active_job_count = fields.Integer(compute="_compute_active_job_count")` to `news.article` model
- [x] 8.2 Implement `_compute_active_job_count` method using SQL on `queue_job` table
- [x] 8.3 Implement `action_view_active_jobs` method returning filtered `queue.job` list action
- [x] 8.4 Add `oe_button_box` with Active Jobs smart button to `newsassistant/views/news_article_views.xml`
- [x] 8.5 Update `newsassistant_blog/views/news_article_views.xml` Blog Post button xpath to inject into existing `button_box` instead of creating a new one

## 9. Translations

- [x] 9.1 Add DE/FR translations for `active_job_count`, `log_count`, `snapshot_count` field labels in `newsassistant/i18n/de.po` and `fr.po`

## 10. Tests

- [x] 10.1 Write tests for `news.source` computed fields (`snapshot_count`, `log_count`, `active_job_count`)
- [x] 10.2 Write tests for `news.source` action methods (`action_view_logs`, `action_view_snapshots`, `action_view_active_jobs`)
- [x] 10.3 Write tests for `news.article` computed field (`active_job_count`) and action method (`action_view_active_jobs`)
- [x] 10.4 Run full test suite and verify no regressions
