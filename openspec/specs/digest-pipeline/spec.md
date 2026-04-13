## ADDED Requirements

### Requirement: Digest state tracking on articles
The system SHALL extend `news.article` with a `digest_state` field (Selection: `pending`, `processed`) defaulting to `pending`. This field SHALL track whether the digest pipeline has processed the article.

#### Scenario: New article has pending digest state
- **WHEN** a new `news.article` is created by the scraping pipeline
- **THEN** the `digest_state` SHALL be `pending`

#### Scenario: Processed article has processed digest state
- **WHEN** the digest pipeline finishes processing an article (regardless of decision)
- **THEN** the `digest_state` SHALL be `processed`

### Requirement: Digest cron job
The system SHALL provide a scheduled action "Newsfeed: Process Digest" that runs daily by default. The cron SHALL call `_cron_digest_all()` on the `news.article` model.

#### Scenario: Cron triggers digest processing
- **WHEN** the digest cron job runs
- **THEN** the system SHALL find all articles where `state = 'scraped'` AND `digest_state = 'pending'`
- **THEN** the system SHALL queue one `_digest_article()` job per article

#### Scenario: Only scraped articles are processed
- **WHEN** an article has `state = 'error'` or `state = 'pending'`
- **THEN** the digest cron SHALL NOT process that article

### Requirement: Queue-based digest processing
The system SHALL process each article as a separate queue job using the existing `queue_job` infrastructure. Jobs SHALL use channel `root.newsassistant`.

#### Scenario: Digest jobs are queued
- **WHEN** the digest cron finds 10 unprocessed articles
- **THEN** the system SHALL create 10 separate queue jobs
- **THEN** jobs SHALL run in parallel up to the channel concurrency limit

#### Scenario: Failed job can be retried
- **WHEN** a digest job fails due to transient error (timeout, API rate limit)
- **THEN** the job SHALL be retried according to queue_job retry policy

### Requirement: Three-way relevance decision
The system SHALL evaluate each article against the content strategy prompt and return one of three decisions: `relevant`, `uncertain`, or `discard`.

#### Scenario: Article marked as relevant
- **WHEN** the AI determines an article matches the content strategy criteria for "highly relevant"
- **THEN** the decision SHALL be `relevant`
- **THEN** the article SHALL proceed to teaser generation

#### Scenario: Article marked as uncertain
- **WHEN** the AI determines an article partially matches or is unclear
- **THEN** the decision SHALL be `uncertain`
- **THEN** the article SHALL remain in the "New" stage for human review
- **THEN** no teaser SHALL be generated

#### Scenario: Article marked as discard
- **WHEN** the AI determines an article does not match the content strategy
- **THEN** the decision SHALL be `discard`
- **THEN** the article SHALL be moved to the "Discarded" stage
- **THEN** no teaser SHALL be generated

### Requirement: Digest logging
The system SHALL log digest processing results using the existing `news.log` model with category `digest`. Logs SHALL include the AI decision and reasoning.

#### Scenario: Successful digest logged
- **WHEN** an article is successfully processed by the digest
- **THEN** a `news.log` entry SHALL be created with level `success` and category `digest`
- **THEN** log entries SHALL include the decision and reasoning from the AI

#### Scenario: Failed digest logged
- **WHEN** digest processing fails for an article
- **THEN** a `news.log` entry SHALL be created with level `error` and category `digest`
- **THEN** the error details SHALL be recorded
