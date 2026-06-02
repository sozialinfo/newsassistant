## ADDED Requirements

### Requirement: Digest prompt field on strategy.strategy
The `newsassistant_strategy_digest` module SHALL add a `digest_prompt` Html field to `strategy.strategy` via model inheritance, replacing the previously module-owned `prompt` field. This field SHALL be used for the article labeling evaluation AI call.

#### Scenario: Digest prompt replaces legacy prompt field
- **WHEN** the digest module is installed (after refactoring)
- **THEN** `strategy.strategy` SHALL have a `digest_prompt` field instead of the old `prompt` field
- **THEN** all existing logic (distillation, evaluation, digest generation) SHALL reference `digest_prompt`

### Requirement: Independent distillation per module
Each sister module SHALL provide its own distillation action with distinct method names and its own `_DISTILL_SYSTEM_PROMPT` constant. The digest module uses `action_distill_digest_prompt()` and `_distill_digest_prompt()`. The watch module uses `action_distill_watch_prompt()` and `_distill_watch_prompt()`. Each module SHALL call the AI independently.

#### Scenario: Digest distillation uses digest-specific prompt
- **WHEN** the user clicks "Distill" in the Digest Prompt section
- **THEN** the system SHALL call the AI with the digest module's `_DISTILL_SYSTEM_PROMPT`
- **THEN** the result SHALL be saved to `digest_prompt`

#### Scenario: Watch distillation uses watch-specific prompt
- **WHEN** the user clicks "Distill" in the Watch Prompt section
- **THEN** the system SHALL call the AI with the watch module's `_DISTILL_SYSTEM_PROMPT`
- **THEN** the result SHALL be saved to `watch_prompt`

#### Scenario: Distillation runs independently
- **WHEN** both modules are installed and the user distills only the watch prompt
- **THEN** the digest prompt SHALL remain unchanged
- **THEN** only the watch prompt SHALL be updated
