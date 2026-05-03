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

### Requirement: HTML prompt conversion for article evaluation
The system SHALL convert the HTML prompt of a strategy to plain text before including it in the LLM request for article evaluation. The conversion SHALL use the shared `html_to_markdown()` utility from the `newsassistant` base module.

#### Scenario: HTML prompt converted to plain text before LLM call
- **WHEN** an article is evaluated against a strategy whose prompt contains HTML markup
- **THEN** the HTML SHALL be converted to plain text before being sent to the LLM
- **THEN** the LLM SHALL NOT receive raw HTML tags in the prompt
