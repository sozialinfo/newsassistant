## 1. Model — store reasoning for all decisions

- [x] 1.1 In `_handle_discard`: write `blog_reasoning` alongside `stage_id`
- [x] 1.2 In `_handle_uncertain`: write `blog_reasoning` and move to Shortlist stage
- [x] 1.3 In `_handle_shortlist`: remove the `stage_id = shortlist_stage` write (relevant goes directly to Published via `_create_blog_post`)

## 2. Version bump

- [x] 2.1 Bump `newsassistant_blog` version in `__manifest__.py` (behaviour change → minor bump)
