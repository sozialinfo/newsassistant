## Why

The existing `newsassistant_strategy_digest` module bundles article labeling, executive brief generation, and a shared `strategy.strategy` model into one module. To support a new "strategy watch" feature (flagging articles with strategic impact), the `strategy.strategy` model needs to be extracted into a shared base module. This enables both digest and watch features to coexist independently while sharing the same strategy definitions.

## What Changes

- **New base module `newsassistant_strategy`**: Extracts `strategy.strategy` and `strategy.label` models from the digest module into a shared base. Owns the unified cron job and menu root.
- **Refactor `newsassistant_strategy_digest`**: Inherits `strategy.strategy` from the base module instead of defining it. Renames `prompt` field to `digest_prompt`. Menu items move under the new "Strategy" root.
- **New module `newsassistant_strategy_watch`**: Adds `strategy_watch` (boolean), `strategy_watch_state`, and `strategy_watch_reasoning` fields to `news.article`. Extends `strategy.strategy` with `watch_prompt`. Evaluates articles against the watch prompt and sets a clickable star icon on kanban cards when strategic impact is detected.
- **Unified cron**: Base module runs a single `_cron_strategy_eval()` that dispatches to both sister modules' evaluation methods.
- **Prompt tab restructure**: Base module creates a shell "Prompt" tab on the strategy form. Each sister module injects its own prompt section and "Distill" button. Distillation is fully decoupled — each module calls the AI independently.

## Capabilities

### New Capabilities

- `strategy-base`: Shared `strategy.strategy` and `strategy.label` models, unified cron, "Strategy" menu root, prompt tab shell
- `strategy-watch`: Article strategy watch flagging with boolean star toggle on kanban cards, watch prompt per strategy, independent AI distillation
- `strategy-digest-prompts`: Per-module prompt fields (`digest_prompt` on digest, `watch_prompt` on watch), independent distillation per module

### Modified Capabilities

<!-- None — existing capabilities preserved through refactoring -->

## Impact

- **`newsassistant_strategy_digest`**: Significant refactor — `strategy.strategy` model definition moves to base module, `prompt` field renamed to `digest_prompt`, menu restructured. Existing views, tests, and logic preserved with updated model references.
- **`newsassistant_strategy_watch`**: New module, no impact on existing code.
- **`newsassistant` core**: No changes. Both sister modules extend `news.article` independently.
- **Database**: No migration needed — this is a development environment, clean reinstall expected.