## 1. Update Article Stages Data (newsassistant)

- [x] 1.1 Replace `news_article_stage_relevant` with `news_article_stage_shortlist` (name: "Shortlist", seq 20, fold: False) in `news_article_stage_data.xml`
- [x] 1.2 Replace `news_article_stage_archived` with `news_article_stage_published` (name: "Published", seq 30, fold: True) in `news_article_stage_data.xml`

## 2. Core Module Settings (newsassistant)

- [x] 2.1 Create `newsassistant/models/res_config_settings.py` extending `res.config.settings` with `newsassistant_new_article_stage_id` (Many2one → `news.article.stage`, config_parameter: `newsassistant.new_article_stage_id`)
- [x] 2.2 Update `newsassistant/models/__init__.py` to import `res_config_settings`
- [x] 2.3 Update `news.article._default_stage_id()` to read from `ir.config_parameter` `newsassistant.new_article_stage_id`, falling back to "New" stage by name
- [x] 2.4 Create `newsassistant/views/res_config_settings_views.xml` with a settings page section for "News Assistant" showing the new article stage field
- [x] 2.5 Add settings view XML to `newsassistant/__manifest__.py` data list
- [x] 2.6 Add `res.config.settings` access to `newsassistant/security/ir.model.access.csv` if missing

## 3. Blog Module Stage Settings (newsassistant_blog)

- [x] 3.1 Add `newsassistant_blog_shortlist_stage_id` (Many2one → `news.article.stage`, config_parameter: `newsassistant_blog.shortlist_stage_id`) to `newsassistant_blog/models/res_config_settings.py`
- [x] 3.2 Add `newsassistant_blog_published_stage_id` (Many2one → `news.article.stage`, config_parameter: `newsassistant_blog.published_stage_id`) to `newsassistant_blog/models/res_config_settings.py`
- [x] 3.3 Add `newsassistant_blog_discard_stage_id` (Many2one → `news.article.stage`, config_parameter: `newsassistant_blog.discard_stage_id`) to `newsassistant_blog/models/res_config_settings.py`
- [x] 3.4 Update `get_values()` and `set_values()` in `newsassistant_blog/models/res_config_settings.py` to handle the three new stage fields
- [x] 3.5 Add the three stage fields to `newsassistant_blog/views/res_config_settings_views.xml` in a "Pipeline Stages" block

## 4. Install Hook (newsassistant_blog)

- [x] 4.1 Create `newsassistant_blog/hooks.py` with `post_init_hook(env)` that:
  - Finds or creates "Shortlist" stage and writes `newsassistant_blog.shortlist_stage_id`
  - Finds or creates "Published" stage (fold=True) and writes `newsassistant_blog.published_stage_id`
  - Finds or creates "Discarded" stage (fold=True) and writes `newsassistant_blog.discard_stage_id`
  - Finds or creates `blog.blog(name="News")` and writes `newsassistant_blog.blog_id`
- [x] 4.2 Register `post_init_hook` in `newsassistant_blog/__manifest__.py`

## 5. Wire Pipeline to Settings (newsassistant_blog)

- [x] 5.1 Add helper method `_get_pipeline_stage(param_key, fallback_name)` to `news.article` in `newsassistant_blog/models/news_article.py` that reads stage from `ir.config_parameter` by key, falls back to lookup by name
- [x] 5.2 Update `_handle_discard()` to use `_get_pipeline_stage('newsassistant_blog.discard_stage_id', 'Discarded')`
- [x] 5.3 Update `_handle_relevant()` (rename to `_handle_shortlist()`) to use `_get_pipeline_stage('newsassistant_blog.shortlist_stage_id', 'Shortlist')`
- [x] 5.4 Update `_create_blog_post()` to move article to `_get_pipeline_stage('newsassistant_blog.published_stage_id', 'Published')` after blog post creation
- [x] 5.5 Update `_digest_article()` call site to use the renamed `_handle_shortlist()` method

## 6. Remove Obsolete Stage Data References

- [x] 6.1 Audit `newsassistant_blog` for any remaining hardcoded references to `news_article_stage_relevant` or `news_article_stage_archived` XML IDs and replace with the settings-based lookup

## 7. Tests

- [x] 7.1 Update `newsassistant` tests: replace assertions on "Relevant"/"Archived" stage names with "Shortlist"/"Published"
- [x] 7.2 Add tests for `newsassistant` `res.config.settings`: get/set `newsassistant_new_article_stage_id`
- [x] 7.3 Add tests for `news.article._default_stage_id()` reading from config parameter
- [x] 7.4 Add tests for `newsassistant_blog` `res.config.settings`: get/set the three new stage fields
- [x] 7.5 Add tests for `post_init_hook`: stages found scenario and stages created scenario
- [x] 7.6 Add tests for `post_init_hook`: "News" blog found scenario and blog created scenario
- [x] 7.7 Add/update tests for `_handle_shortlist()`, `_handle_discard()`, and `_create_blog_post()` using settings-driven stages
