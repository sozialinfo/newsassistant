## ADDED Requirements

### Requirement: Article stage model
The system SHALL provide a `news.article.stage` model with fields: `name` (Char, required, translatable), `sequence` (Integer), and `fold` (Boolean, default False). Default stages SHALL be created via data XML: New (sequence 10, not folded), Shortlist (sequence 20, not folded), Published (sequence 30, folded), Discarded (sequence 40, folded).

#### Scenario: Default stages exist after install
- **WHEN** the module is installed
- **THEN** four stages SHALL exist: New, Shortlist, Published, Discarded
- **THEN** stages SHALL be ordered by sequence

#### Scenario: Published and Discarded are folded
- **WHEN** the kanban view is rendered
- **THEN** the Published and Discarded columns SHALL be folded by default

#### Scenario: New and Shortlist are not folded
- **WHEN** the kanban view is rendered
- **THEN** the New and Shortlist columns SHALL be visible (not folded)

### Requirement: Stage list view

The system SHALL provide a list view for `news.article.stage` model displaying: name, sequence, and fold status. The list SHALL be editable inline. Records SHALL be ordered by sequence.

#### Scenario: View all stages
- **WHEN** admin navigates to Configuration → Article Stages
- **THEN** all stages SHALL be displayed in a list ordered by sequence
- **THEN** the list SHALL show name, sequence, and fold columns

#### Scenario: Edit stage inline
- **WHEN** admin edits a stage name directly in the list
- **THEN** the change SHALL be saved immediately

### Requirement: Stage form view

The system SHALL provide a form view for `news.article.stage` with fields: name, sequence, and fold. The form SHALL allow creating new stages and editing existing ones.

#### Scenario: Create new stage
- **WHEN** admin clicks "New" in the stage list
- **THEN** a form view SHALL open for creating a new stage
- **THEN** admin SHALL be able to set name, sequence, and fold values

#### Scenario: Edit existing stage
- **WHEN** admin clicks on a stage in the list
- **THEN** a form view SHALL open with the stage details
- **THEN** admin SHALL be able to modify all fields

### Requirement: Stage configuration menu

The system SHALL provide a Configuration submenu under News Assistant containing "Article Stages". This menu SHALL be restricted to users with the `newsassistant_group_admin` group.

#### Scenario: Admin sees configuration menu
- **WHEN** admin user opens News Assistant menu
- **THEN** a "Configuration" submenu SHALL be visible
- **THEN** "Article Stages" SHALL be under Configuration

#### Scenario: Non-admin cannot see configuration
- **WHEN** regular user (non-admin) opens News Assistant menu
- **THEN** the "Configuration" submenu SHALL NOT be visible

### Requirement: Stage action

The system SHALL provide a window action for `news.article.stage` with path "article-stages" for pretty URLs.

#### Scenario: Stage configuration has pretty URL
- **WHEN** admin navigates to Article Stages configuration
- **THEN** the URL SHALL be `/odoo/article-stages`
