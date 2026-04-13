## Why

Articles that are skipped (not actual news articles) or no longer relevant clutter the article list. Users need the ability to archive articles using Odoo's standard pattern, and skipped articles should automatically disappear from view while still being used for URL deduplication during fetching. Additionally, the Re-fetch/Skip/Reset buttons are too prominent in the form view header and should move to the action menu.

## What Changes

- Add `active` field to `news.article` model (Odoo standard archive pattern)
- Rename `error_message` field to `status_message` (used for both errors and skip reasons)
- Auto-archive articles when skipped (both AI-detected and manual skip)
- Show skip status and reason prominently in the GUI (list view column, form view banner)
- Move Re-fetch, Skip, and Reset buttons from form header to Action dropdown menu
- Update article deduplication to check ALL articles (including archived) during fetch

## Capabilities

### New Capabilities
- `article-archive`: Standard Odoo archive/unarchive functionality for articles with auto-archive on skip

### Modified Capabilities
- None (no existing specs to modify)

## Impact

- **Models**: `news.article` (new field, renamed field, modified methods)
- **Models**: `news.source` (dedup query change to include archived)
- **Views**: `news_article_views.xml` (remove header buttons, add status visibility, add archive filter)
- **Data**: `server_actions.xml` (new server actions for Re-fetch, Skip, Reset)
- **Migration**: Required to rename `error_message` → `status_message`
