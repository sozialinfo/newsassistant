## Why

The Blog and Strategy tabs in the article detail view share the same conceptual structure — an evaluation state, AI reasoning, and a result — but are implemented with inconsistencies in field labels, button visibility guards, and evaluation reset behaviour. This creates a confusing experience where the two tabs look similar but behave differently.

## What Changes

- `digest_state` field string renamed from "Digest State" → "Evaluation Status"
- `strategy_eval_state` field string renamed from "Strategy Eval State" → "Evaluation Status"
- `strategy_reasoning` field string renamed from "Strategy Reasoning" → "Reasoning"
- Strategy "Evaluate" button gains `invisible="state != 'scraped'"` guard (matching Blog)
- Strategy "Evaluate" button gains a `title=` tooltip (matching Blog)
- `action_reevaluate_strategy_labels` now clears `strategy_label_ids` before re-evaluating (matching blog's teaser reset pattern)

## Capabilities

### New Capabilities
<!-- None — this is a polish/consistency change, no new spec-level capability -->

### Modified Capabilities
- `strategy-article-evaluation`: evaluation reset now clears existing labels (behaviour change)
- `article-views`: both tabs now follow the same UI pattern — same badge labels, same button guards, same reasoning field label

## Impact

- `addons/newsassistant_blog/models/news_article.py` — field string change
- `addons/newsassistant_strategy_digest/models/news_article.py` — field string change, reasoning string change, reset logic change
- `addons/newsassistant_strategy_digest/views/news_article_views.xml` — button invisible + title attributes
- No DB migration required (field names unchanged, selection values unchanged)
- No test changes expected (existing tests assert on field values, not string labels)
