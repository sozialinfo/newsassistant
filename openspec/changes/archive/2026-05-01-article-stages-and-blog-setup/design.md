## Context

The `newsassistant` module manages articles through a kanban stage pipeline. Currently the stages are: New, Relevant (seq 20), Archived (seq 30, folded), Discarded (seq 40, folded). The `newsassistant_blog` extension auto-publishes relevant articles to an Odoo blog and hardcodes stage XML IDs (`news_article_stage_relevant`, `news_article_stage_discarded`) directly in the pipeline code.

Neither module has a `res.config.settings` extension, so the only way to change pipeline behaviour is to edit code. The target blog is also stored in `ir.config_parameter` but never auto-initialized on install.

Since the module is not in production, no migration scripts are needed — a clean reinstall is sufficient after the changes.

## Goals / Non-Goals

**Goals:**
- Replace "Relevant" → "Shortlist" and "Archived" → "Published" (clean data, no migration)
- Add `res.config.settings` to `newsassistant` core for configuring the default new-article stage
- Add stage configuration (shortlist, published, discard) + blog configuration to `newsassistant_blog` settings
- Wire the digest pipeline to read all three stages from settings at runtime
- Auto-initialize stages and "News" blog on `newsassistant_blog` install via `post_init_hook`

**Non-Goals:**
- Migration of existing production data
- Making stages user-creatable from the install hook UI (hook only links existing or creates missing standard ones)
- Changing any other pipeline logic (AI calls, Pixabay, etc.)

## Decisions

### D1: Delete old stages, create new ones (no rename)

**Decision:** Remove `news_article_stage_relevant` and `news_article_stage_archived` from `news_article_stage_data.xml` and add `news_article_stage_shortlist` and `news_article_stage_published`.

**Rationale:** Since there is no production data, a clean slate is simpler and avoids confusion from mismatched XML IDs. Renaming in-place would leave the XML ID (`_relevant`) inconsistent with the displayed name ("Shortlist").

**Alternative considered:** Rename label only, keep XML ID — rejected because it creates a permanent inconsistency between ID and meaning.

### D2: Settings use Many2one fields backed by ir.config_parameter

**Decision:** `res.config.settings` fields for stages are `Many2one("news.article.stage")` with `config_parameter` attribute, storing the record ID as a string.

**Rationale:** This is the standard Odoo pattern for persisting relational config. It gives a dropdown UI in settings automatically and survives stage record ID changes across reinstalls as long as the config parameter is updated by the hook.

**Alternative considered:** Store XML external IDs as strings — rejected because it adds complexity and is not the Odoo convention.

### D3: post_init_hook in newsassistant_blog for auto-setup

**Decision:** A `post_init_hook` in `newsassistant_blog/__manifest__.py` points to `hooks.py:post_init_hook`. It:
1. Finds "Shortlist" stage by name → links as shortlist_stage; if not found, creates it
2. Finds "Published" stage by name → links as published_stage; if not found, creates it
3. Finds "Discarded" stage by name → links as discard_stage; if not found, creates it
4. Finds `blog.blog(name="News")` → links as blog; if not found, creates it

**Rationale:** This makes `newsassistant_blog` self-contained. Installing it on any `newsassistant` instance (even one with different stage names) will always result in a working configuration.

**Alternative considered:** Data XML with `noupdate="1"` to set config parameters — rejected because it cannot query existing records conditionally.

### D4: Pipeline reads stages from ir.config_parameter at runtime

**Decision:** `_handle_discard()`, `_handle_relevant()` (now `_handle_shortlist()`), and `_create_blog_post()` each call a helper `_get_stage(param_key)` that reads the stage ID from `ir.config_parameter` and returns the `news.article.stage` browse record. If the parameter is unset, fall back to searching by name.

**Rationale:** Keeps pipeline methods clean and ensures they always respect the current settings, even after a user changes the configuration post-install.

### D5: newsassistant core gets its own res.config.settings extension

**Decision:** New file `newsassistant/models/res_config_settings.py` extends `res.config.settings` with a single `Many2one` field `newsassistant_new_article_stage_id` using `config_parameter="newsassistant.new_article_stage_id"`. The `news.article._default_stage_id()` method reads this parameter.

**Rationale:** Decouples the hardcoded default from the XML ID, allowing administrators to change the initial stage without code changes.

## Risks / Trade-offs

- **Stage lookup by name in hook is locale-sensitive** → Mitigation: hook searches by name with the English string; since this runs at install time before any locale switch, it is safe. The stages are also created by the core module's data XML in English.
- **If ir.config_parameter is cleared**, the pipeline will fall back to name-based lookup, which is robust but adds a DB query → acceptable trade-off for resilience.
- **Settings Many2one fields could reference a deleted stage** → Mitigation: stages should not be deleted by users; no special guard needed for this scope.

## Migration Plan

1. No migration scripts required.
2. Uninstall `newsassistant_blog` and `newsassistant`, then reinstall both.
3. The `post_init_hook` runs automatically and seeds all config values.
4. The Makefile `rebuild` target handles the full clean-slate cycle.
