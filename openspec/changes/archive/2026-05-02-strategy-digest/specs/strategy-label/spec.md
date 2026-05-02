## ADDED Requirements

### Requirement: Strategy label model
The system SHALL provide a `strategy.label` model with fields: `name` (Char, required, translatable), `color` (Integer, default random 1–11). The model SHALL enforce uniqueness on `name`. Admin users SHALL be able to manage labels via Configuration → Strategy Labels.

#### Scenario: Create a strategy label
- **WHEN** an admin navigates to Configuration → Strategy Labels and creates a label "Innovation"
- **THEN** a `strategy.label` record SHALL be created with the given name
- **THEN** a colour SHALL be assigned (random default if not chosen)

#### Scenario: Duplicate label name is rejected
- **WHEN** an admin attempts to create a second label with an already-used name
- **THEN** the system SHALL raise a validation error
- **THEN** the duplicate record SHALL NOT be saved

#### Scenario: Non-admin cannot manage labels
- **WHEN** a regular user (without admin rights) attempts to create or delete a strategy label
- **THEN** the system SHALL deny the operation

### Requirement: Strategy label field on news.article
The system SHALL add a Many2many field `strategy_label_ids` (→ `strategy.label`) to `news.article` via model inheritance. Users SHALL be able to manually assign or remove labels on the article form view. The field SHALL also be editable inline in the list view.

#### Scenario: Assign label to article manually
- **WHEN** a user opens an article form and selects one or more strategy labels
- **THEN** the article's `strategy_label_ids` SHALL be updated to reflect the selection

#### Scenario: Article can have multiple labels
- **WHEN** a user assigns two different strategy labels to the same article
- **THEN** both labels SHALL be stored on the article
- **THEN** both labels SHALL be visible on the kanban card as colour chips

#### Scenario: Label chips visible on kanban card
- **WHEN** an article has one or more strategy labels assigned
- **THEN** the kanban card SHALL display coloured chips for each assigned label

### Requirement: Strategy label filter in article search
The system SHALL add a filter and groupby option for `strategy_label_ids` in the article search bar. Users SHALL be able to filter articles to show only those with a specific strategy label.

#### Scenario: Filter articles by strategy label
- **WHEN** a user selects a strategy label in the search bar filter
- **THEN** only articles that have that label assigned SHALL be displayed
- **THEN** articles without that label SHALL be hidden

#### Scenario: Filter by multiple labels (OR logic)
- **WHEN** a user selects two strategy labels in the search bar
- **THEN** articles that have ANY of the selected labels SHALL be displayed
