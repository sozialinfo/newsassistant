## ADDED Requirements

### Requirement: Article state field

The `news.article` model SHALL have a `state` Selection field with values: `pending` (default), `scraped`, `error`, `skipped`. The field SHALL be readonly in the UI.

#### Scenario: New article defaults to pending

- **WHEN** a new `news.article` record is created during Stage 1 listing discovery
- **THEN** the `state` field SHALL be `pending`

#### Scenario: State displayed in article form

- **WHEN** a user views an article form
- **THEN** the `state` field SHALL be visible as a status badge
- **THEN** the field SHALL NOT be editable

### Requirement: Article error tracking fields

The `news.article` model SHALL have fields: `error_message` (Text), `retry_count` (Integer, default 0), `last_error_date` (Datetime). These fields SHALL be readonly in the UI.

#### Scenario: Error fields visible on article form

- **WHEN** an article is in `error` state
- **THEN** the `error_message`, `retry_count`, and `last_error_date` fields SHALL be displayed

#### Scenario: Error fields hidden when no error

- **WHEN** an article is in `pending` or `scraped` state
- **THEN** the error details section SHALL be hidden or collapsed

### Requirement: State transition on successful extraction

When article extraction succeeds, the system SHALL set `state` to `scraped`, clear `error_message`, clear `last_error_date`, and keep `retry_count` unchanged.

#### Scenario: Pending article successfully extracted

- **WHEN** a `pending` article is successfully extracted
- **THEN** `state` SHALL be `scraped`
- **THEN** `error_message` SHALL be empty
- **THEN** `last_error_date` SHALL be empty

#### Scenario: Error article re-fetch succeeds

- **WHEN** an `error` article with `retry_count=3` is successfully re-fetched
- **THEN** `state` SHALL be `scraped`
- **THEN** `error_message` SHALL be empty
- **THEN** `retry_count` SHALL remain `3`

### Requirement: State transition on failed extraction

When article extraction fails, the system SHALL set `state` to `error`, set `error_message` to describe the failure, set `last_error_date` to current timestamp, and increment `retry_count` by 1.

#### Scenario: Extraction fails with HTTP error

- **WHEN** article extraction fails due to HTTP 404
- **THEN** `state` SHALL be `error`
- **THEN** `error_message` SHALL contain "404" or similar description
- **THEN** `last_error_date` SHALL be the current timestamp
- **THEN** `retry_count` SHALL be incremented by 1

#### Scenario: Extraction fails with parse error

- **WHEN** article extraction fails because AI returned invalid JSON
- **THEN** `state` SHALL be `error`
- **THEN** `error_message` SHALL describe the parse failure

### Requirement: Manual skip action

Users with admin group SHALL be able to mark an article as `skipped`. This SHALL set `state` to `skipped` and preserve error fields.

#### Scenario: Admin skips error article

- **WHEN** an admin clicks "Skip" on an article in `error` state
- **THEN** `state` SHALL be `skipped`
- **THEN** `error_message` and `retry_count` SHALL be preserved

#### Scenario: Skip button visibility

- **WHEN** a regular user views an article form
- **THEN** the "Skip" button SHALL NOT be visible

### Requirement: Manual reset action

Users with admin group SHALL be able to reset a `skipped` article to `pending`. This SHALL set `state` to `pending`, clear `error_message`, clear `last_error_date`, and reset `retry_count` to 0.

#### Scenario: Admin resets skipped article

- **WHEN** an admin clicks "Reset" on an article in `skipped` state
- **THEN** `state` SHALL be `pending`
- **THEN** `error_message` SHALL be empty
- **THEN** `retry_count` SHALL be `0`
- **THEN** `last_error_date` SHALL be empty

#### Scenario: Reset button only for skipped

- **WHEN** an article is in `error` state
- **THEN** the "Reset" button SHALL NOT be visible (use "Re-fetch" instead)

### Requirement: Article state filters

The article list view SHALL have filters for each state: Pending, Scraped, Error, Skipped. These filters SHALL be visible to all users.

#### Scenario: Filter articles by error state

- **WHEN** a user selects the "Error" filter in article list
- **THEN** only articles with `state='error'` SHALL be displayed

#### Scenario: Filter articles by pending state

- **WHEN** a user selects the "Pending" filter in article list
- **THEN** only articles with `state='pending'` SHALL be displayed

### Requirement: Article state badge in list view

The article list view SHALL display the `state` field as a colored badge.

#### Scenario: State badge colors

- **WHEN** viewing the article list
- **THEN** `pending` articles SHALL show a neutral/gray badge
- **THEN** `scraped` articles SHALL show a success/green badge
- **THEN** `error` articles SHALL show a danger/red badge
- **THEN** `skipped` articles SHALL show a muted/gray badge
