## Context

The newsassistant module scrapes news sources and extracts articles. Currently:
- Articles have a `state` field (pending/scraped/error/skipped) but no archive capability
- The `error_message` field stores both actual errors and skip reasons (semantic mismatch)
- Skipped articles remain visible in lists, cluttering the view
- Re-fetch/Skip/Reset buttons are prominent header buttons in the form view
- Deduplication only checks active articles (would re-fetch archived URLs)

Sources already have the `active` field (Odoo standard archive pattern).

## Goals / Non-Goals

**Goals:**
- Enable archiving articles using Odoo's standard `active` field pattern
- Automatically archive skipped articles (both AI-detected and manual)
- Maintain URL deduplication across ALL articles (including archived)
- Improve GUI clarity: show skip reasons, move admin buttons to action menu
- Clean field naming: `error_message` → `status_message`

**Non-Goals:**
- Auto-archive based on age (future enhancement)
- Archive based on stage (e.g., auto-archive "Done" articles)
- Bulk archive operations beyond Odoo's standard list actions

## Decisions

### 1. Use Odoo standard `active` field pattern
**Decision**: Add `active = fields.Boolean(default=True)` to `news.article`

**Rationale**: Odoo's ORM automatically filters `active=False` records from searches. This gives us archive/unarchive for free via standard UI actions. No custom archive state needed.

**Alternatives considered**:
- Custom `archived` field: Would require manual filtering everywhere, no standard UI support
- Soft-delete with `deleted_at`: Overkill, not Odoo convention

### 2. Rename `error_message` to `status_message`
**Decision**: Rename the field via migration, update all references

**Rationale**: The field stores both error messages (state=error) and skip reasons (state=skipped). `status_message` is semantically accurate for both cases.

**Alternatives considered**:
- Add separate `skip_reason` field: Creates redundancy, complicates logic
- Keep `error_message` but use it for both: Confusing, poor semantics

### 3. Auto-archive on skip (consistent behavior)
**Decision**: Both AI-skip and manual skip set `active=False`

**Rationale**: Users confirmed skip should always mean "hide from view." Consistency is better than having AI-skip behave differently from manual skip.

**Impact**: `action_skip()` and the AI skip path in `_fetch_and_extract()` both set `active=False`

### 4. Dedup includes archived articles
**Decision**: Use `with_context(active_test=False)` for URL existence check

**Rationale**: If we archived an article (skipped or manually), we don't want to re-create it next scrape cycle. The URL is still "known" even if archived.

**Location**: `news_source.py` line ~682, the `Article.search([("url", "=", normalized)])` call

### 5. Server actions instead of header buttons
**Decision**: Create `ir.actions.server` records for Re-fetch, Skip, Reset

**Rationale**: Server actions appear in the Action dropdown automatically. This de-clutters the form header while keeping the functionality accessible to admins.

**Visibility**: Actions will use `groups_id` to restrict to `newsassistant_group_admin`

## Risks / Trade-offs

**[Risk] Migration complexity for field rename**
→ Mitigation: Use Odoo's standard migration pattern with `openupgrade` or direct SQL rename. Test on staging first.

**[Risk] Users may be confused when skipped articles "disappear"**
→ Mitigation: Add "Archived" filter to search view, ensure it's discoverable. The skip action could show a notification: "Article archived (skipped)."

**[Risk] Performance of dedup query with active_test=False on large datasets**
→ Mitigation: The `url` field is already indexed (`index=True`). Query will still be fast. Monitor if issues arise.

**[Trade-off] Unarchiving a skipped article keeps it skipped**
→ Accepted: User confirmed this is desired. User can then use Reset action if they want to retry fetching.
