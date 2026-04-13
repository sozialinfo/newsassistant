## MODIFIED Requirements

### Requirement: News source form view

The system SHALL provide a form view for `news.source` allowing editing of name, url, and active flag, with read-only display of state, last_scrape_date, error_message, and a list of related articles. For users in admin group, the form SHALL also display a "Scrape Now" button, a "Scrape Status" section showing last job details (status, retries, next retry time, error), and a "Scrape History" section showing the last 10 log entries.

#### Scenario: Edit a news source

- **WHEN** the user opens a news source form
- **THEN** the user SHALL be able to edit name, url, and active flag
- **THEN** state, last_scrape_date, and error_message SHALL be read-only

#### Scenario: Admin sees scrape controls

- **WHEN** an admin opens a news source form
- **THEN** the "Scrape Now" button SHALL be visible in the form header
- **THEN** the "Scrape Status" section SHALL be visible showing last job information
- **THEN** the "Scrape History" section SHALL be visible showing recent log entries

#### Scenario: User does not see scrape controls

- **WHEN** a regular user opens a news source form
- **THEN** the "Scrape Now" button SHALL NOT be visible
- **THEN** the "Scrape Status" section SHALL NOT be visible
- **THEN** the "Scrape History" section SHALL NOT be visible

## ADDED Requirements

### Requirement: Source list filters for scrape status

The source list view search SHALL include filters: "Has Errors" (state=error), "Never Scraped" (last_scrape_date is empty), "Stale" (last_scrape_date older than 7 days).

#### Scenario: Filter sources with errors

- **WHEN** a user selects the "Has Errors" filter
- **THEN** only sources with `state='error'` SHALL be displayed

#### Scenario: Filter never scraped sources

- **WHEN** a user selects the "Never Scraped" filter
- **THEN** only sources where `last_scrape_date` is empty SHALL be displayed

#### Scenario: Filter stale sources

- **WHEN** a user selects the "Stale" filter and today is April 12
- **THEN** only sources where `last_scrape_date` is before April 5 SHALL be displayed
