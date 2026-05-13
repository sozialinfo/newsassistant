## MODIFIED Requirements

### Requirement: Kanban header image layout

The article kanban view SHALL display the header image as a small square (64x64 pixels) in the top-right corner of the card, using the Odoo 18 flex-row card pattern.

#### Scenario: Article with header image in kanban
- **WHEN** viewing articles in kanban view where an article has a header image
- **THEN** the image SHALL appear as a small square on the right side of the card content

#### Scenario: Article without header image in kanban
- **WHEN** viewing articles in kanban view where an article has no header image
- **THEN** the card SHALL display only the text content without an image placeholder

### Requirement: Form view header layout

The article form view SHALL display all metadata fields (source, date, URL, scrape date) in the left column of the header group, with the header image alone in the right column without a label.

#### Scenario: Article with header image in form view
- **WHEN** viewing an article form with a header image
- **THEN** all metadata fields SHALL appear in the left column and the image SHALL appear in the right column without a label

#### Scenario: Article without header image in form view
- **WHEN** viewing an article form without a header image
- **THEN** all metadata fields SHALL appear in the left column and the right column SHALL remain empty

### Requirement: Unified Blog and Strategy tab pattern
The Blog tab and the Strategy tab in the article form view SHALL follow an identical UI pattern: an evaluation status badge and re-trigger button shown side-by-side, followed by a Reasoning block, followed by a result block. The evaluation status field label, the reasoning field label, and the button visibility rule SHALL be identical in both tabs. Only the result block differs (teaser text for Blog; label tags for Strategy).

#### Scenario: Evaluation status badge uses the same label in both tabs
- **WHEN** a user opens the Blog tab or the Strategy tab
- **THEN** the evaluation status field SHALL be labelled "Evaluation Status" in both tabs

#### Scenario: Reasoning block uses the same label in both tabs
- **WHEN** reasoning text is present
- **THEN** the group heading SHALL read "Reasoning" in both the Blog tab and the Strategy tab

#### Scenario: Evaluate button hidden when article is not scraped
- **WHEN** an article has `state != 'scraped'`
- **THEN** the Evaluate button SHALL NOT be visible in either the Blog tab or the Strategy tab

#### Scenario: Evaluate button visible when article is scraped
- **WHEN** an article has `state == 'scraped'`
- **THEN** the Evaluate button SHALL be visible in both the Blog tab and the Strategy tab
