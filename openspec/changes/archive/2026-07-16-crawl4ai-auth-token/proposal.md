## Why

When crawl4ai runs on a separate server, the API endpoint needs authentication. Add a configurable API token field to the Settings UI so users can secure the crawl4ai connection.

## What Changes

- **New** `newsassistant_crawl4ai_api_token` field in `res.config.settings`
- **Modified** `fetch_page()` in `crawl4ai_utils.py` to include `Authorization: Bearer <token>` header when token is set
- **Modified** Settings view to include the API token field

## Capabilities

### New Capabilities
- `crawl4ai-auth`: Configurable API token for crawl4ai server authentication

### Modified Capabilities
- `crawl4ai-fetching`: fetch_page() now sends Bearer token when configured

## Impact

- `newsassistant_website/models/res_config_settings.py` — add api_token field
- `newsassistant_website/models/crawl4ai_utils.py` — add Authorization header support
- `newsassistant_website/views/res_config_settings_views.xml` — add token field to UI
- `newsassistant_website/tests/test_crawl4ai_utils.py` — test auth header behavior