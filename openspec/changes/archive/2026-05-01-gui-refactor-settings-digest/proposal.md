## Why

Several UI rough edges have been identified in the News Assistant that reduce usability: the Blog tab on articles is hidden when an article is discarded (making discard reasoning invisible), settings are split across two separate menu entries (confusing for users), prompt input fields are cramped and poorly laid out, and the news source form uses slow inline tabs for logs and snapshots instead of efficient smart buttons. These are all day-to-day usability issues that should be fixed together.

## What Changes

- **Digest — Blog tab always visible**: Remove `invisible="not teaser"` condition so the Blog tab shows on all articles regardless of digest outcome, making discard reasoning accessible.
- **Settings — Single menu**: Merge the `newsassistant_blog` settings app block into the `newsassistant` app block (same view inheritance as email settings), and remove the separate "Blog Settings" menu item. All News Assistant settings appear under one "Settings" menu entry.
- **Settings — Prompt layout**: Place the label on its own line above the textarea and make the field full-width, replacing the current side-by-side layout that makes the textarea small.
- **Settings — Relevance criteria help text**: Expand the help text to explain what auto-publish, human review, and discard mean, so users understand the consequences of their criteria.
- **News source — Remove Log tab**: Replace the inline Log tab with a smart button that navigates to the filtered log list view.
- **News source — Remove Snapshots tab**: Replace the inline Snapshots tab with a smart button that navigates to the filtered snapshot list view.
- **News source — Queue job smart button**: Add a smart button showing active queue job count (admin-only, hidden when zero).
- **News article — Queue job smart button**: Add a smart button showing active queue job count (admin-only, hidden when zero).

## Capabilities

### New Capabilities

- `source-smart-buttons`: Smart buttons on the news source form for logs, snapshots, and active queue jobs replacing the previous tab-based inline views.
- `article-job-button`: Active queue job smart button on the news article form.

### Modified Capabilities

- `digest-pipeline`: Blog tab visibility behavior changes — always shown, not conditional on teaser presence.
- `digest-configuration`: Settings consolidation — blog config merges into the main News Assistant settings block with improved prompt layout and help text.

## Impact

- `newsassistant/models/news_source.py`: New computed fields (`log_count`, `snapshot_count`, `active_job_count`) and action methods.
- `newsassistant/models/news_article.py`: New computed field (`active_job_count`) and action method.
- `newsassistant/views/news_source_views.xml`: Smart buttons added, notebook removed.
- `newsassistant/views/news_article_views.xml`: Button box with active jobs button added.
- `newsassistant_blog/views/news_article_views.xml`: Blog tab `invisible` condition removed; blog post button xpath updated.
- `newsassistant_blog/views/res_config_settings_views.xml`: `inherit_id` changed, app block merged, layout improved, help text updated.
- `newsassistant_blog/views/menu.xml`: "Blog Settings" menu item removed.
- `newsassistant/i18n/de.po`, `fr.po`: New translation entries for new field labels.
