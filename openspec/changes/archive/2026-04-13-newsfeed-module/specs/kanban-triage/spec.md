## MODIFIED Requirements

### Requirement: Kanban view for articles
The system SHALL provide a kanban view for `news.article` grouped by `stage_id`. Each kanban card SHALL display: title (bold/prominent), source name, article date, and a truncated summary (first ~200 characters). Users SHALL be able to drag cards between stages. Additionally, cards for articles with `digest_state = 'processed'` MAY display an indicator showing the digest decision.

#### Scenario: View articles in kanban
- **WHEN** the user navigates to the News Articles menu
- **THEN** articles SHALL be displayed in a kanban view grouped by stage
- **THEN** each card SHALL show title, source name, date, and truncated summary

#### Scenario: Drag article to different stage
- **WHEN** the user drags an article card from "New" to "Relevant"
- **THEN** the article's `stage_id` SHALL be updated to "Relevant"

#### Scenario: Digest moves article to Relevant
- **WHEN** the digest pipeline marks an article as `relevant`
- **THEN** the article's `stage_id` SHALL be automatically updated to the "Relevant" stage

#### Scenario: Digest moves article to Discarded
- **WHEN** the digest pipeline marks an article as `discard`
- **THEN** the article's `stage_id` SHALL be automatically updated to the "Discarded" stage

#### Scenario: Uncertain articles stay in New
- **WHEN** the digest pipeline marks an article as `uncertain`
- **THEN** the article's `stage_id` SHALL remain in the "New" stage
- **THEN** humans can review and manually move the article

#### Scenario: Human can override digest decision
- **WHEN** the digest has moved an article to "Discarded"
- **THEN** a human user SHALL be able to drag the article to "Relevant" or another stage
- **THEN** manual stage changes SHALL override the digest decision
