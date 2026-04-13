## Why

The Odoo 18 backend user experience for the News Assistant module has several rough edges that make daily use friction-prone. URLs are cryptic hash-based references instead of human-readable paths, article form views display "news,article,61" instead of the article title, and administrators have no way to configure article stages without direct database access.

## What Changes

- Add `path` field to all window actions for pretty URLs (e.g., `/odoo/articles/61` instead of `/odoo/action-123#id=61`)
- Set `_rec_name = "title"` on `news.article` model so form headers display the article title
- Create views and configuration menu for `news.article.stage` model, restricted to admin group
- Add list/form views for stage management with sequence, name, and fold configuration

## Capabilities

### New Capabilities
- `pretty-urls`: Configure Odoo 18 path-based routing for all module actions
- `stage-configuration`: Admin-only configuration menu for managing article stages

### Modified Capabilities
- `kanban-triage`: Article model needs `_rec_name` attribute for proper display name resolution

## Impact

- **Models**: `news.article` (add `_rec_name`), `news.article.stage` (add views)
- **Views**: New stage views (`news_article_stage_views.xml`), modify menu structure
- **Actions**: Add `path` field to `news_article_action`, `news_source_action`, `pipeline_monitor_action`
- **Security**: Existing `newsassistant_group_admin` group already exists for access control
- **Manifest**: Add new view files to data list
