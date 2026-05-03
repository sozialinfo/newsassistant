## 1. Base Module — HTML Utility

- [x] 1.1 Create `newsassistant/models/utils.py` with `html_to_markdown(html)` using BeautifulSoup4 (p/br→newlines, li→`- `, h1-h6→`#`, strong/b→`**`, em/i→`*`, strip all other tags)
- [x] 1.2 Add `from . import utils` to `newsassistant/models/__init__.py`
- [x] 1.3 Write tests for `html_to_markdown()` in `newsassistant/tests/test_utils.py` covering: plain text passthrough, paragraph→newlines, list items, headings, bold/italic, nested tags, empty string, None input

## 2. Strategy Model — State Field and Wizards

- [x] 2.1 Add `state = fields.Selection([('draft','Draft'),('active','Active'),('archived','Archived')], default='draft')` to `strategy.strategy`
- [x] 2.2 Add `action_activate()` method: if prompt set → write state=active; if no prompt but content → open `strategy.activate.confirm` wizard; if no content → raise UserError
- [x] 2.3 Add `action_set_draft()` method: write state=draft unconditionally
- [x] 2.4 Add `action_archive()` method: write state=archived unconditionally
- [x] 2.5 Create transient model `strategy.activate.confirm` (wizard): message field (Char), `action_distill_and_activate()` method that calls `action_distill_prompt()` then sets state=active
- [x] 2.6 Create transient model `strategy.distill.confirm` (wizard): `action_confirm_distill()` method that calls the actual distillation logic

## 3. Strategy Model — HTML Prompt

- [x] 3.1 Change `prompt` field from `fields.Text(readonly=True)` to `fields.Html()` (remove readonly)
- [x] 3.2 Update `action_distill_prompt()` to wrap AI-returned plain text in `<p>` tags before writing to `prompt`
- [x] 3.3 Update `action_distill_prompt()` to check if prompt already set → open `strategy.distill.confirm` wizard instead of running distillation directly
- [x] 3.4 Update `action_distill_prompt()` to be callable directly (bypassing wizard) for use by `strategy.activate.confirm`

## 4. Strategy Views

- [x] 4.1 Add statusbar to form `<header>`: `<field name="state" widget="statusbar" statusbar_visible="draft,active,archived"/>`
- [x] 4.2 Add state badge to list view
- [x] 4.3 Rename notebook tab from "AI Labelling Prompt" to "Prompt"
- [x] 4.4 Remove "Distill Prompt" button from `<header>`
- [x] 4.5 Add explanation text above prompt field in Prompt tab: "This prompt instructs the AI on how to evaluate news articles for this strategy. It is generated from the attached documents and description, but can be edited manually."
- [x] 4.6 Add "Distill Prompt" button inside Prompt tab (always visible)
- [x] 4.7 Create form view for `strategy.activate.confirm` wizard
- [x] 4.8 Create form view for `strategy.distill.confirm` wizard
- [x] 4.9 Register wizard views in manifest data

## 5. Digest and Article Evaluation — Active Filter + HTML Conversion

- [x] 5.1 Update `strategy_digest._get_active_strategies_for_period()` to filter `state = 'active'` in the search domain
- [x] 5.2 Update `strategy_digest._build_brief_prompt()`: import and apply `html_to_markdown()` on `strategy.prompt` before appending to prompt text (and remove `[:500]` truncation that would cut HTML tags mid-string — apply truncation after conversion)
- [x] 5.3 Update `news_article._evaluate_for_strategy()` in `newsassistant_strategy_digest`: import and apply `html_to_markdown()` on `strategy.prompt` in system_prompt construction
- [x] 5.4 Replace `re.sub(r"<[^>]+>", " ", self.content)` in `news_article._evaluate_for_strategy()` with `html_to_markdown(self.content)` from the utility

## 6. Active Strategy Filter in Article Evaluation Cron

- [x] 6.1 Verify that `news_article._run_strategy_evaluation_for_article()` uses strategies resolved via `_get_active_strategies_for_period()` or equivalent — update any direct `strategy.strategy` search to include `('state', '=', 'active')` filter

## 7. Demo Data

- [x] 7.1 Update `demo/strategy_strategy_demo.xml` to set `state="active"` on all demo strategies so fresh instance works end-to-end

## 8. Tests

- [x] 8.1 Add tests for `action_activate()`: prompt set → activates; no prompt + content → wizard returned; no prompt + no content → UserError
- [x] 8.2 Add tests for `action_set_draft()` and `action_archive()`
- [x] 8.3 Add tests for `strategy.activate.confirm` wizard: `action_distill_and_activate()` calls distill then sets active
- [x] 8.4 Add tests for `strategy.distill.confirm` wizard: confirm runs distillation; cancel leaves prompt unchanged
- [x] 8.5 Add tests for overwrite confirmation: distill when prompt set → wizard opened; wizard confirm → distillation runs; wizard cancel → prompt unchanged
- [x] 8.6 Add tests for HTML prompt storage: distill writes `<p>...</p>` HTML; prompt field accepts HTML; empty label names skipped; utils 100% coverage
- [x] 8.7 Add tests for `_get_active_strategies_for_period()` filtering: draft/archived strategies excluded; active strategies included
- [x] 8.8 Add tests for HTML→MD conversion in digest `_build_brief_prompt()`: HTML prompt converted before LLM call
- [x] 8.9 Add tests for HTML→MD conversion in article evaluation: HTML prompt converted; content HTML stripped via utility
- [x] 8.10 Add tests for state badge display: verify state field values and selection values

## 9. Translations

- [x] 9.1 Extract POT, update `i18n/de.po` and `i18n/fr.po` for `newsassistant_strategy_digest` with new strings (state labels, wizard messages, explanation text, button labels)
- [x] 9.2 Update `i18n/de.po` and `i18n/fr.po` for `newsassistant` base module if new translatable strings added in utils
