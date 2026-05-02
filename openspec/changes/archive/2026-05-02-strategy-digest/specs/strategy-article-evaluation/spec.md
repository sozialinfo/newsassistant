## ADDED Requirements

### Requirement: Article strategy evaluation state
The system SHALL add a field `strategy_eval_state` (Selection: `pending` / `processed`, default `pending`, readonly, indexed) to `news.article` via model inheritance. This field tracks whether the article has been evaluated against active strategies.

#### Scenario: New article starts as pending
- **WHEN** a new article is created (state = scraped)
- **THEN** `strategy_eval_state` SHALL default to `pending`

#### Scenario: After evaluation, state becomes processed
- **WHEN** the evaluation pipeline finishes processing an article
- **THEN** `strategy_eval_state` SHALL be set to `processed`

### Requirement: Cron-based automatic evaluation
The system SHALL provide a cron job that runs hourly and evaluates all articles in state `scraped` with `strategy_eval_state = pending` against all active strategies. For each article × strategy pair, the system SHALL call the AI using the strategy's distilled prompt and assign matching `strategy.label` records to the article's `strategy_label_ids`. After all strategies are evaluated for an article, `strategy_eval_state` SHALL be set to `processed`.

#### Scenario: Cron evaluates unprocessed articles
- **WHEN** the cron runs and there are articles with strategy_eval_state = pending
- **THEN** each such article SHALL be queued for evaluation via queue_job
- **THEN** articles already processed SHALL be skipped

#### Scenario: Article evaluated against multiple active strategies
- **WHEN** an article is evaluated and two active strategies match
- **THEN** labels from both strategies SHALL be added to the article's strategy_label_ids

#### Scenario: Strategy with expired date range is skipped
- **WHEN** a strategy has date_to in the past
- **THEN** that strategy SHALL NOT be evaluated against new articles

#### Scenario: Strategy without distilled prompt is skipped
- **WHEN** a strategy has no prompt (empty string)
- **THEN** that strategy SHALL be skipped during evaluation
- **THEN** a warning SHALL be logged

### Requirement: Manual re-evaluation trigger
The system SHALL provide an action button "Re-evaluate Strategy Labels" on the `news.article` form view. When triggered, it SHALL reset `strategy_eval_state` to `pending` and queue a new evaluation job. A server action SHALL also be available from the list view to re-evaluate selected articles.

#### Scenario: Manual re-evaluation on form
- **WHEN** a user clicks "Re-evaluate Strategy Labels" on an article form
- **THEN** `strategy_eval_state` SHALL be reset to `pending`
- **THEN** an evaluation job SHALL be queued immediately
- **THEN** a notification SHALL confirm the job was queued

#### Scenario: Bulk re-evaluation from list view
- **WHEN** a user selects multiple articles and triggers "Re-evaluate Strategy Labels"
- **THEN** all selected articles SHALL have their strategy_eval_state reset to pending
- **THEN** evaluation jobs SHALL be queued for each selected article

### Requirement: AI label assignment per strategy
The system SHALL call the AI for each article × active strategy pair using the strategy's stored prompt. The AI SHALL return a JSON object with a boolean `is_relevant` and the list of label names to assign (from the strategy's label set). The system SHALL resolve label names to `strategy.label` records and add them to the article's `strategy_label_ids`.

#### Scenario: AI returns relevant with labels
- **WHEN** the AI responds with is_relevant=true and label names ["Innovation", "Risk"]
- **THEN** the article SHALL have those strategy.label records added to strategy_label_ids

#### Scenario: AI returns not relevant
- **WHEN** the AI responds with is_relevant=false
- **THEN** no labels from this strategy SHALL be added to the article
- **THEN** no existing labels SHALL be removed

#### Scenario: AI returns unknown label name
- **WHEN** the AI returns a label name not in the strategy's label_ids
- **THEN** the system SHALL log a warning and skip that label
- **THEN** other valid labels SHALL still be assigned
