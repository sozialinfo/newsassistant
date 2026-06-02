# News Assistant - Strategy Watch

**Version:** 18.0.1.0.0  
**License:** LGPL-3

Strategy impact detection: flags articles with strategic watch relevance using AI evaluation against watch prompts.

## Features

- **Watch prompt** per strategy: AI-generated prompt for detecting strategic impact
- **Article watch flagging**: boolean star toggle on kanban cards
- **Automatic evaluation**: articles evaluated against active strategies' watch prompts
- **Kanban star**: clickable `boolean_favorite` star widget
- **Search filters**: filter by watch status and pending evaluation state

## Models

### news.article (extended)

| Field | Type | Description |
|-------|------|-------------|
| `strategy_watch` | Boolean | Whether article is on strategy watch |
| `strategy_watch_state` | Selection | Pending / Processed |
| `strategy_watch_reasoning` | Text | AI reasoning for watch evaluation |

### strategy.strategy (extended)

| Field | Type | Description |
|-------|------|-------------|
| `watch_prompt` | Text | AI-generated watch evaluation prompt |

## Pipeline

```
_strategy_eval_cron (daily)
    └─▶ article._evaluate_strategies()
            └─▶ article._evaluate_strategy_watch()
                    ├─▶ strategy._call_ai()        [evaluate article relevance]
                    └─▶ mark article.strategy_watch = True/False
```

## Security

| Group | Access |
|-------|--------|
| `newsassistant_group_user` | Read+Write extended news.article fields |
| `newsassistant_group_admin` | Full access |

ACLs are inherited from `newsassistant` and `newsassistant_strategy`.

## Configuration

No post-install configuration required. Watch prompts are auto-generated via the Distill Prompts button on each strategy.

## Dependencies

- `newsassistant` — base module
- `newsassistant_strategy` — shared strategy model

## License

LGPL-3