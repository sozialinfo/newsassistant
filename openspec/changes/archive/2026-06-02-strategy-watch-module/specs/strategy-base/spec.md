## ADDED Requirements

### Requirement: Shared strategy base module
The system SHALL provide a `newsassistant_strategy` module that defines the shared `strategy.strategy` and `strategy.label` models previously owned by `newsassistant_strategy_digest`. The base module SHALL NOT depend on either sister module. The base module SHALL own the "Strategy" root menu and the unified strategy evaluation cron.

#### Scenario: Base module installs independently
- **WHEN** `newsassistant_strategy` is installed without any sister modules
- **THEN** `strategy.strategy` and `strategy.label` models SHALL be available
- **THEN** the "Strategy" root menu with "Strategies" submenu SHALL be visible
- **THEN** the unified cron SHALL be registered (but may have no dispatch targets)

### Requirement: Unified strategy evaluation cron
The base module SHALL provide a cron job that runs hourly and evaluates all scraped articles against active strategies. The cron SHALL queue `_evaluate_strategies()` per article, which dispatches to sister modules' evaluation methods. The base module's dispatch methods (`_evaluate_strategy_labels` and `_evaluate_strategy_watch`) SHALL be no-ops that sister modules override.

#### Scenario: Cron runs with no sister modules installed
- **WHEN** the unified cron runs and no sister modules are installed
- **THEN** the dispatch SHALL be a no-op
- **THEN** no errors SHALL occur

#### Scenario: Cron runs with both sister modules installed
- **WHEN** the unified cron runs and both digest and watch modules are installed
- **THEN** each article SHALL be evaluated by both the digest module and the watch module

### Requirement: Strategy root menu
The system SHALL provide a "Strategy" root menu under the News Assistant parent menu. The root menu SHALL contain the "Strategies" submenu (from the base module). Sister modules SHALL add their own submenus under "Strategy" via xpath or menuitem inheritance.

#### Scenario: Navigate to strategy root
- **WHEN** a user clicks "Strategy" in the News Assistant menu
- **THEN** the Strategies submenu SHALL be visible
- **THEN** sister module submenus (Digest, Watch) SHALL be visible if installed

### Requirement: Prompt tab shell in strategy form
The base module SHALL define a "Prompt" notebook page in the `strategy.strategy` form view. The page SHALL contain only an instructional banner explaining that sister modules add their own prompt sections. Sister modules SHALL inject their prompt fields and distillation buttons into this page.

#### Scenario: Prompt tab shows instructional banner when no sister modules installed
- **WHEN** a user opens the Prompt tab on a strategy form and no sister modules are installed
- **THEN** an instructional banner SHALL be displayed explaining how to install modules for prompt configuration

#### Scenario: Sister module injects prompt section
- **WHEN** the digest module is installed
- **THEN** a "Digest Prompt" section with the `digest_prompt` field and "Distill" button SHALL appear in the Prompt tab
- **WHEN** the watch module is also installed
- **THEN** a "Watch Prompt" section with the `watch_prompt` field and "Distill" button SHALL also appear in the Prompt tab

### Requirement: Strategy strategy model in base module
The system SHALL define `strategy.strategy` in the base module with fields: `name` (Char, required), `state` (Selection: draft/active/archived), `date_from` (Date), `date_to` (Date), `description` (Text), `document_ids` (Many2many → ir.attachment), and `label_ids` (Many2many → strategy.label). The prompt field SHALL NOT be in the base module — each sister module adds its own prompt field.

#### Scenario: Strategy created in base module has no prompt field
- **WHEN** a base-only strategy record is created
- **THEN** the record SHALL have name, state, dates, description, documents, and labels
- **THEN** no prompt field SHALL exist on the record

### Requirement: Strategy label model in base module
The system SHALL define `strategy.label` in the base module with fields: `name` (Char, required, unique), `color` (Integer, default random 1–11). Admin users SHALL manage labels via "Strategy" → "Labels" submenu.

#### Scenario: Strategy labels managed from base module
- **WHEN** an admin navigates to Strategy → Labels
- **THEN** the list of strategy labels SHALL be displayed and editable