## Context

When a URL is validated and determined to not be an article (e.g., it's a category page, index page, etc.), the system marks it as `skipped` and creates a `news.log` record. Currently, this log is created with `level="warning"`, but skipping non-articles is expected behavior - not an anomaly requiring attention.

Current code in `news_article.py` line ~322:
```python
self._create_log(
    level="warning",  # Should be "info"
    message=f"Skipped (not an article): {self.title[:50]}",
    ...
)
```

## Goals / Non-Goals

**Goals:**
- Change skipped article log level from `warning` to `info`
- Update specs to reflect the correct log level requirement

**Non-Goals:**
- Changing log levels for actual errors or anomalies
- Modifying log vacuum behavior (accepting that skipped logs may now be vacuumed)

## Decisions

### Decision 1: Use `info` level for skipped articles

**Choice**: Change log level from `warning` to `info`.

**Rationale**:
- Skipping non-articles is the system working correctly, not a warning condition
- `info` level is appropriate for "successfully processed, result was skip"
- Keeps warning/error levels meaningful for actual problems

**Alternative considered**: Keep `warning` but add filtering in log views.
→ Rejected: Doesn't address the semantic incorrectness of the log level.

### Decision 2: Accept log vacuum implications

**Choice**: Allow skipped article logs to be subject to normal vacuum rules.

**Rationale**:
- Per unified-logging spec, only `warning` and `error` logs are exempt from vacuum
- Skipped articles are routine - no need for permanent retention
- Vacuum keeps the log table manageable

## Risks / Trade-offs

**[Trade-off] Historical skipped article logs may be vacuumed**
→ Acceptable: Skipped articles remain in `news.article` table; log retention is for debugging, not audit.
