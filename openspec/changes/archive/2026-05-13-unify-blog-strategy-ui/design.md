## Context

The article detail view has two evaluation tabs — Blog and Strategy — that share the same conceptual structure (state badge + evaluate button, reasoning block, result block) but diverge in three ways:

1. **Field string labels** — `digest_state` is "Digest State"; `strategy_eval_state` is "Strategy Eval State"; `strategy_reasoning` is "Strategy Reasoning". These surface in search filters, group-by menus, and chatter tracking with inconsistent naming.
2. **Button visibility** — Blog's Evaluate button hides when `state != 'scraped'`; Strategy's does not, making it clickable on unscraped articles where evaluation cannot produce meaningful output.
3. **Re-evaluation reset** — Blog's `action_digest_now` clears `teaser` before re-running. Strategy's `action_reevaluate_strategy_labels` clears `strategy_reasoning` but leaves existing `strategy_label_ids` in place, causing labels to accumulate across re-evaluations.

## Goals / Non-Goals

**Goals:**
- Both tabs present identical chrome (badge label strings, button visibility rule, tooltip presence)
- Both re-evaluation actions follow the same "clear previous result, then queue job" pattern
- Field string labels unified to "Evaluation Status" / "Reasoning" so search and group-by are consistent

**Non-Goals:**
- Visual redesign of the tab layout (already structurally parallel)
- Moving the "Blog Post" stat button out of the button-box
- Renaming selection values (`pending`/`processed`) — labels already identical, no migration needed
- Unifying notification wording ("Digest Started" vs "Evaluation Queued") — deferred polish
- Extracting shared `_call_ai`/`_parse_ai_json` to avoid cross-module duplication — separate architectural concern

## Decisions

### D1: Change field `string=` attributes, not field names
Field names (`digest_state`, `strategy_eval_state`, `strategy_reasoning`) are referenced in Python code, tests, and views. Renaming them would require a DB column rename + migration. The `string=` attribute is purely presentational — it only affects what the label displays to the user and in search/filters. We change only `string=`, leaving field names and selection values untouched.

**Alternatives considered:** Rename fields entirely → rejected due to migration cost and risk for a cosmetic fix.

### D2: Clear `strategy_label_ids` with `(5, False, False)` command
Odoo's Many2many write command `(5, False, False)` unlinks all existing relations without deleting the `strategy.label` records themselves. This is the correct way to "clear" a M2M field. The reset happens synchronously in `action_reevaluate_strategy_labels` before the background job is queued, matching the blog pattern where `teaser = False` is set before calling `with_delay()`.

**Alternatives considered:** Clear inside the background job `_evaluate_strategy_labels` → rejected because it leaves stale labels visible during the queued window, and it breaks the symmetry with the blog pattern.

### D3: Reuse existing button visibility expression `invisible="state != 'scraped'"`
The blog tab already uses this exact expression. Applying the same string to the strategy button requires no new computed field or domain logic — it references the base `state` field on `news.article` which is always present.

## Risks / Trade-offs

- **Stale labels on existing records**: Records that were evaluated before this change may have labels that would not be assigned again on re-evaluation. This is pre-existing state; the change only affects what happens on the _next_ re-evaluation. Acceptable.
- **Search filter display change**: Renaming `string="Digest State"` → `"Evaluation Status"` changes how the field appears in the search panel filters for the blog module. Users who have saved filters referencing "Digest State" by label will see the label change. Low risk — this is a beta/internal app with no saved-filter dependency documented.

## Migration Plan

1. Edit three Python files (field string attributes + one action method body)
2. Edit one XML view file (button attributes)
3. Upgrade both affected modules (`newsassistant_blog`, `newsassistant_strategy_digest`)
4. Restart container
5. Smoke test

No DB schema changes. No data migration. Rollback = revert Python/XML edits + upgrade.
