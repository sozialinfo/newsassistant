## ADDED Requirements

### Requirement: Strategy watch flag on news.article
The system SHALL add a `strategy_watch` Boolean field (default `False`) to `news.article` via the `newsassistant_strategy_watch` module. The field SHALL be displayable on kanban cards using the `boolean_favorite` widget in the top-right corner of the card. The field SHALL also be filterable in the list and kanban search views.

#### Scenario: Watch flag not set by default
- **WHEN** a new article is scraped
- **THEN** `strategy_watch` SHALL be `False`

#### Scenario: Watch flag becomes True after evaluation
- **WHEN** an article is evaluated against a watch prompt and the AI determines strategic impact
- **THEN** `strategy_watch` SHALL be set to `True`

### Requirement: Strategy watch state on news.article
The system SHALL add a `strategy_watch_state` Selection field (pending/processed, default pending, readonly, indexed) to `news.article`. This tracks whether the article has been evaluated by the watch module.

#### Scenario: New articles are pending watch evaluation
- **WHEN** a new article is created
- **THEN** `strategy_watch_state` SHALL be `pending`

#### Scenario: Watch evaluation marks article as processed
- **WHEN** an article's watch evaluation completes
- **THEN** `strategy_watch_state` SHALL be set to `processed`

### Requirement: Strategy watch reasoning on news.article
The system SHALL add a `strategy_watch_reasoning` Text field (readonly) to `news.article`. This stores the LLM reasoning for why the article was flagged or not flagged as strategically relevant.

#### Scenario: Watch reasoning populated after evaluation
- **WHEN** an article is evaluated by the watch module
- **THEN** the AI's reasoning SHALL be stored in `strategy_watch_reasoning`

### Requirement: Watch prompt field on strategy.strategy
The `newsassistant_strategy_watch` module SHALL add a `watch_prompt` Html field to `strategy.strategy` via model inheritance. This field SHALL be used for the watch evaluation AI call.

#### Scenario: Watch prompt added to strategy form
- **WHEN** the watch module is installed
- **THEN** a "Watch Prompt" section SHALL appear in the Prompt tab with the `watch_prompt` field and a "Distill" button

### Requirement: Watch prompt distillation
The watch module SHALL provide an `action_distill_watch_prompt()` action on `strategy.strategy`. When triggered, the system SHALL call the AI with the strategy's documents and description to generate a watch-specific prompt. The result SHALL be saved to `watch_prompt`. If `watch_prompt` already exists, a confirmation wizard SHALL be shown before overwriting.

#### Scenario: Distill watch prompt from documents
- **WHEN** a user clicks "Distill" in the Watch Prompt section on a strategy with PDFs and description
- **THEN** the system SHALL call the AI to generate a watch prompt
- **THEN** the result SHALL be saved to `strategy.watch_prompt`
- **THEN** a success notification SHALL be shown

#### Scenario: Overwrite confirmation for existing watch prompt
- **WHEN** a user clicks "Distill" and `watch_prompt` already exists
- **THEN** a confirmation wizard SHALL be shown before overwriting

### Requirement: Watch evaluation logic
The watch module SHALL provide `_evaluate_strategy_watch()` on `news.article` (overriding the base no-op). This method SHALL iterate over all active strategies with a non-empty `watch_prompt`, call the AI for each, and set `strategy_watch = True` if the AI determines strategic impact exists. The AI response SHALL include a boolean `is_watch_relevant` and reasoning.

#### Scenario: Article triggers strategy watch
- **WHEN** an article's content matches a strategy's watch prompt
- **AND** the AI returns `is_watch_relevant: true`
- **THEN** `strategy_watch` SHALL be set to `True`
- **THEN** `strategy_watch_reasoning` SHALL contain the AI's explanation

#### Scenario: Article does not trigger strategy watch
- **WHEN** an article's content does not match any strategy's watch prompt
- **THEN** `strategy_watch` SHALL remain `False`
- **THEN** `strategy_watch_state` SHALL still be set to `processed`

#### Scenario: No active strategies with watch prompt
- **WHEN** no active strategies have a `watch_prompt`
- **THEN** the article SHALL be marked as `strategy_watch_state = processed` without any AI call

### Requirement: Watch star on kanban card
The kanban card SHALL display a clickable star icon using the `boolean_favorite` widget for the `strategy_watch` field in the top-right corner. The star SHALL toggle `strategy_watch` on click with autosave.

#### Scenario: Empty star when not watched
- **WHEN** `strategy_watch` is `False`
- **THEN** the kanban card SHALL show an empty star (fa-star-o) in the top-right corner

#### Scenario: Filled star when watched
- **WHEN** `strategy_watch` is `True`
- **THEN** the kanban card SHALL show a filled gold star (fa-star) in the top-right corner

#### Scenario: Click toggles watch flag
- **WHEN** a user clicks the star on the kanban card
- **THEN** `strategy_watch` SHALL toggle between True and False
- **THEN** the record SHALL be autosaved

### Requirement: Watch filter in search view
The search view SHALL include filters for `strategy_watch` and `strategy_watch_state`, allowing users to filter articles by watch status.

#### Scenario: Filter for watched articles
- **WHEN** a user selects the "Strategy Watch" filter
- **THEN** only articles with `strategy_watch = True` SHALL be displayed

#### Scenario: Filter for pending watch evaluation
- **WHEN** a user selects the "Watch: Pending" filter
- **THEN** only articles with `strategy_watch_state = pending` SHALL be displayed

### Requirement: Watch manual re-evaluation
The watch module SHALL provide an `action_reevaluate_strategy_watch()` button on the article form. This SHALL clear watch-related fields and re-queue evaluation.

#### Scenario: Manual re-evaluation clears watch data
- **WHEN** a user clicks "Watch Evaluate" on the article form
- **THEN** `strategy_watch_state` SHALL be reset to `pending`
- **THEN** `strategy_watch_reasoning` SHALL be cleared
- **THEN** `strategy_watch` SHALL be reset to `False`
- **THEN** a new evaluation job SHALL be queued