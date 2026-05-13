## Why

After the blog relevance AI evaluates an article, the user has no visibility into the outcome — the reasoning is lost for discarded and uncertain articles, and uncertain articles don't move to a meaningful pipeline stage. Users need to understand why an article was accepted or rejected.

## What Changes

- Store `blog_reasoning` for **all** evaluation outcomes (discard, uncertain, relevant) — currently only stored for relevant
- Move **uncertain** articles to the Shortlist stage (currently they stay in "New" with no feedback)
- Move **relevant** articles **directly to Published** after blog post creation — remove the intermediate Shortlist stop (currently relevant → Shortlist → Published; now relevant → Published directly)

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- `digest-pipeline`: Reasoning is now stored for all decisions; uncertain articles move to Shortlist; relevant articles skip Shortlist and go directly to Published

## Impact

- `newsassistant_blog/models/news_article.py`: `_handle_discard`, `_handle_uncertain`, `_handle_shortlist` — store reasoning in all branches; move uncertain to shortlist; remove shortlist stage write from relevant path
- No view changes required — Blog tab already shows `blog_reasoning` when set (`invisible="not blog_reasoning"`)
- No new fields, no schema changes, no version-breaking changes
