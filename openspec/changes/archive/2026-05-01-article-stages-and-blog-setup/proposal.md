## Why

The news assistant pipeline needs clearly named stages that reflect the editorial workflow (New → Shortlist → Published / Discarded), and both the core and blog modules need configuration options so stage assignments and the target blog are driven by settings rather than hardcoded XML IDs. Without this, the pipeline is inflexible and the blog module cannot be self-contained on install.

## What Changes

- Replace existing "Relevant" stage with a new "Shortlist" stage (delete old, create new)
- Replace existing "Archived" stage with a new "Published" (collapsed) stage (delete old, create new)
- Add `res.config.settings` extension to `newsassistant` core with a configurable "new article stage"
- Add stage configuration fields to `newsassistant_blog` settings: shortlist stage, published stage, discard stage
- Wire the `newsassistant_blog` digest pipeline to read stages from settings instead of hardcoded XML IDs
- Add `post_init_hook` to `newsassistant_blog`: auto-link (or create) Shortlist/Published/Discard stages in settings
- Add `post_init_hook` to `newsassistant_blog`: auto-create a "News" blog and link it in settings

## Capabilities

### New Capabilities

- `article-stage-config`: Configuration of article stages in `newsassistant` core settings (new article default stage)
- `blog-stage-config`: Configuration of pipeline stages and blog in `newsassistant_blog` settings (shortlist, published, discard stages + target blog)
- `blog-install-hook`: On install of `newsassistant_blog`, auto-resolve/create the required stages and a "News" blog, and store them in settings

### Modified Capabilities

- `article-stages`: Stage set changes — "Relevant" replaced by "Shortlist", "Archived" replaced by "Published" (collapsed)

## Impact

- `newsassistant/data/news_article_stage_data.xml` — updated stage records
- `newsassistant/models/` — new `res_config_settings.py`
- `newsassistant/views/` — new settings view XML + menu entry
- `newsassistant_blog/models/res_config_settings.py` — new stage fields (shortlist, published, discard)
- `newsassistant_blog/models/news_article.py` — pipeline methods read stages from settings
- `newsassistant_blog/__manifest__.py` — add `post_init_hook`
- `newsassistant_blog/hooks.py` — new file with install hook logic
- Tests for both modules updated to reflect new stages and settings-driven pipeline
