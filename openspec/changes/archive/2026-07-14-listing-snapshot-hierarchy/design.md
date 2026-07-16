## Context

Currently, `news.snapshot` has no hierarchy. Every snapshot represents a single fetched page and runs the single-article extraction prompt. For email newsletters, this fails because the AI sees multiple articles and returns `is_article: false`. The website path avoids this by processing the listing page in-memory and never persisting it as a snapshot — it goes straight to per-article snapshots.

The proposal unifies these paths: both website and email sources create a **listing snapshot** first, then discover child snapshots from it.

## Goals / Non-Goals

**Goals:**
- Add `is_listing`, `parent_id`, `child_ids` to `news.snapshot`
- Add `_discover_articles()` base method that raises `NotImplementedError`
- Modify `create()` to skip `_extract_articles()` for listing snapshots, enqueue `_discover_articles()` instead
- Implement `_discover_articles()` in `newsassistant_website` (AI → URLs → crawl4ai → child snapshots)
- Implement `_discover_articles()` in `newsassistant_email` (AI → sections → child snapshots)
- Update `_scrape_listing()` to create and use a listing snapshot
- Update `message_new()` to create a listing snapshot

**Non-Goals:**
- Changing the single-article `_extract_articles()` prompt — child snapshots handle this
- Removing the current email extraction channel (`root.email_extraction`)
- Modifying snapshot views significantly (Phase 2 concern)

## Decisions

### 1. `_discover_articles()` as a protocol method in core
**Choice**: Abstract method in `news.snapshot` core, overridden in website and email modules.
**Rationale**: Keeps the dependency tree clean — core defines the contract, modules implement. No cross-module coupling.

### 2. Listing snapshots skip `_extract_articles()`, enqueue `_discover_articles()` instead
**Choice**: `create()` checks `is_listing` flag and branches.
**Rationale**: Avoids wasted AI calls on listing content. The listing snapshot goes through a different pipeline entirely.

### 3. Website `_scrape_listing()` persists listing snapshot
**Choice**: The listing page content (from crawl4ai) is stored as a listing snapshot.
**Rationale**: Uniformity with email path. Provides audit trail of what the listing looked like at scrape time. Previously this content was discarded after URL extraction.

### 4. Email `_discover_articles()` sends the full newsletter HTML to AI
**Choice**: Single AI call to extract all article sections from the newsletter.
**Rationale**: The newsletter content is already fully inline. No need for separate fetches (unlike website where each URL must be crawled). One AI call returns all sections → child snapshots created per section → each child runs `_extract_articles()` for title/date/summary/content refinement.

### 5. Parent linking via context in website path
**Choice**: `_scrape_listing()` passes listing snapshot ID via context to `_fetch_and_create_snapshot()`.
**Rationale**: `_fetch_and_create_snapshot()` is a separate queue job and needs to know its parent listing. Context is the simplest mechanism for passing the parent ID across job boundaries.

## Risks / Trade-offs

- **[Increased AI cost]** Email `_discover_articles()` adds one AI call per newsletter to split sections. Mitigation: this replaces the current (broken) single-article extraction call, so net AI call count per newsletter increases by ~0 (one split call instead of one failed single-article call).
- **[Increased snapshot count]** Each newsletter creates N+1 snapshots (1 listing + N child sections). Mitigation: snapshots are lightweight (no AI calls on listing), and the hierarchy makes them easy to prune.
- **[Context-passing fragility]** Website path uses context to pass parent ID across job boundaries. Mitigation: context is captured at job creation time and replayed when the job runs — this is standard Odoo queue_job behavior.