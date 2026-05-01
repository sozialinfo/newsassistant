## ADDED Requirements

### Requirement: Log smart button on news source form
The `news.source` form view SHALL display a smart button showing the count of log entries for the source. The button SHALL navigate to the `news.log` list view filtered by `source_id`. The button SHALL only be visible to users in the `newsassistant_group_admin` group.

#### Scenario: Log smart button shows count and navigates
- **WHEN** an admin opens a news source form
- **THEN** a smart button labeled "Logs" SHALL appear with the log count
- **WHEN** the admin clicks the Logs button
- **THEN** the system SHALL open the `news.log` list filtered to show only logs for this source

#### Scenario: Log smart button hidden from regular users
- **WHEN** a non-admin user opens a news source form
- **THEN** the Logs smart button SHALL NOT be visible

### Requirement: Snapshot smart button on news source form
The `news.source` form view SHALL display a smart button showing the count of snapshots for the source. The button SHALL navigate to the `news.snapshot` list view filtered by `source_id`. The button SHALL be visible to all users.

#### Scenario: Snapshot smart button shows count and navigates
- **WHEN** a user opens a news source form
- **THEN** a smart button labeled "Snapshots" SHALL appear with the snapshot count
- **WHEN** the user clicks the Snapshots button
- **THEN** the system SHALL open the `news.snapshot` list filtered to show only snapshots for this source

### Requirement: Active jobs smart button on news source form
The `news.source` form view SHALL display a smart button showing the count of active queue jobs (state in `pending`, `enqueued`, `started`) for the source. The button SHALL only be visible when the count is greater than zero AND the user is a system administrator (`base.group_system`). The button SHALL navigate to the `queue.job` list filtered to those specific jobs.

#### Scenario: Active jobs button hidden when no jobs
- **WHEN** there are no active queue jobs for this source
- **THEN** the Active Jobs smart button SHALL NOT be visible

#### Scenario: Active jobs button visible when jobs are running
- **WHEN** a system administrator opens a source form with 1 or more active queue jobs
- **THEN** the Active Jobs smart button SHALL be visible with the job count

#### Scenario: Active jobs button navigates to filtered job list
- **WHEN** a system administrator clicks the Active Jobs button
- **THEN** the system SHALL open the `queue.job` list showing only the active jobs for this source

### Requirement: Inline tabs removed from news source form
The `news.source` form view SHALL NOT contain an inline Snapshots tab or inline Log tab in a notebook. These are replaced by the smart buttons above.

#### Scenario: No notebook on source form
- **WHEN** a user opens any news source form
- **THEN** the form SHALL NOT contain a notebook with Snapshots or Log pages
