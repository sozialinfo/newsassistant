## MODIFIED Requirements

### Requirement: Article date is required with today as default
The `news.article.date` field SHALL be `required=True` with `default=fields.Date.today`. The AI extraction pipeline SHALL also default to today's date when the AI returns no publication date. This is a UI-level constraint only (no DB NOT NULL).

#### Scenario: New article created via GUI has today's date prefilled
- **WHEN** a user opens the New article form
- **THEN** the `date` field SHALL be prefilled with today's date

#### Scenario: AI extraction without date falls back to today
- **WHEN** the AI extraction returns `"date": null` for an article
- **THEN** the article SHALL be created with `date` set to today

#### Scenario: AI extraction with a valid date preserves it
- **WHEN** the AI extraction returns `"date": "2026-04-01"` for an article
- **THEN** the article SHALL be created with `date = 2026-04-01`

### Requirement: Article form has snapshot SmartButton (admin only)
The article form view SHALL display an admin-only SmartButton in the `button_box` that shows the related snapshot count (0 or 1) and navigates to the snapshot form when clicked.

#### Scenario: Article with snapshot shows SmartButton
- **WHEN** an admin opens an article form that has a linked snapshot
- **THEN** a SmartButton labelled "Snapshot" with count 1 SHALL be visible in the button box

#### Scenario: Article without snapshot hides SmartButton
- **WHEN** an admin opens an article form with no snapshot linked
- **THEN** the snapshot SmartButton SHALL NOT be visible

#### Scenario: SmartButton navigates to snapshot
- **WHEN** an admin clicks the snapshot SmartButton
- **THEN** the snapshot form for the linked snapshot SHALL open

#### Scenario: Non-admin cannot see SmartButton
- **WHEN** a regular user opens an article form
- **THEN** the snapshot SmartButton SHALL NOT be visible

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
The Blog tab and the Strategy tab in the article form view SHALL follow an identical UI pattern: an evaluation status badge and re-trigger button shown side-by-side, followed by a Reasoning block, followed by a result block.

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
