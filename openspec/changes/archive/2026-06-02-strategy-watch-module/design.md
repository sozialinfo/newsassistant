## Context

The `newsassistant_strategy_digest` module currently owns `strategy.strategy`, `strategy.label`, and all strategy-related functionality. To add a separate "strategy watch" feature without coupling it to the digest module, the shared models must be extracted into a base module. This is a development environment — no production data or migration concerns.

## Goals / Non-Goals

**Goals:**
- Extract `strategy.strategy` and `strategy.label` into a shared `newsassistant_strategy` base module
- Create `newsassistant_strategy_watch` — an independent module for binary strategic impact detection
- Both sisters share the same "Strategy" menu root and strategy form
- Each sister module has its own prompt field on `strategy.strategy` and independently distills it
- Unified cron in the base module dispatches to both sisters' evaluation methods
- Watch flag uses `boolean_favorite` widget as a clickable star on kanban cards

**Non-Goals:**
- No database migration (clean reinstall)
- No shared AI infrastructure between sisters (each has `_call_ai`)
- No changes to `strategy.digest` model or brief generation
- No changes to `newsassistant` core module

## Decisions

### D1: Three-module architecture (base + two sisters)

```
newsassistant_strategy/              # BASE — owns strategy.strategy, strategy.label, cron, menu root
newsassistant_strategy_digest/       # SISTER — inherits strategy.strategy, adds digest_prompt
newsassistant_strategy_watch/        # SISTER — inherits strategy.strategy, adds watch_prompt
```

**Rationale**: Clean separation. Each sister can be installed independently. The base module provides shared infrastructure without knowing about either sister.

**Alternative considered**: Single module with two features. Rejected — violates user's requirement for independent modules.

### D2: strategy.strategy keeps `_name` in base, sisters use `_inherit`

Base defines `strategy.strategy` with all shared fields (name, state, dates, description, document_ids, label_ids). Sisters add their own prompt fields via `_inherit`. The existing `prompt` field in the digest module is renamed to `digest_prompt`.

**Rationale**: Standard Odoo inheritance pattern. No `_inherits` delegation needed since no new table is created — just field additions.

**Alternative considered**: Use `_inherits` delegation. Rejected — adds complexity for no benefit. Sisters only add fields, no new model identity.

### D3: Independent `_call_ai()` in each module

Each module has its own AI calling infrastructure (duplicated code pattern, matching the current digest module's self-contained approach). No shared AI utility.

**Rationale**: Follows existing pattern in the codebase (the digest module already has its own `_call_ai`). Avoids coupling sisters through utility dependencies.

### D4: Unified cron in base module

Base module owns `_cron_strategy_eval()` which queues `_evaluate_strategies()` per article. Sisters extend this method:

```python
# Base module (news.article extension)
def _evaluate_strategies(self):
    self.ensure_one()
    self._evaluate_strategy_labels()  # no-op in base, overridden in digest
    self._evaluate_strategy_watch()   # no-op in base, overridden in watch

# Digest module (news.article extension)
def _evaluate_strategy_labels(self):
    ... # existing logic, checks strategy_eval_state

# Watch module (news.article extension)
def _evaluate_strategy_watch(self):
    ... # new logic, checks strategy_watch_state
```

Each sister's method is a no-op in the base and checks its own state field to skip already-processed articles.

**Rationale**: One cron to rule them all. No redundant scheduling. Each module short-circuits if already processed.

**Alternative considered**: Separate crons per module. Rejected — user requested unified approach.

### D5: Prompt tab shell in base, sections injected by sisters

Base form view defines a "Prompt" notebook page with only an explanation banner. Each sister xpath-injects its own section (prompt field + Distill button) into this page.

```xml
<!-- Base: newsassistant_strategy/views/strategy_strategy_views.xml -->
<page string="Prompt" name="prompt">
    <p class="text-muted">Configure prompts for strategy evaluation...</p>
</page>

<!-- Digest: injects -->
<xpath expr="//page[@name='prompt']" position="inside">
    <group string="Digest Prompt">
        <field name="digest_prompt"/>
        <button name="action_distill_digest_prompt" string="Distill" type="object"/>
    </group>
</xpath>

<!-- Watch: injects -->
<xpath expr="//page[@name='prompt']" position="inside">
    <group string="Watch Prompt">
        <field name="watch_prompt"/>
        <button name="action_distill_watch_prompt" string="Distill" type="object"/>
    </group>
</xpath>
```

**Rationale**: Extensible. Any number of future modules can add prompt sections.

### D6: boolean_favorite widget for strategy watch flag

The `strategy_watch` boolean on `news.article` uses `widget="boolean_favorite"` on the kanban card. This renders as `fa-star-o` (empty) / `fa-star` (gold) — clickable toggle at the top-right corner of the card.

**Rationale**: User explicitly requested this widget and top-right placement. Follows `project.project` kanban pattern.

### D7: Module-level distillation button naming

Each sister module provides its own distillation button with distinct method names:
- Digest: `action_distill_digest_prompt()` → `_distill_digest_prompt()`
- Watch: `action_distill_watch_prompt()` → `_distill_watch_prompt()`

Each uses its own `_DISTILL_SYSTEM_PROMPT` class constant.

**Rationale**: No name conflicts. Clear ownership. Each module's distillation logic is fully self-contained.

## Risks / Trade-offs

- **Risk**: `_call_ai()` duplication across three modules → **Mitigation**: Follows existing pattern. Phase 2 hardening can extract shared utility.
- **Risk**: Creeping coupling if more sisters are added → **Mitigation**: The base module only provides model shell + cron dispatch. No sister-specific logic in base.
- **Risk**: Prompt tab getting cluttered with many modules → **Mitigation**: Each section is clearly labeled. For now, only two modules.