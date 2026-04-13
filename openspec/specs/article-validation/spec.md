### Requirement: Article content validation

Before extracting content from a fetched page, the system SHALL determine whether the content represents a single news article or blog post. The validation SHALL be performed by the LLM as part of the extraction prompt. The LLM SHALL classify content as NOT an article if it is: a listing/index page showing multiple articles, a category or topic overview page, a navigation page, a homepage, or any page without substantial article body text.

#### Scenario: Content is a single article

- **WHEN** the fetched content contains a single article with headline, publication date, and body text
- **THEN** the system SHALL classify it as an article
- **THEN** the system SHALL proceed with content extraction

#### Scenario: Content is a category listing page

- **WHEN** the fetched content is a category page listing multiple article links (e.g., "/themen/arbeit/news")
- **THEN** the system SHALL classify it as NOT an article
- **THEN** the system SHALL return `is_article: false` with reason "Category/index page listing multiple articles"

#### Scenario: Content is a navigation or overview page

- **WHEN** the fetched content is primarily navigation links or topic overview without article body
- **THEN** the system SHALL classify it as NOT an article
- **THEN** the system SHALL return `is_article: false` with reason explaining the page type

#### Scenario: Ambiguous content defaults to article

- **WHEN** the content structure is unclear but contains substantial prose text
- **THEN** the system SHALL classify it as an article to avoid false negatives

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
