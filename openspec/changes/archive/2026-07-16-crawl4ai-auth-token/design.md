## Context

crawl4ai currently has no auth. The `fetch_page()` function sends a simple POST request. When running on a separate server, we need to support JWT Bearer token authentication.

## Decisions

**Decision 1: Token field in Settings UI**
- Stored as `ir.config_parameter` key `newsassistant_website.crawl4ai_api_token`
- Password field in the UI (masked input)
- Same pattern as Pixabay API key

**Decision 2: Optional auth**
- If token is empty, no auth header is sent (backward compatible)
- If token is set, `Authorization: Bearer <token>` is added to all crawl4ai requests