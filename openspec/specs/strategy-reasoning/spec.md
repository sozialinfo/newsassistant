## ADDED Requirements

### Requirement: Strategy evaluation stores LLM reasoning
The system SHALL capture and store the LLM's reasoning for each strategy label assignment. When an article is evaluated against one or more active strategies, the reasoning from each strategy evaluation SHALL be concatenated into a single `strategy_reasoning` text field on the article, prefixed with the strategy name.

#### Scenario: Single strategy match with reasoning
- **WHEN** an article is evaluated against one active strategy and the LLM returns labels and reasoning
- **THEN** `strategy_reasoning` is set to the reasoning text prefixed with the strategy name

#### Scenario: Multiple strategy matches with reasoning
- **WHEN** an article is evaluated against multiple active strategies and each returns reasoning
- **THEN** `strategy_reasoning` contains all reasonings concatenated, each prefixed with its strategy name, separated by a blank line

#### Scenario: Re-evaluation resets reasoning
- **WHEN** `action_reevaluate_strategy_labels` is called on an article
- **THEN** `strategy_reasoning` is cleared (set to False) before re-evaluation begins

#### Scenario: No matching strategies
- **WHEN** no active strategies exist or none match
- **THEN** `strategy_reasoning` remains empty

### Requirement: Strategy reasoning is visible in article form
The system SHALL display `strategy_reasoning` in the Strategy tab of the article form view, in the same visual style as `blog_reasoning` in the Blog tab (read-only text below the evaluation state).

#### Scenario: Reasoning displayed after evaluation
- **WHEN** an article has been evaluated and `strategy_reasoning` is non-empty
- **THEN** the Strategy tab shows the reasoning text in a labelled group, read-only

#### Scenario: Reasoning section hidden when empty
- **WHEN** `strategy_reasoning` is empty or False
- **THEN** the reasoning group is not displayed (invisible)
