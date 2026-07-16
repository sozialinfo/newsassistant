## 1. Settings Model

- [x] 1.1 Add `newsassistant_crawl4ai_api_token` field to `res.config.settings`

## 2. Fetch Utility

- [x] 2.1 Update `fetch_page()` to read token and send Bearer auth header

## 3. Settings View

- [x] 3.1 Add API token field to the settings view XML

## 4. Tests

- [x] 4.1 Add test for auth header when token is set
- [x] 4.2 Add test for no auth header when token is empty

## 5. Deployment

- [x] 5.1 Upgrade the module and restart
- [x] 5.2 Smoke test