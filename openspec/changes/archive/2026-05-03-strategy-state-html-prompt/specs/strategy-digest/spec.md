## MODIFIED Requirements

### Requirement: Automatic strategy and article resolution
The system SHALL provide a method that, given the digest's `date_from` and `date_to`, resolves: (a) all **active** `strategy.strategy` records (state = `active`) whose date range overlaps the digest period (or that have no dates), and (b) all `news.article` records with at least one `strategy_label_ids` entry and a `date` within the period.

#### Scenario: Resolve strategies for period — active only
- **WHEN** the digest period is Jan–Dec 2026
- **THEN** only strategies with state = `active` AND overlapping date range SHALL be included
- **THEN** draft and archived strategies SHALL be excluded even if their date range overlaps

#### Scenario: Resolve articles for period
- **WHEN** the digest period is Jan–Dec 2026
- **THEN** only articles with date within the period AND at least one strategy_label_ids SHALL be included
- **THEN** articles outside the date range SHALL be excluded
- **THEN** articles with no strategy labels SHALL be excluded

### Requirement: HTML prompt conversion for digest generation
The system SHALL convert the HTML prompt of each strategy to plain text before including it in the LLM request for brief generation. The conversion SHALL use the shared `html_to_markdown()` utility from the `newsassistant` base module.

#### Scenario: HTML prompt converted before LLM call
- **WHEN** a digest brief is generated and strategies have HTML prompts
- **THEN** each strategy prompt SHALL be converted to plain text before being sent to the LLM
- **THEN** the LLM SHALL NOT receive raw HTML tags in the prompt
