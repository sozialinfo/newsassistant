## Context

The blog digest pipeline evaluates articles using AI and routes them to one of three outcomes: discard, uncertain, or relevant. Currently `blog_reasoning` (the AI's explanation) is only persisted for `relevant` articles. Uncertain articles also have no stage movement, leaving them invisible in the pipeline. Relevant articles pass through the Shortlist stage before landing in Published — an unnecessary intermediate stop since teaser and blog post creation are fully automated.

## Goals / Non-Goals

**Goals:**
- Store `blog_reasoning` for all three decisions so the user can always see why an article was accepted or rejected
- Move uncertain articles to the Shortlist stage so they surface for human review
- Move relevant articles directly to Published (skip Shortlist) since the full pipeline is automated

**Non-Goals:**
- No UI changes — the Blog tab already conditionally shows `blog_reasoning`
- No new fields — `blog_reasoning` already exists on the model
- No changes to the AI prompt or evaluation logic
- No changes to teaser generation or blog post creation

## Decisions

**Store reasoning in all handlers**
Each of `_handle_discard`, `_handle_uncertain`, `_handle_shortlist` will write `blog_reasoning`. This is the minimal change — one extra field write per handler.

**Uncertain → Shortlist stage**
Uncertain means "maybe relevant, human should decide." The Shortlist stage is the correct holding area for human review. The same `shortlist_stage_id` config parameter is reused — no new config needed.

**Relevant skips Shortlist**
`_handle_shortlist` (misleadingly named) currently writes `stage_id = shortlist_stage` at the top before generating the teaser. Removing that write means the article stays in its current stage during processing and lands directly in Published after blog post creation. The method name stays as-is to avoid unnecessary refactoring.

## Risks / Trade-offs

**Existing articles with no reasoning:** Articles processed before this change will have empty `blog_reasoning` — the Blog tab will simply not show the reasoning section (existing `invisible="not blog_reasoning"` guard). No migration needed.

**Shortlist stage not configured:** If `shortlist_stage_id` is not set in config, `_get_pipeline_stage` returns None and the uncertain article's stage is not updated (current silent-fail behaviour is preserved). This is acceptable — the reasoning will still be stored.
