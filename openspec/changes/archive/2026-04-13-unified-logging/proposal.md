## Why

The current logging infrastructure is fragmented and insufficient. Separate `news.source.log` and `news.article.log` tables track only final outcomes without visibility into intermediate steps. LLM interactions (prompts, responses, token usage) are completely invisible. The Pipeline Monitor provides only aggregate counts without actionable detail. Debugging failures requires piecing together information from multiple places.

## What Changes

- **BREAKING**: Remove Pipeline Monitor (`news.pipeline.monitor`) entirely
- **BREAKING**: Replace `news.source.log` and `news.article.log` with unified `news.log` model
- Add `news.log.entry` model for detailed step-by-step logging within each operation
- Log LLM interactions with full prompts, responses, and token usage
- Rename "History" tabs to "Log" tabs on Source and Article forms
- Add admin-only "Logs" menu with filtering/grouping capabilities
- Add admin-only "Running Jobs" menu showing active queue jobs
- Add computed "scraping" indicator on Sources list
- Add vacuum rule to clean up detail entries for successful logs after 1 day

## Capabilities

### New Capabilities
- `unified-logging`: Centralized logging with two-tier model (summary + details), LLM interaction capture, admin log browser, and running jobs visibility

### Modified Capabilities
- `scrape-history`: Replace with unified logging - "History" tabs become "Log" tabs using new `news.log` model
- `pipeline-monitor`: Remove entirely - functionality replaced by unified logging admin views

## Impact

- **Models**: Delete `news.pipeline.monitor`, `news.source.log`, `news.article.log`. Create `news.log`, `news.log.entry`.
- **Views**: Update Source/Article forms (History → Log tabs). Delete Pipeline Monitor views. Create Logs and Running Jobs admin views.
- **Menu**: Remove Pipeline Monitor menu. Add Logs and Running Jobs menus.
- **Security**: Update access rules for new models, admin-only access for log browser.
- **Data**: Existing log data in `news.source.log` and `news.article.log` will be lost (migration not planned).
- **Code**: Modify `_scrape_listing` and `_fetch_and_extract` to use new logging. Modify `_call_infomaniak_ai` to return usage data.
