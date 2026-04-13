## Why

The current scraping pipeline lacks visibility into failures and provides no way to manually trigger scrapes for debugging. When articles fail to extract or sources encounter errors, diagnosing issues requires digging through queue_job records and inferring state from implicit markers (like `[Error:` prefixes in content). Operators need tools to monitor pipeline health, identify failures quickly, and manually re-trigger scrapes without resorting to shell commands.

## What Changes

- Add explicit `state` field to articles (`pending`, `scraped`, `error`, `skipped`) with `error_message`, `retry_count`, and `last_error_date` fields
- Add scrape history logging for both sources and articles (new models: `news.source.log`, `news.article.log`)
- Add manual trigger buttons on source and article forms ("Scrape Now", "Re-fetch", "Skip", "Reset")
- Add bulk actions on list views for multi-select operations
- Add "Pipeline Monitor" dashboard showing error counts and recent failures
- Add state/error filters to source and article list views
- Implement async polling UI pattern for manual triggers (queue job, poll for completion, refresh view)
- Add two security groups: `newsassistant_group_user` (basic access) and `newsassistant_group_admin` (debugging tools)

## Capabilities

### New Capabilities

- `article-state-tracking`: Explicit state machine for articles (pending/scraped/error/skipped) with error tracking fields and state transitions
- `scrape-history`: Log models for source and article scrape attempts, with timestamp, status, duration, error details, and job links
- `manual-triggers`: Buttons and server actions to manually trigger scrapes, with async polling UI for feedback
- `pipeline-monitor`: Dashboard view showing error counts, pending articles, and recent failures (admin-only)
- `debug-roles`: Security groups separating regular users from pipeline administrators

### Modified Capabilities

- `scraping-pipeline`: Update to record scrape history logs and set article state on success/failure
- `source-management`: Add "Scrape Now" button to source form, show scrape history section for admins

## Impact

- **Models**: New fields on `news.article`, new models `news.source.log` and `news.article.log`
- **Views**: Modified source/article forms and lists, new Pipeline Monitor dashboard
- **Security**: New groups and access rules, conditional UI visibility based on group membership
- **Queue jobs**: Manual trigger jobs follow same retry policy as scheduled jobs
- **Existing data**: Migration needed to set initial `state` on existing articles based on current implicit state
