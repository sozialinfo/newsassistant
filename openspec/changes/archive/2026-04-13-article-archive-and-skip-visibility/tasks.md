## 1. Model Changes

- [x] 1.1 Add `active` field to `news.article` model with default=True
- [x] 1.2 Rename `error_message` field to `status_message` in `news.article` model
- [x] 1.3 Update `action_skip()` to set `active=False` along with state
- [x] 1.4 Update `action_reset()` to set `active=True` along with state reset
- [x] 1.5 Update `_fetch_and_extract()` AI skip path to set `active=False`

## 2. Deduplication Fix

- [x] 2.1 Update URL dedup query in `_scrape_listing()` to use `with_context(active_test=False)`

## 3. Migration

- [x] 3.1 Create migration script to rename `error_message` column to `status_message`

## 4. Server Actions

- [x] 4.1 Create `ir.actions.server` for Re-fetch action (admin group, visible when not skipped)
- [x] 4.2 Create `ir.actions.server` for Skip action (admin group, visible when not skipped)
- [x] 4.3 Create `ir.actions.server` for Reset action (admin group, visible when skipped)

## 5. View Updates

- [x] 5.1 Remove header buttons (Re-fetch, Skip, Reset) from article form view
- [x] 5.2 Add `status_message` as optional column in article list view
- [x] 5.3 Add prominent alert/banner in form view for skipped articles showing status_message
- [x] 5.4 Add "Archived" filter to article search view
- [x] 5.5 Update field references from `error_message` to `status_message` in views

## 6. Testing

- [x] 6.1 Run existing tests to verify no regressions
- [x] 6.2 Test archive/unarchive flow manually
- [x] 6.3 Test skip auto-archive behavior
- [x] 6.4 Test dedup with archived articles
