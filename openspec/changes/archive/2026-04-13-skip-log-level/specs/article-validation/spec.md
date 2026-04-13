## MODIFIED Requirements

### Requirement: Non-article handling

When validation determines content is NOT an article, the system SHALL mark the article stub as `skipped` with the `error_message` field set to the validation reason. The stub SHALL remain in the database to prevent the URL from being re-discovered in future scrapes.

#### Scenario: Non-article marked as skipped

- **WHEN** validation returns `is_article: false` with reason "Category/index page"
- **THEN** the article `state` SHALL be set to `skipped`
- **THEN** the article `error_message` SHALL be set to "Not an article: Category/index page"
- **THEN** the article `scrape_date` SHALL be set to current timestamp

#### Scenario: Skipped article prevents re-discovery

- **WHEN** a future listing scrape discovers the same URL
- **THEN** the system SHALL skip it due to existing `news.article` record (normal deduplication)
- **THEN** no new stub SHALL be created

#### Scenario: Non-article creates log entry

- **WHEN** an article is marked as skipped due to validation
- **THEN** a `news.log` record SHALL be created with level `info` and category `extraction`
- **THEN** the log message SHALL indicate the URL was not an article
