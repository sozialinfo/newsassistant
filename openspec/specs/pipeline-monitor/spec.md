## ADDED Requirements

### Requirement: Pipeline Monitor menu item

The News Assistant menu SHALL include a "Pipeline Monitor" menu item visible to admin group only. It SHALL open the Pipeline Monitor dashboard.

#### Scenario: Admin sees Pipeline Monitor menu

- **WHEN** an admin opens the News Assistant menu
- **THEN** "Pipeline Monitor" SHALL be visible as a menu item

#### Scenario: Regular user does not see Pipeline Monitor

- **WHEN** a regular user opens the News Assistant menu
- **THEN** "Pipeline Monitor" SHALL NOT be visible

### Requirement: Pipeline Monitor dashboard

The Pipeline Monitor SHALL be a dashboard view displaying summary statistics and quick links to filtered views.

#### Scenario: Dashboard displays counts

- **WHEN** an admin opens the Pipeline Monitor
- **THEN** the dashboard SHALL display counts for:
  - Sources with errors
  - Articles pending extraction
  - Articles with errors
  - Recent failed jobs (last 24 hours)

### Requirement: Sources with errors stat button

The Pipeline Monitor SHALL display a stat button showing count of sources with `state='error'`. Clicking it SHALL open the source list filtered to error state.

#### Scenario: Click sources with errors

- **WHEN** an admin clicks the "Sources with Errors" stat button showing count "3"
- **THEN** the source list SHALL open filtered to `state='error'`
- **THEN** 3 sources SHALL be displayed

### Requirement: Articles pending stat button

The Pipeline Monitor SHALL display a stat button showing count of articles with `state='pending'`. Clicking it SHALL open the article list filtered to pending state.

#### Scenario: Click articles pending

- **WHEN** an admin clicks the "Articles Pending" stat button
- **THEN** the article list SHALL open filtered to `state='pending'`

### Requirement: Articles with errors stat button

The Pipeline Monitor SHALL display a stat button showing count of articles with `state='error'`. Clicking it SHALL open the article list filtered to error state.

#### Scenario: Click articles with errors

- **WHEN** an admin clicks the "Articles with Errors" stat button
- **THEN** the article list SHALL open filtered to `state='error'`

### Requirement: Recent failures table

The Pipeline Monitor SHALL display a table of recent job failures (last 24 hours) showing: Source/Article name, Type (listing/article), Time, Error message.

#### Scenario: View recent failures

- **WHEN** an admin views the Pipeline Monitor and 5 jobs failed in the last 24 hours
- **THEN** the recent failures table SHALL show 5 rows
- **THEN** each row SHALL show the related source or article name, job type, failure time, and error summary

#### Scenario: No recent failures

- **WHEN** no jobs have failed in the last 24 hours
- **THEN** the recent failures table SHALL show a message "No recent failures"

#### Scenario: Click failure row

- **WHEN** an admin clicks a row in the recent failures table
- **THEN** the related source or article form SHALL open

### Requirement: Dashboard refresh

The Pipeline Monitor dashboard counts SHALL reflect current data when opened. The dashboard MAY provide a manual refresh button.

#### Scenario: Dashboard shows current counts

- **WHEN** an admin opens the Pipeline Monitor
- **THEN** all counts SHALL reflect the current database state
