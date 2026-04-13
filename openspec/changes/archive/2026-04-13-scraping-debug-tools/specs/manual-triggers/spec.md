## ADDED Requirements

### Requirement: Scrape Now button on source form

The source form view SHALL display a "Scrape Now" button visible to admin group only. Clicking it SHALL queue a listing scrape job for that source.

#### Scenario: Admin triggers manual scrape

- **WHEN** an admin clicks "Scrape Now" on a source form
- **THEN** a queue job SHALL be created for `_scrape_listing()`
- **THEN** the UI SHALL show a loading indicator

#### Scenario: Scrape Now button visibility

- **WHEN** a regular user views a source form
- **THEN** the "Scrape Now" button SHALL NOT be visible

### Requirement: Re-fetch button on article form

The article form view SHALL display a "Re-fetch" button visible to admin group only. Clicking it SHALL queue an extraction job for that article.

#### Scenario: Admin triggers manual re-fetch

- **WHEN** an admin clicks "Re-fetch" on an article form
- **THEN** a queue job SHALL be created for `_fetch_and_extract()`
- **THEN** the UI SHALL show a loading indicator

#### Scenario: Re-fetch available for all non-skipped states

- **WHEN** an admin views an article in `pending`, `scraped`, or `error` state
- **THEN** the "Re-fetch" button SHALL be visible

#### Scenario: Re-fetch not available for skipped

- **WHEN** an admin views an article in `skipped` state
- **THEN** the "Re-fetch" button SHALL NOT be visible (use Reset first)

### Requirement: Async polling for manual triggers

When a manual trigger button is clicked, the UI SHALL poll for job completion every 2 seconds. On completion, the view SHALL refresh to show updated state.

#### Scenario: Successful scrape completion

- **WHEN** an admin clicks "Scrape Now" and the job completes successfully
- **THEN** the UI SHALL stop polling
- **THEN** the source form SHALL refresh showing updated `last_scrape_date` and any new articles

#### Scenario: Failed scrape completion

- **WHEN** an admin clicks "Scrape Now" and the job fails permanently
- **THEN** the UI SHALL stop polling
- **THEN** the source form SHALL refresh showing `state='error'` and error details

#### Scenario: Job still running

- **WHEN** an admin clicks "Scrape Now" and the job is still running after 2 seconds
- **THEN** the UI SHALL continue polling
- **THEN** the loading indicator SHALL remain visible

### Requirement: Bulk scrape server action

The source list view SHALL provide a server action "Scrape Selected" visible to admin group only. It SHALL queue scrape jobs for all selected sources.

#### Scenario: Bulk scrape multiple sources

- **WHEN** an admin selects 3 sources and runs "Scrape Selected"
- **THEN** 3 queue jobs SHALL be created, one per source
- **THEN** a confirmation message SHALL indicate jobs were queued

#### Scenario: Bulk action visibility

- **WHEN** a regular user views source list actions
- **THEN** the "Scrape Selected" action SHALL NOT be available

### Requirement: Bulk re-fetch server action

The article list view SHALL provide a server action "Re-fetch Selected" visible to admin group only. It SHALL queue extraction jobs for all selected articles that are not in `skipped` state.

#### Scenario: Bulk re-fetch multiple articles

- **WHEN** an admin selects 5 articles (3 error, 1 pending, 1 skipped) and runs "Re-fetch Selected"
- **THEN** 4 queue jobs SHALL be created (skipped article excluded)
- **THEN** a confirmation message SHALL indicate how many jobs were queued

### Requirement: Bulk skip server action

The article list view SHALL provide a server action "Mark as Skipped" visible to admin group only. It SHALL set `state='skipped'` on all selected articles.

#### Scenario: Bulk skip error articles

- **WHEN** an admin selects 3 error articles and runs "Mark as Skipped"
- **THEN** all 3 articles SHALL have `state='skipped'`

### Requirement: Bulk reset server action

The article list view SHALL provide a server action "Reset to Pending" visible to admin group only. It SHALL reset all selected articles to pending state (clear errors, reset retry count).

#### Scenario: Bulk reset skipped articles

- **WHEN** an admin selects 2 skipped articles and runs "Reset to Pending"
- **THEN** both articles SHALL have `state='pending'`
- **THEN** `error_message`, `last_error_date` SHALL be cleared
- **THEN** `retry_count` SHALL be reset to 0
