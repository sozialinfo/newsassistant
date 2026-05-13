## MODIFIED Requirements

### Requirement: Cron-based automatic evaluation
The system SHALL provide a cron job that runs hourly and evaluates all articles in state `scraped` with `strategy_eval_state = pending` against all **active** strategies (state = `active`). For each article × strategy pair, the system SHALL call the AI using the strategy's distilled prompt (converted from HTML to plain text on the fly) and assign matching `strategy.label` records to the article's `strategy_label_ids`. After all strategies are evaluated for an article, `strategy_eval_state` SHALL be set to `processed`.

#### Scenario: Cron evaluates unprocessed articles against active strategies only
- **WHEN** the cron runs and there are articles with strategy_eval_state = pending
- **THEN** each such article SHALL be evaluated only against strategies with state = `active`
- **THEN** draft and archived strategies SHALL be excluded from evaluation

#### Scenario: Article evaluated against multiple active strategies
- **WHEN** an article is evaluated and two active strategies match
- **THEN** labels from both strategies SHALL be added to the article's strategy_label_ids

#### Scenario: Strategy with expired date range is skipped
- **WHEN** a strategy has date_to in the past
- **THEN** that strategy SHALL NOT be evaluated against new articles

#### Scenario: Strategy without distilled prompt is skipped
- **WHEN** an active strategy has no prompt (empty)
- **THEN** that strategy SHALL be skipped during evaluation
- **THEN** a warning SHALL be logged

### Requirement: Manual re-evaluation clears previous result
When a user triggers manual re-evaluation of strategy labels, the system SHALL clear all existing `strategy_label_ids` and reset `strategy_reasoning` to empty before queuing the background job. This ensures re-evaluation always produces a clean result rather than accumulating labels from prior runs.

#### Scenario: Re-evaluate clears existing labels
- **WHEN** a user clicks the Evaluate button on the Strategy tab of an article that already has strategy labels
- **THEN** all existing `strategy_label_ids` SHALL be removed before the new evaluation job runs
- **THEN** `strategy_eval_state` SHALL be set to `pending`
- **THEN** `strategy_reasoning` SHALL be cleared

#### Scenario: Re-evaluate only available on scraped articles
- **WHEN** an article has `state != 'scraped'`
- **THEN** the Evaluate button on the Strategy tab SHALL NOT be visible
