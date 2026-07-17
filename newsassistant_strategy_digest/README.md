# News Assistant — Strategy Digest

Strategy-aware article labelling and AI-generated executive briefs for News Assistant.

## Overview

This addon adds strategic intelligence on top of the News Assistant pipeline. You define named
strategies (e.g. "Digital Transformation", "Poverty Reduction") with supporting PDF documents and
a description. The AI distils an evaluation prompt from those documents, then automatically labels
newly extracted articles with matching strategy labels. At any time you can generate an AI executive
brief covering a selected date range and export it as a PDF using the company's paper format.

Requires `newsassistant` (base module).

## Features

- **Strategy labels**: coloured kanban tags that can be assigned to articles manually or automatically
- **Strategy management**: define strategies with PDF documents, date ranges, and labels; AI distils an evaluation prompt from the documents
- **Automatic article evaluation**: an hourly cron assigns strategy labels to all articles that have not yet been evaluated
- **Manual re-evaluation**: re-evaluate a single article or a batch from the list view
- **Strategy digest**: AI-generated HTML executive brief covering labelled articles in a selected date range
- **PDF export**: print the brief using the company's paper format and logo

## Pipeline

### Strategy setup (one-time per strategy)

```
strategy.strategy
    ├─▶ Upload PDF documents + write description
    └─▶ action_distill_prompt()
            ├─▶ _distill_gather_content()     [extract text from PDFs + description]
            ├─▶ _distill_call_ai()            [AI generates labels and evaluation prompt]
            └─▶ _distill_save_labels_prompt() [creates strategy.label records, saves prompt]
```

### Article evaluation (hourly cron)

```
ir.cron (hourly)
    └─▶ news.article._cron_strategy_eval_impl()
            └─▶ [per article with strategy_eval_state = pending]
                    └─▶ article.with_delay()._evaluate_strategy_labels()
                            └─▶ [per active strategy]
                                    └─▶ _evaluate_against_strategy(strategy)
                                            └─▶ AI decides which labels apply
```

### Digest generation (on demand)

```
strategy.digest
    └─▶ action_generate_brief()
            ├─▶ _get_active_strategies_for_period()
            ├─▶ _get_articles_for_period()       [labelled articles in date range]
            ├─▶ _build_brief_prompt()
            └─▶ _call_ai()                       [generates HTML executive brief]
```

## Configuration

### 1. Create strategies

Go to **Strategy Digest → Configuration → Strategies**:

1. Click **New** and give the strategy a name.
2. Set an optional **Valid From / Valid To** date range (leave blank for open-ended).
3. Write a **Description** explaining the strategy's focus.
4. Attach **PDF Documents** if you have strategy papers, reports, or guidelines.
5. Click **Distill Prompt** to let the AI extract labels and build an evaluation prompt.
6. Review the generated labels and prompt; adjust if needed.
7. Click **Activate** to make the strategy live — the hourly cron will now evaluate articles against it.

### 2. Generate a digest

Go to **Strategy Digest → Digests**:

1. Click **New**.
2. Set a **Name**, **Date From**, and **Date To**.
3. Click **Generate Brief**.
4. Review the AI-generated HTML brief in the **Brief** field.
5. Click **Print Brief** to export a PDF using the company's paper format.

## Usage

### View labelled articles

In the article kanban or list view, strategy labels appear as coloured tags on each article card.
Filter or group by label to see articles relevant to a specific strategy.

### Re-evaluate a single article

Open an article and click **Re-evaluate Strategy Labels**. The AI re-runs the evaluation for all
active strategies and updates the labels immediately (synchronous, not queued).

### Re-evaluate in bulk

In the article list view, select multiple articles, then **Action → Re-evaluate Strategy Labels**.
Jobs are enqueued for each selected article.

### Manage labels

Labels are created automatically during **Distill Prompt**, but can also be created manually at
**Strategy Digest → Configuration → Labels**. Labels can be shared across multiple strategies.

## Error Handling

| Condition | Behaviour |
|---|---|
| No active strategies | Evaluation skipped; article stays `pending` |
| PDF text extraction fails | Strategy built from description only; warning logged |
| AI returns no labels | Article saved with no labels; `strategy_eval_state` set to `processed` |
| Digest has no labelled articles in range | Brief generated with a note that no relevant articles were found |
| AI call fails (transient) | `RetryableJobError` — evaluation job retried with escalating delay |

## Security

| Group | Access |
|---|---|
| `newsassistant.newsassistant_group_user` | Read labels; create and edit strategies and digests (no delete) |
| `newsassistant.newsassistant_group_admin` | Full access including delete |

## Dependencies

- `newsassistant` — base module (required)
- `queue_job` — OCA background job processing (required)
- `INFOMANIAK_AI_API_KEY` — environment variable (required)
- `pdfminer.six` — Python package for PDF text extraction (must be installed in the Odoo container)

## Testing

```bash
docker compose run --rm odoo odoo \
    -d test_newsassistant_$(date +%s) \
    -i newsassistant_strategy_digest \
    --test-enable \
    --test-tags=/newsassistant_strategy_digest \
    --stop-after-init
```

## License

LGPL-3
