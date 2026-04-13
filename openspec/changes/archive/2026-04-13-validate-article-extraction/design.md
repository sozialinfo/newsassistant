## Context

The scraping pipeline has two stages: Stage 1 discovers article URLs from listing pages, Stage 2 extracts content from each article. Currently, Stage 1 sometimes extracts navigation/category links (e.g., `/themen/arbeit/news`) instead of actual article links (e.g., `/aktuell/artikel/...`). These non-article URLs create stubs that go through the full extraction pipeline, wasting Jina and LLM API calls.

The root cause is that listing pages often have prominent navigation menus with "News" links that the LLM mistakes for article links. The actual articles are in the main content area with dates and specific headlines.

## Goals / Non-Goals

**Goals:**
- Validate fetched content is actually an article before extraction
- Mark non-articles as `skipped` to prevent re-discovery in future scrapes
- Reduce false positives from Stage 1 with improved prompt
- Single LLM call for validation + extraction (no extra API cost)

**Non-Goals:**
- Source-specific URL patterns or filtering rules
- Changing the article data model or states
- Pre-fetch validation (we validate using already-fetched content)

## Decisions

### Decision 1: Combined validation + extraction prompt

**Choice**: Merge validation into the existing extraction prompt rather than adding a separate validation step.

**Rationale**: 
- No additional API calls - validation uses the same content we'd extract from
- Single prompt first checks "is this an article?" then extracts if yes
- If not an article, returns `{is_article: false, reason: "..."}` instead of extracted data

**Alternatives considered**:
- Separate validation call before extraction: Doubles API calls, adds latency
- URL pattern filtering: Requires source-specific configuration, fragile
- Heuristic title filtering: Could miss legitimate articles with common titles

### Decision 2: Reuse `skipped` state for non-articles

**Choice**: Use existing `state="skipped"` with `error_message` explaining the reason.

**Rationale**:
- No schema changes needed
- `skipped` already means "don't process this" - works for both manual and automatic skipping
- URL remains in database, preventing re-discovery
- Can differentiate by checking `error_message` content if needed

**Alternatives considered**:
- New `discarded` state: Cleaner semantics but requires migration
- Delete the stub: Loses URL memory, would be re-discovered next scrape

### Decision 3: Validation criteria

**Choice**: LLM determines if content is a single article based on structural signals.

**Article indicators**:
- Single piece of content with headline and body text
- Publication date present
- Substantial prose (not just a list of links)
- Discusses one specific topic

**Non-article indicators**:
- List of multiple articles/links (index page)
- Category/topic overview with many subtopics
- Navigation-heavy content
- Missing body text (just links and headers)

### Decision 4: Improved Stage 1 prompt

**Choice**: Enhance listing prompt with explicit guidance about article indicators.

**Additions**:
- Emphasize looking for dated content items
- Explicit examples of what to exclude (navigation menus, category links ending in `/news`)
- Instruct to look for article-specific URL patterns (often contain `/artikel/`, `/article/`, `/post/`, date segments)
- Focus on main content area, not navigation

## Risks / Trade-offs

**[Risk] LLM validation may have false negatives** (real articles marked as not-articles)
- Mitigation: Conservative prompt - when uncertain, classify as article
- Mitigation: `skipped` articles can be manually reset to `pending` if needed

**[Risk] Validation adds latency to extraction**
- Mitigation: Minimal - just prompt text changes, same API call count

**[Risk] Improved Stage 1 prompt may reduce recall**
- Mitigation: Better to miss some articles than flood with non-articles
- Mitigation: Monitor discovery counts after deployment

**[Trade-off] Non-article stubs remain in database**
- Acceptable: Prevents re-discovery, provides audit trail
- Can be periodically cleaned if desired (manual process)
