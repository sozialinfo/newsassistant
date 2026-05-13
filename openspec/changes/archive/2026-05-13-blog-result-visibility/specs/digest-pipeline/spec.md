## MODIFIED Requirements

### Requirement: Three-way relevance decision
The system SHALL evaluate each article against the content strategy prompt and return one of three decisions: `relevant`, `uncertain`, or `discard`. The `blog_reasoning` field SHALL be stored for all three decisions. Uncertain articles SHALL be moved to the configured Shortlist stage. Relevant articles SHALL skip the Shortlist stage and be moved directly to Published after blog post creation.

#### Scenario: Article marked as relevant
- **WHEN** the AI determines an article matches the content strategy criteria for "highly relevant"
- **THEN** the decision SHALL be `relevant`
- **THEN** the article SHALL proceed to teaser generation and blog post creation
- **THEN** `blog_reasoning` SHALL be stored with the AI's explanation
- **THEN** the article SHALL be moved directly to the Published stage (NOT via Shortlist)

#### Scenario: Article marked as uncertain
- **WHEN** the AI determines an article partially matches or is unclear
- **THEN** the decision SHALL be `uncertain`
- **THEN** `blog_reasoning` SHALL be stored with the AI's explanation
- **THEN** the article SHALL be moved to the configured Shortlist stage for human review
- **THEN** no teaser SHALL be generated

#### Scenario: Article marked as discard
- **WHEN** the AI determines an article does not match the content strategy
- **THEN** the decision SHALL be `discard`
- **THEN** `blog_reasoning` SHALL be stored with the AI's explanation
- **THEN** the article SHALL be moved to the configured Discarded stage
- **THEN** no teaser SHALL be generated
