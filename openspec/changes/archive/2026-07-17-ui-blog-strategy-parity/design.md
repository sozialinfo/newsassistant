## Context

The article detail form view is extended by two independent modules: `newsassistant_blog` and `newsassistant_strategy_digest`. Currently:
- Blog fields are partially in a tab, partially in the header (button)
- Strategy fields are in the main group body (not a tab), with the re-evaluate button as a stat_button in the button_box
- The two evaluation workflows look different despite being conceptually identical (state + reasoning + result)
- `news.snapshot` has its raw content tab named "Raw Content" gated behind admin groups, listed after Articles

## Goals / Non-Goals

**Goals:**
- Identical visual pattern for Blog and Strategy tabs: `[state badge] [action button]` → reasoning → result
- `strategy_reasoning` field added to model and populated from LLM
- Snapshot form: Content tab first, no admin gate, named "Content"

**Non-Goals:**
- No custom JavaScript — use standard Odoo widgets only
- No changes to list/kanban views beyond what's already there
- No translations (Phase 1)

## Decisions

### D1: Inline button placement next to evaluation state

Odoo 18 form views do not have a native "field + button on same row" layout primitive in `<group>`. The cleanest solution is a `<div class="d-flex align-items-center gap-2">` wrapping both the badge field and a regular `<button>` inside a tab page. This avoids custom JS and renders correctly in the web client.

Alternative considered: keep button in header or button_box — rejected because the user explicitly requested it next to the state.

### D2: strategy_reasoning as a single Text field

Since an article can match multiple strategies, reasoning is concatenated as:
```
Strategy A: <reasoning text>

Strategy B: <reasoning text>
```
This mirrors the shape of `blog_reasoning` and avoids a new relational model. The field is reset (along with `strategy_label_ids`) when `action_reevaluate_strategy_labels` is called.

### D3: LLM prompt update for reasoning

Add `"reasoning"` as a required key in the JSON contract returned by `_evaluate_against_strategy`. The prompt already asks for `is_relevant` and `labels`; adding `"reasoning": "short explanation"` is a minimal change. The reasoning is extracted and accumulated across strategies before being written to `strategy_reasoning` in `_evaluate_strategy_labels`.

### D4: Remove strategy fields from main group

The `<group string="Strategy">` in the main body (added by `newsassistant_strategy_digest`) is removed via xpath. Strategy labels remain visible in the kanban card (unchanged) and in the new Strategy tab.

### D5: Snapshot Content tab — remove groups restriction

The `groups="newsassistant.newsassistant_group_admin"` on the Raw Content page served no real purpose (the HTML was already readonly). Removing it makes raw content accessible to all users who can access snapshots.

## Risks / Trade-offs

- [Existing strategy reasoning is NULL] → Acceptable: field is new, old records will show empty reasoning. No migration needed.
- [LLM may not always return "reasoning" key] → Mitigation: use `.get("reasoning", "")` with a safe fallback, same pattern as `labels`.
- [Multiple xpath patches on the same view] → Mitigation: each module owns its own inherit view; order is determined by priority (default 16). No conflicts expected.
