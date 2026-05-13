## 1. Strategy Model — reasoning field and LLM update

- [ ] 1.1 Add `strategy_reasoning` Text field to `newsassistant_strategy_digest/models/news_article.py`
- [ ] 1.2 Update `_evaluate_against_strategy` AI prompt to request a `"reasoning"` key in the JSON response
- [ ] 1.3 Accumulate reasoning per strategy in `_evaluate_strategy_labels` and write to `strategy_reasoning`
- [ ] 1.4 Reset `strategy_reasoning` to False in `action_reevaluate_strategy_labels`

## 2. Strategy View — new Strategy tab

- [ ] 2.1 Remove `<group string="Strategy">` from main body in `newsassistant_strategy_digest/views/news_article_views.xml`
- [ ] 2.2 Remove "Re-evaluate" stat button from `button_box` in the same view
- [ ] 2.3 Add Strategy tab after the Blog tab (xpath after Blog page) with: eval state badge + Re-evaluate button inline, reasoning group (invisible when empty), labels field
- [ ] 2.4 Add list view column for `strategy_eval_state` (optional) if not already showing

## 3. Blog View — move button into tab

- [ ] 3.1 Remove "Digest Now" button from `<header>` in `newsassistant_blog/views/news_article_views.xml`
- [ ] 3.2 Add "Digest Now" button inline next to `digest_state` badge inside the Blog tab

## 4. Snapshot View — Content tab rename and reorder

- [ ] 4.1 In `newsassistant/views/news_snapshot_views.xml`: rename "Raw Content" tab to "Content", remove `groups` restriction, move it before the "Articles" tab

## 5. Version bumps

- [ ] 5.1 Bump `newsassistant_strategy_digest` version in `__manifest__.py` (data model change → major bump)
- [ ] 5.2 Bump `newsassistant_blog` version in `__manifest__.py` (view change → minor bump)
- [ ] 5.3 Bump `newsassistant` version in `__manifest__.py` (view change → minor bump)
