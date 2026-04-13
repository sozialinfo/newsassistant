## 1. Article Display Name Fix

- [x] 1.1 Add `_rec_name = "title"` to `NewsArticle` model in `models/news_article.py`

## 2. Pretty URLs for Actions

- [x] 2.1 Add `path` field to `news_article_action` in `views/news_article_views.xml` (path="articles")
- [x] 2.2 Add `path` field to `news_source_action` in `views/menu.xml` (path="sources")
- [x] 2.3 Add `path` field to `pipeline_monitor_action` in `views/pipeline_monitor_views.xml` (path="pipeline-monitor")

## 3. Stage Configuration Views

- [x] 3.1 Create `views/news_article_stage_views.xml` with list view for stages (editable, ordered by sequence)
- [x] 3.2 Add form view for stages in `views/news_article_stage_views.xml`
- [x] 3.3 Create window action for stages with path="article-stages"

## 4. Configuration Menu

- [x] 4.1 Add Configuration submenu to `views/menu.xml` restricted to admin group
- [x] 4.2 Add "Article Stages" menu item under Configuration, linked to stages action

## 5. Module Manifest

- [x] 5.1 Add `views/news_article_stage_views.xml` to data list in `__manifest__.py`

## 6. Verification

- [x] 6.1 Restart Odoo and upgrade module
- [x] 6.2 Verify article form shows title in header (not "news,article,ID")
- [x] 6.3 Verify URL is `/odoo/articles` for article list and `/odoo/articles/{id}` for form
- [x] 6.4 Verify Configuration menu visible only to admin users
- [x] 6.5 Verify stages can be created/edited via Configuration → Article Stages
