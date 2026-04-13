## ADDED Requirements

### Requirement: Teaser field on articles
The system SHALL extend `news.article` with a `teaser` field (Text) to store the AI-generated teaser for relevant articles.

#### Scenario: Relevant article has teaser
- **WHEN** an article is marked as `relevant` by the digest pipeline
- **THEN** the system SHALL generate a teaser and store it in the `teaser` field

#### Scenario: Non-relevant article has no teaser
- **WHEN** an article is marked as `uncertain` or `discard`
- **THEN** the `teaser` field SHALL remain empty

### Requirement: Teaser generation via AI
The system SHALL generate teasers using a separate LLM call with the teaser prompt from system parameters. The teaser prompt SHALL be configurable independently from the content strategy prompt.

#### Scenario: Teaser generated with configured prompt
- **WHEN** the system generates a teaser for a relevant article
- **THEN** the system SHALL use the prompt from `newsfeed.teaser_prompt` system parameter
- **THEN** the system SHALL pass the article title, summary, and content to the LLM

#### Scenario: Teaser generation uses higher temperature
- **WHEN** the system calls the LLM for teaser generation
- **THEN** the temperature SHALL be higher than the relevance scoring call (creative output)

### Requirement: Teaser content format
The system SHALL generate teasers as plain text suitable for blog post content. Teasers SHALL be concise (2-4 sentences) and encourage readers to click through to the source.

#### Scenario: Teaser is concise
- **WHEN** a teaser is generated
- **THEN** the teaser SHALL be 2-4 sentences summarizing the article's key point

#### Scenario: Teaser includes call to action
- **WHEN** a teaser is generated
- **THEN** the teaser content (combined with blog post template) SHALL encourage reading the full article at the source

### Requirement: Teaser generation failure handling
The system SHALL handle teaser generation failures gracefully. If teaser generation fails, the article SHALL still be marked as relevant but without a blog post.

#### Scenario: Teaser generation fails
- **WHEN** the LLM call for teaser generation fails
- **THEN** the article SHALL be marked as `relevant` in the kanban
- **THEN** the `digest_state` SHALL be `processed`
- **THEN** no blog post SHALL be created
- **THEN** an error SHALL be logged with category `digest`
