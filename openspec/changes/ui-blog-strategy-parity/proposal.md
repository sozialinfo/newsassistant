## Why

The Blog and Strategy tabs in the article detail view are inconsistent: Blog has a dedicated tab with its evaluation state and reasoning, while Strategy fields are scattered in the main group with a stat button in the button_box. The snapshot form also buries raw HTML content behind an admin-only tab with poor naming and ordering. Unifying the UI pattern makes both evaluation workflows readable and comparable side-by-side.

## What Changes

- Move all Blog-related fields and the "Digest Now" button into the Blog tab; remove from header and button_box
- Add a Strategy tab with `strategy_eval_state`, reasoning, labels, and a "Re-evaluate" button inline next to the state — remove these from the main group and button_box
- Both tabs display evaluation state with identical badge styling and language
- Add `strategy_reasoning` field (Text) to store per-strategy reasoning, concatenated when multiple strategies match
- Update the AI prompt in `_evaluate_against_strategy` to request a `"reasoning"` key in the JSON response
- Store the reasoning when processing each strategy evaluation
- In `news.snapshot` form: rename "Raw Content" tab to "Content", move it before "Articles", remove `groups` restriction, display `raw_content` as HTML read-only

## Capabilities

### New Capabilities
- `strategy-reasoning`: Store and display LLM reasoning for strategy label assignments (why labels were matched)

### Modified Capabilities
- None — this is a UI reorganisation and a new field; no existing spec-level behaviour changes

## Impact

- `newsassistant_blog`: `views/news_article_views.xml` — Blog tab restructured, button moved
- `newsassistant_strategy_digest`: `models/news_article.py` — new `strategy_reasoning` field, updated AI prompt and storage; `views/news_article_views.xml` — Strategy tab added, main-group fields removed, button moved
- `newsassistant`: `views/news_snapshot_views.xml` — tab renamed, reordered, groups restriction removed
- No new module dependencies; no breaking API changes
