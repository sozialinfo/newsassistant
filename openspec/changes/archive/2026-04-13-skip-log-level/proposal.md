## Why

When an article is skipped (validated as not being an article), the system logs this with level `warning`. However, skipping non-articles is expected, normal behavior - not a warning condition. Using `warning` level pollutes log dashboards and incorrectly suggests something is wrong when the system is working correctly.

## What Changes

- Change the log level for skipped articles from `warning` to `info`
- Update specs to reflect the new log level requirement

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `article-validation`: Change the log level requirement from `warning` to `info` when a URL is validated as not being an article
- `scraping-pipeline`: Change the log level requirement from `warning` to `info` for skipped articles

## Impact

- `addons/newsassistant/models/news_article.py`: Change `level="warning"` to `level="info"` in `_create_log` call for skipped articles
- Log viewing/filtering: Skipped articles will no longer appear in warning-filtered views
- Log retention: Currently, `warning` and `error` logs are exempt from vacuum. Changing to `info` means skipped article logs may be vacuumed. This is acceptable - skipped articles are routine, not noteworthy events requiring permanent retention.
