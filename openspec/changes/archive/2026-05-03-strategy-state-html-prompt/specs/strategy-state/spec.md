## ADDED Requirements

### Requirement: Strategy lifecycle state
The system SHALL add a `state` field (Selection: `draft` / `active` / `archived`, default `draft`) to `strategy.strategy`. The form view SHALL display a statusbar widget in the header showing all three states. The list view SHALL display a badge widget for the state column.

#### Scenario: New strategy starts as draft
- **WHEN** a user creates a new strategy
- **THEN** its `state` SHALL default to `draft`
- **THEN** the statusbar SHALL show "Draft" as the current step

#### Scenario: State visible as badge in list view
- **WHEN** a user views the strategy list
- **THEN** the `state` column SHALL display a muted badge for draft, a success badge for active, and a danger badge for archived

### Requirement: State transitions
The system SHALL allow all state transitions in any direction: draft → active, draft → archived, active → draft, active → archived, archived → draft, archived → active. Transitions SHALL be performed by clicking the statusbar steps in the form view. No transition is one-way except the activation guard (see below).

#### Scenario: Activate from draft via statusbar
- **WHEN** a user clicks "Active" in the statusbar of a draft strategy that has a prompt set
- **THEN** the strategy state SHALL change to `active`

#### Scenario: Archive from active via statusbar
- **WHEN** a user clicks "Archived" in the statusbar of an active strategy
- **THEN** the strategy state SHALL change to `archived`

#### Scenario: Reactivate from archived via statusbar
- **WHEN** a user clicks "Active" in the statusbar of an archived strategy that has a prompt set
- **THEN** the strategy state SHALL change to `active`

#### Scenario: Reset to draft from any state
- **WHEN** a user clicks "Draft" in the statusbar of an active or archived strategy
- **THEN** the strategy state SHALL change to `draft`

### Requirement: Activation guard — prompt required
The system SHALL prevent activation of a strategy that has no prompt set. The guard SHALL be enforced in the model method called by the statusbar transition.

#### Scenario: Activation blocked — no prompt and no content
- **WHEN** a user attempts to activate a strategy with no prompt AND no documents AND no description
- **THEN** the system SHALL raise a UserError explaining that a prompt is required and must be distilled first

#### Scenario: Activation blocked — no prompt but content available — wizard offered
- **WHEN** a user attempts to activate a strategy with no prompt but with at least one document or a description
- **THEN** the system SHALL open a confirmation wizard offering to distill the prompt and then activate
- **WHEN** the user confirms in the wizard
- **THEN** the system SHALL run distillation and set state to `active`
- **WHEN** the user cancels the wizard
- **THEN** the state SHALL remain unchanged

#### Scenario: Activation succeeds — prompt already set
- **WHEN** a user activates a strategy that already has a prompt
- **THEN** the state SHALL change to `active` immediately without any wizard
