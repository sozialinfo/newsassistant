## 1. Blog module — field string labels

- [x] 1.1 In `newsassistant_blog/models/news_article.py`: change `digest_state` field `string=` from `"Digest State"` to `"Evaluation Status"`

## 2. Strategy module — field string labels and reset logic

- [x] 2.1 In `newsassistant_strategy_digest/models/news_article.py`: change `strategy_eval_state` field `string=` from `"Strategy Eval State"` to `"Evaluation Status"`
- [x] 2.2 In `newsassistant_strategy_digest/models/news_article.py`: change `strategy_reasoning` field `string=` from `"Strategy Reasoning"` to `"Reasoning"`
- [x] 2.3 In `newsassistant_strategy_digest/models/news_article.py`: in `action_reevaluate_strategy_labels`, add `strategy_label_ids = [(5, False, False)]` to the write call that resets the state, so existing labels are cleared before re-evaluation

## 3. Strategy module — view consistency

- [x] 3.1 In `newsassistant_strategy_digest/views/news_article_views.xml`: add `invisible="state != 'scraped'"` to the Strategy Evaluate button (matching the Blog tab)
- [x] 3.2 In `newsassistant_strategy_digest/views/news_article_views.xml`: add `title="Re-evaluate this article against all active strategies"` to the Strategy Evaluate button (matching Blog's tooltip pattern)
