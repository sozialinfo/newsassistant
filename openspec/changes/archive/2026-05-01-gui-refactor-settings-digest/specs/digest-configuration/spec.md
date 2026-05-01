## MODIFIED Requirements

### Requirement: Settings appear under a single menu entry
All News Assistant settings (base, email, and blog) SHALL appear under a single "Settings" menu entry in the Configuration menu. Previously blog settings had a separate "Blog Settings" menu entry pointing to a separate app block. Now the blog settings blocks SHALL be injected into the `newsassistant` app block using the same xpath inheritance pattern used by `newsassistant_email`.

#### Scenario: Single settings menu entry
- **WHEN** an admin opens the Configuration menu
- **THEN** only one settings menu item SHALL be present (labeled "Settings")
- **THEN** clicking it SHALL open the standard Odoo settings page with the News Assistant app block
- **THEN** the News Assistant app block SHALL contain all settings: Article Defaults, Email Capture, Content Strategy, Teaser Generation, Publishing, Pipeline Stages, and Header Images

#### Scenario: No separate Blog Settings menu
- **WHEN** an admin opens the Configuration menu
- **THEN** there SHALL be no "Blog Settings" menu item separate from "Settings"

### Requirement: Prompt input fields have full-width layout
The Content Strategy and Teaser Prompt input fields in the settings view SHALL use a full-width layout: the label SHALL appear on its own line above the textarea, and the textarea SHALL occupy the full available width within the settings column. Previously the label and field appeared side-by-side, making the textarea narrow.

#### Scenario: Content strategy prompt field is full-width
- **WHEN** an admin opens the settings and scrolls to Content Strategy
- **THEN** the label "Your Content Strategy" SHALL appear above the textarea (not beside it)
- **THEN** the textarea SHALL fill the available column width

#### Scenario: Teaser prompt field is full-width
- **WHEN** an admin opens the settings and scrolls to Teaser Generation
- **THEN** the label "Your Teaser Prompt" SHALL appear above the textarea (not beside it)
- **THEN** the textarea SHALL fill the available column width

### Requirement: Relevance criteria help text explains outcomes
The "Relevance Criteria" setting SHALL include help text that explains the three AI classification outcomes and their consequences: Relevant articles are auto-published to the blog, Uncertain articles are moved to the Shortlist stage for human review, and Discarded articles are moved to the Discard stage and skipped.

#### Scenario: Help text explains all three outcomes
- **WHEN** an admin hovers over the help icon for "Relevance Criteria"
- **THEN** the tooltip SHALL explain that Relevant = auto-published, Uncertain = Shortlist for human review, Discard = Discard stage and skipped
