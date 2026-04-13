## Context

The News Assistant addon scrapes news sources via a two-stage pipeline: Stage 1 discovers article URLs from listing pages, Stage 2 extracts content from each article. Both stages use queue_job for async processing with automatic retries.

Currently:
- Source-level errors are tracked (`state`, `error_message`) but article-level errors are implicit (buried in content field)
- No scrape history exists - only `last_scrape_date` on sources
- Manual triggers require shell access or navigating to queue_job admin
- All users see the same UI regardless of role

The codebase is an Odoo 18 addon using OCA queue_job for async processing.

## Goals / Non-Goals

**Goals:**
- Explicit article state tracking with error visibility
- Scrape history for both sources and articles
- Manual trigger capabilities within Odoo UI
- Pipeline monitoring dashboard for administrators
- Role-based access separating regular users from admin tools

**Non-Goals:**
- Real-time push notifications (polling is sufficient)
- Scrape scheduling customization per source
- Article content versioning (we only keep latest)
- Export/reporting features for scrape statistics

## Decisions

### 1. Article state as Selection field (not computed)

**Decision**: Store `state` as a Selection field, not computed from other fields.

**Alternatives considered**:
- Computed field based on `scrape_date` and content parsing → Rejected: Parsing content for `[Error:` is fragile, can't represent `skipped` state
- Separate boolean flags (`is_scraped`, `has_error`, `is_skipped`) → Rejected: Mutually exclusive states better represented as single selection

**Rationale**: Explicit state is clearer, supports the `skipped` manual state, and allows proper filtering/grouping.

### 2. Separate log models (not JSON field or chatter)

**Decision**: Create `news.source.log` and `news.article.log` models for scrape history.

**Alternatives considered**:
- JSON field storing array of attempts → Rejected: Hard to query, filter, or display in Odoo views
- Use mail.message/chatter → Rejected: Mixes operational logs with user communication, harder to structure

**Rationale**: Dedicated models allow proper list views, filtering, statistics queries, and clear retention policies later.

### 3. Async + polling for manual triggers

**Decision**: Manual trigger buttons queue a job and poll for completion.

**Alternatives considered**:
- Synchronous execution → Rejected: Scraping can take 60+ seconds, exceeds Odoo timeout
- Async with notification → Rejected: Notifications easy to miss, no completion feedback
- Longpolling/websocket → Rejected: Overkill, adds infrastructure complexity

**Rationale**: Polling every 2 seconds provides responsive UX without timeout issues. Queue_job handles retries consistently whether triggered manually or by cron.

**Implementation approach**:
- Button calls a method that creates queue_job and returns job UUID
- JavaScript controller polls `/queue_job/state/<uuid>` endpoint
- On completion, refresh the form/list view
- Show spinner during polling

### 4. Pipeline Monitor as dashboard view

**Decision**: Implement as Odoo dashboard with smart buttons linking to filtered views.

**Alternatives considered**:
- Custom controller/template → Rejected: More work, doesn't leverage Odoo's view system
- Separate menu items for each filter → Rejected: No unified overview

**Rationale**: Dashboard view with stat buttons is standard Odoo pattern (see CRM pipeline, Inventory dashboard). Users get counts at a glance and click to drill down.

### 5. Two groups: user and admin

**Decision**: `newsassistant_group_user` for basic access, `newsassistant_group_admin` (implies user) for debugging tools.

**Alternatives considered**:
- Single group with conditional field visibility → Rejected: Can't restrict menu items, server actions
- Three groups (user/operator/admin) → Rejected: Unnecessary complexity for this use case

**Rationale**: Two levels match the need: regular users work with articles, admins debug the pipeline. Admin implies user via Odoo's group inheritance.

### 6. View Full Log opens queue_job record

**Decision**: Link to existing queue_job form view rather than custom log display.

**Alternatives considered**:
- Inline expandable section → Rejected: queue_job records can be large, clutters form
- Modal popup with formatted log → Rejected: Additional UI work, queue_job view already exists

**Rationale**: Minimal effort, queue_job form has all details needed. Admin users are technical enough to navigate it.

### 7. Log models link to queue_job via Many2one

**Decision**: `news.source.log.job_id` and `news.article.log.job_id` are optional Many2one to `queue.job`.

**Rationale**: Allows "View Full Log" button when job record exists. Field is optional because jobs may be cleaned up by retention policy while logs remain.

## Risks / Trade-offs

**[Risk] Polling load** → Polling every 2s for multiple concurrent manual triggers could create load. Mitigation: Polling stops on completion/failure, typical use is single-source debugging not bulk.

**[Risk] Log table growth** → Scrape logs accumulate forever per proposal. Mitigation: Accepted for now; can add archival/retention later. Index on `source_id`/`article_id` + `timestamp DESC` for query performance.

**[Risk] Migration complexity** → Existing articles need initial state. Mitigation: Simple heuristic in migration: `scrape_date IS NULL` → pending, `content LIKE '[Error:%'` → error, else → scraped.

**[Risk] queue_job dependency for log link** → If queue_job records are deleted, log links break. Mitigation: Many2one with `ondelete='set null'`, UI handles missing job gracefully.

## Migration Plan

1. **Add new fields/models**: Article state fields, log models, security groups
2. **Data migration**: Set initial article states based on existing data
3. **Update scraping pipeline**: Record logs, set article state on completion
4. **Add UI elements**: Buttons, filters, dashboard (visibility controlled by groups)
5. **Rollback**: Remove new fields/models; existing scraping continues unaffected

No breaking changes to existing functionality. Pipeline continues working if migration partially fails.

## Open Questions

None - all decisions resolved during exploration.
