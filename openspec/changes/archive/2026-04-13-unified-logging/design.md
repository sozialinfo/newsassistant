## Context

The current logging infrastructure consists of:
- `news.source.log` - records one entry per Stage 1 listing scrape (status, duration, articles_found)
- `news.article.log` - records one entry per Stage 2 article extraction (status, duration)
- `news.pipeline.monitor` - transient model showing aggregate counts (sources with errors, pending articles, etc.)

Problems:
1. **No LLM visibility**: Calls to Infomaniak AI are completely opaque - no prompts, responses, or token counts logged
2. **Coarse granularity**: Only final outcomes are logged, not intermediate steps (Jina fetch, LLM call, parsing)
3. **Fragmented data**: Two separate log tables make it hard to see the full picture
4. **Pipeline Monitor is shallow**: Just computed counts, not actionable operational data
5. **No running job visibility**: No easy way to see what's currently executing

The `_call_infomaniak_ai` method returns only the response content string, discarding the full API response including token usage data.

## Goals / Non-Goals

**Goals:**
- Unified logging model that captures both source and article operations
- Two-tier logging: summary (one per operation) + details (multiple per operation)
- Full LLM interaction capture: prompts, responses, token usage, timing
- Admin log browser with filtering by source, article, job, level, category
- Running jobs visibility in multiple places (menu, logs view, source list indicator)
- Automatic cleanup of successful operation details after 1 day

**Non-Goals:**
- Migration of existing log data (will be lost)
- Real-time log streaming / live updates (standard Odoo refresh is sufficient)
- Cost tracking based on token usage (could be added later)
- Logging outside the scraping pipeline (e.g., user actions)

## Decisions

### Decision 1: Two-model architecture (news.log + news.log.entry)

**Choice**: Separate summary and detail models with 1:N relationship

**Rationale**: 
- Summary stays forever for audit trail and analytics
- Details can be vacuumed for successful operations without losing the summary
- Cleaner than a single model with nullable fields or JSON blobs
- Matches the mental model: "one operation" with "multiple steps"

**Alternatives considered**:
- Single model with JSON metadata field - harder to query details, vacuum would delete entire records
- Detailed logging only - too verbose, no quick overview possible

### Decision 2: Modify _call_infomaniak_ai to return structured response

**Choice**: Return a dict with `content`, `usage`, and timing instead of just the content string

**Rationale**:
- The Infomaniak API already returns `usage.prompt_tokens`, `usage.completion_tokens`, `usage.total_tokens`
- Current code discards this - simple change to preserve it
- Callers can extract content with `response["content"]` (minimal change)

**Alternatives considered**:
- Separate logging call after AI call - would require re-parsing the response or passing it around
- Global logging context - too magical, harder to trace

### Decision 3: Computed is_scraping field on news.source

**Choice**: Compute by querying queue.job for started jobs referencing this source

**Rationale**:
- Always accurate, no sync issues
- Performance acceptable for typical source list sizes (<100 sources)
- Simpler than maintaining stored state across job start/end

**Alternatives considered**:
- Stored field updated by job hooks - faster reads but risks inconsistency if job crashes

### Decision 4: Vacuum using ir.autovacuum

**Choice**: Standard Odoo autovacuum with rule: delete `news.log.entry` records where parent log is `success` and older than 1 day

**Rationale**:
- Native Odoo mechanism, runs automatically
- Keeps error/warning details forever for debugging
- 1 day gives enough time to investigate issues

**Alternatives considered**:
- Cron job with custom delete logic - more code, same result
- Keep all details forever - storage bloat, especially with full LLM prompts/responses

### Decision 5: Log level on summary is final outcome only

**Choice**: `success`, `warning`, `error` based on operation result, not highest severity of entries

**Rationale**:
- An operation can have intermediate warnings but still succeed
- Summary level should answer "did this operation work?"
- Detail entries capture the journey, summary captures the destination

### Decision 6: Admin-only access for logs and running jobs

**Choice**: New menu items and log views restricted to `newsassistant.newsassistant_group_admin`

**Rationale**:
- Logs may contain sensitive data (prompts, article content)
- Consistent with existing History tab visibility
- Regular users don't need operational visibility

## Risks / Trade-offs

**[Storage growth from full LLM logging]** → Mitigated by vacuum rule deleting success details after 1 day. Monitor storage if many errors accumulate.

**[Performance of is_scraping computed field]** → Acceptable for <100 sources. If source count grows significantly, reconsider with stored field + job hooks.

**[Breaking change - existing logs lost]** → Acceptable for this internal tool. No migration planned. Communicate to users that history resets.

**[Complexity of two-model logging in code]** → Provide helper method `_create_log()` on both news.source and news.article that handles summary + entries creation cleanly.
