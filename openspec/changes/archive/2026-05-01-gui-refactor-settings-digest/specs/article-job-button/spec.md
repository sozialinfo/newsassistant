## ADDED Requirements

### Requirement: Active jobs smart button on news article form
The `news.article` form view SHALL display a smart button showing the count of active queue jobs (state in `pending`, `enqueued`, `started`) for the article. The button SHALL only be visible when the count is greater than zero AND the user is a system administrator (`base.group_system`). The button SHALL navigate to the `queue.job` list filtered to those specific jobs.

#### Scenario: Active jobs button hidden when no jobs
- **WHEN** there are no active queue jobs for this article
- **THEN** the Active Jobs smart button SHALL NOT be visible

#### Scenario: Active jobs button visible when jobs are running
- **WHEN** a system administrator opens an article form with 1 or more active queue jobs
- **THEN** the Active Jobs smart button SHALL be visible with the job count

#### Scenario: Active jobs button navigates to filtered job list
- **WHEN** a system administrator clicks the Active Jobs button
- **THEN** the system SHALL open the `queue.job` list showing only the active jobs for this article

#### Scenario: Active jobs button not visible to non-admins
- **WHEN** a non-system-administrator opens an article form (even with active jobs)
- **THEN** the Active Jobs smart button SHALL NOT be visible
