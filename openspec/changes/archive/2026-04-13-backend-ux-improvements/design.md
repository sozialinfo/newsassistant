## Context

The News Assistant module runs on Odoo 18, which introduced path-based routing for the backend webclient (PR #142007). This replaces the old hash-based URLs (`/web#model=X&id=Y`) with human-readable paths (`/odoo/path/id`). The module currently does not leverage this feature, and has two additional UX issues: the form view header shows the model/id pattern instead of the article title, and stages cannot be configured via the UI.

**Current State:**
- URLs: `/odoo/action-123#id=61` (cryptic)
- Form header: "news,article,61" (no `_rec_name` set, model has `title` not `name`)
- Stages: Created via data XML, no admin UI for management

**Constraints:**
- Must follow Odoo 18 standard patterns
- Stage configuration must be admin-only
- Changes must be non-breaking (existing data preserved)

## Goals / Non-Goals

**Goals:**
- Enable pretty URLs for all module actions using Odoo 18's `path` field
- Fix article display name by setting `_rec_name = "title"`
- Provide admin-accessible stage configuration UI

**Non-Goals:**
- Custom URL patterns beyond what Odoo 18 framework supports
- Public/portal access to stages (admin only)
- Changing stage data model structure (just adding views)

## Decisions

### Decision 1: Use `path` field on actions for pretty URLs

**Choice:** Add `path` attribute to `ir.actions.act_window` records

**Rationale:** This is the Odoo 18 standard approach (introduced in commit c63d14a). The framework handles all routing, breadcrumb restoration, and backward compatibility automatically.

**Alternatives Considered:**
- Custom controllers with slug routes: Rejected - fights the framework, requires maintenance
- Website module integration: Rejected - overkill for backend-only module

**Implementation:**
```xml
<record id="news_article_action" model="ir.actions.act_window">
    <field name="path">articles</field>
    ...
</record>
```

**Resulting URLs:**
- `/odoo/articles` → Article kanban
- `/odoo/articles/61` → Article form
- `/odoo/sources` → Sources list
- `/odoo/pipeline-monitor` → Pipeline monitor

### Decision 2: Set `_rec_name` on article model

**Choice:** Add `_rec_name = "title"` to `NewsArticle` class

**Rationale:** Odoo uses `_rec_name` to determine the display name shown in form headers, Many2one dropdowns, and breadcrumbs. Without it, and without a `name` field, Odoo falls back to `model,id` format.

**Alternatives Considered:**
- Rename `title` to `name`: Rejected - would require migration, `title` is semantically correct
- Override `name_get()`: Rejected - `_rec_name` is simpler and sufficient

### Decision 3: Standard Odoo configuration pattern for stages

**Choice:** Create list/form views for `news.article.stage` with Configuration submenu

**Rationale:** Follows Odoo's standard pattern for model configuration (see Sales → Configuration → Pipeline stages as reference).

**Menu Structure:**
```
News Assistant
├── Articles
├── Sources
├── Pipeline Monitor (admin)
└── Configuration (admin)
    └── Article Stages
```

**Access Control:** Use existing `newsassistant.newsassistant_group_admin` group

## Risks / Trade-offs

**[Risk] Path collision with other modules** → Use descriptive paths (`articles` not `list`), paths are validated unique by Odoo

**[Risk] Existing bookmarks may break** → Odoo 18 automatically redirects old-format URLs to new format

**[Trade-off] Stage configuration is admin-only** → Acceptable - stage structure is application configuration, not user data
