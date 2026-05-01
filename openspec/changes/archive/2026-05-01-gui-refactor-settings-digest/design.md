## Context

The News Assistant Odoo module suite has several UI rough edges that have been identified through daily use:

1. **Blog tab hidden on discarded articles** — `invisible="not teaser"` on the Blog tab means discard reasoning (`blog_reasoning`) is inaccessible when an article is discarded (because no teaser is generated for discarded articles). Users cannot see why an article was discarded.

2. **Split settings menus** — `newsassistant_blog` settings use a separate `<app>` block in the standard Odoo settings grid (appears as a separate app), with a separate "Blog Settings" menu entry in the Configuration menu. The email settings are correctly merged into the `newsassistant` app block via `inherit_id`. Blog settings should follow the same pattern.

3. **Cramped prompt inputs** — The multiline textarea fields for content strategy and teaser prompt appear side-by-side with their labels in the settings `<setting>` widget's 2-column layout. This makes the textarea narrow. Labels should be on their own line above the field, and the field should use full available width.

4. **Insufficient help text on relevance criteria** — The "Relevance Criteria" setting's `help=` text doesn't explain that the three AI classification outcomes map to concrete actions (auto-publish, shortlist for human review, discard).

5. **Slow inline tabs for logs/snapshots** — The news source form embeds inline lists for both Snapshots and Logs inside notebook tabs. For sources with many logs, this is slow to render and wastes space. Smart buttons navigating to filtered list views are more idiomatic Odoo.

6. **No queue job visibility** — There is no way to see active queue jobs from a source or article form. The `is_scraping` boolean exists but provides no clickable access. Admins debugging hung jobs must navigate to the queue job list manually.

## Goals / Non-Goals

**Goals:**
- Always show Blog tab on articles (remove conditional visibility)
- Merge blog settings into the single `newsassistant` app block
- Remove "Blog Settings" menu entry; keep only "Settings" in Configuration menu
- Fix prompt label/field layout: label on own line, full-width textarea
- Improve relevance criteria help text with outcome explanations
- Replace Snapshots tab with smart button on news source form
- Replace Log tab with smart button on news source form
- Add Active Jobs smart button on news source form (admin/system, count > 0)
- Add Active Jobs smart button on news article form (admin/system, count > 0)

**Non-Goals:**
- Changing any business logic in the digest pipeline
- Adding new queue job functionality
- Modifying the news.log or news.snapshot models
- Changing access control rules

## Decisions

### D1: Settings merge via xpath inheritance (not new app block)

**Decision:** Change `newsassistant_blog/views/res_config_settings_views.xml` to inherit from `newsassistant.res_config_settings_view_form_newsassistant` (the base module's view) and use xpath `//app[@name='newsassistant']` to inject blocks. Remove the `<app>` wrapper.

**Rationale:** This is the exact same pattern used by `newsassistant_email`. Both submodules inject blocks into the parent app block. No need for a separate app in the settings grid.

**Alternative considered:** Keep separate app block but link from one menu item. Rejected — this still creates a separate "app" tile in the standard Odoo settings grid, which is confusing.

### D2: Smart buttons use `type="object"` action methods (not direct action refs)

**Decision:** Log, Snapshot, and Job smart buttons call Python methods (`action_view_logs`, `action_view_snapshots`, `action_view_active_jobs`) that return `ir.actions.act_window` dicts with computed domains.

**Rationale:** The log and snapshot actions already exist as global actions, but we need to pass `source_id` as a domain filter. Using `type="object"` methods gives us full control over the domain. Queue jobs require a SQL query to find UUIDs since `queue.job.records` is a JSONB-serialized field that cannot be filtered via normal Odoo domain syntax.

**Alternative considered:** Use `context="{'search_default_source_id': id}"` on a direct action reference. Rejected for queue jobs (no standard domain field). Consistent approach: all three buttons use object methods.

### D3: Job count via raw SQL against queue_job table

**Decision:** `active_job_count` is a non-stored computed field using `self.env.cr.execute()` with a SQL query on the `queue_job` table, filtering by `model_name` and `records->>'res_id'`. Same pattern as the existing `is_scraping` field.

**Rationale:** The `queue.job` model's `records` field is a `JobSerialized` (JSONB) field — not a standard Odoo relational field. ORM search/domain cannot filter on it. SQL is the only reliable approach. The existing `is_scraping` proves this pattern works.

### D4: Active job button uses UUID list domain

**Decision:** `action_view_active_jobs()` runs a SQL query to get job UUIDs, then returns an action with `domain=[("uuid", "in", [...])]`.

**Rationale:** `queue.job` has a standard `uuid` Char field that is indexed and searchable via ORM. This avoids the JSONB domain problem while still giving a properly filtered list view.

### D5: Active jobs button uses `groups="base.group_system"` (Administrator)

**Decision:** The queue jobs smart button is gated on `base.group_system` (Technical Administrator), not `newsassistant.newsassistant_group_admin`.

**Rationale:** Queue job monitoring is a technical concern appropriate for Odoo system administrators. The Log and Snapshot buttons are gated at `newsassistant_group_admin` (business admin) level, which is appropriate for operational monitoring.

### D6: Blog tab — remove invisible entirely (not replace with different condition)

**Decision:** Remove the `invisible="not teaser"` attribute entirely, making the Blog tab always visible when `newsassistant_blog` is installed.

**Rationale:** Even when an article is discarded (no teaser), the tab is useful to show `digest_state` (processed/pending) and `blog_reasoning` (the discard explanation). Making it always visible is the correct behavior. The `blog_reasoning` group inside already has its own `invisible="not blog_reasoning"` guard.

## Risks / Trade-offs

- **Settings inheritance order** → The blog settings view inherits from the newsassistant base settings view. If that view is not yet loaded when blog settings are applied, it would fail. Risk is very low since `newsassistant_blog` depends on `newsassistant` — Odoo loads dependencies first. Mitigation: test on fresh instance.

- **Empty notebook** → The news source form previously had a `<notebook>` with two pages. After removing both pages, the notebook element itself is removed. If any other view (website module) xpaths into the notebook, it would fail. Verified: the website extension only modifies `//header`, not the notebook.

- **queue_job table may not exist on first install** → The `_compute_active_job_count` and `_compute_is_scraping` both query the `queue_job` table. If `queue_job` module is not installed, this would error. Risk is same as existing `is_scraping` field — the module already depends on `queue_job`. No additional risk.

- **Prompt layout with `w-100`** → The Odoo settings form uses a CSS grid layout. The `w-100` class and `style="width: 100%"` on the field should make the textarea expand to fill the available column width. Odoo 18's Bootstrap-based styling should support this without custom CSS.

## Migration Plan

This is a pure view/model change with no database migrations:
1. Update module code
2. Upgrade modules: `odoo -d <db> -u newsassistant,newsassistant_blog`
3. No data migration needed — no field type changes, no renamed fields

Rollback: revert git changes and upgrade again.
