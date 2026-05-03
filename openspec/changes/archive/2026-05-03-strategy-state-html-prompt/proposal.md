## Why

`strategy.strategy` currently has no lifecycle state — every strategy is implicitly "always active," which means draft or obsolete strategies pollute digest generation and article evaluation. The prompt is stored as plain text, limiting rich formatting for complex AI instructions.

## What Changes

- Add `state` field (`draft` / `active` / `archived`) to `strategy.strategy` with a statusbar in the form view and a badge in the list view
- Gate digest generation and article evaluation to `active` strategies only
- Guard activation: a strategy can only be activated if a prompt is set; if not, offer to distill from available documents/description, or block with a clear error
- Change `prompt` field from `fields.Text` (readonly) to `fields.Html` (editable), with HTML→Markdown conversion on the fly when sending to the LLM
- Move the "Distill Prompt" button into the "Prompt" tab (rename tab); add confirmation dialog if overwriting an existing prompt
- Add `html_to_markdown()` utility in the base `newsassistant` module (using BeautifulSoup4); apply it everywhere HTML content is stripped before sending to the LLM

## Capabilities

### New Capabilities
- `strategy-state`: Draft/active/archived lifecycle for strategies, statusbar navigation, activation guard with distill-offer wizard

### Modified Capabilities
- `strategy-management`: Prompt field changes to HTML; tab renamed; button relocated; explanation text added
- `strategy-article-evaluation`: Filters to active strategies only; converts HTML prompt to Markdown before LLM call
- `strategy-digest`: Filters to active strategies only; converts HTML prompt to Markdown before LLM call

## Impact

- `newsassistant_strategy_digest/models/strategy_strategy.py` — new `state` field, new action methods, wizards
- `newsassistant_strategy_digest/views/strategy_strategy_views.xml` — statusbar, tab rename, button move, explanation text
- `newsassistant_strategy_digest/models/strategy_digest.py` — filter active strategies, HTML→MD conversion
- `newsassistant_strategy_digest/models/news_article.py` — filter active strategies, HTML→MD conversion
- `newsassistant/models/utils.py` — new file with `html_to_markdown()` utility
- `newsassistant/__init__.py` — import utils
- New transient models: `strategy.distill.confirm`, `strategy.activate.confirm`
- Translations: DE + FR for new strings
- Tests: new coverage for state transitions, wizards, guard logic, utility function
