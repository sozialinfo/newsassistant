## ADDED Requirements

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
