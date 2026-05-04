# News Assistant — Strategy Digest

Strategy-aware article labelling and AI-generated executive briefs for News Assistant.

## Features

- Strategy labels: coloured tags for strategic relevance (managed in Configuration)
- Strategy management: define strategies with PDF documents, date ranges, and labels
- AI prompt distillation: extract text from strategy PDFs and generate a labelling prompt
- Automatic article evaluation: cron job evaluates articles against active strategies
- Strategy digest: AI-generated HTML executive brief for a selected period
- PDF export of the brief using the company paper format

## Models

### strategy.label

| Field | Type | Description |
|-------|------|-------------|
| `name` | Char | Label name (translateable) |
| `color` | Integer | Kanban colour index |

### strategy.strategy

| Field | Type | Description |
|-------|------|-------------|
| `name` | Char | Strategy name |
| `state` | Selection | draft / active / archived |
| `date_from` | Date | Valid from (optional) |
| `date_to` | Date | Valid to (optional) |
| `description` | Text | Free-text strategy description |
| `document_ids` | Many2many | PDF strategy documents |
| `label_ids` | Many2many | Labels for this strategy |
| `prompt` | Html | AI-generated evaluation prompt |

### strategy.digest

| Field | Type | Description |
|-------|------|-------------|
| `name` | Char | Digest name |
| `date_from` | Date | Period start |
| `date_to` | Date | Period end |
| `strategy_ids` | Many2many | Active strategies in period |
| `article_ids` | Many2many | Strategy-labelled articles in period |
| `brief` | Html | AI-generated executive brief |
| `state` | Selection | draft / done |

### news.article (extended)

| Field | Type | Description |
|-------|------|-------------|
| `strategy_label_ids` | Many2many | Assigned strategy labels |
| `strategy_eval_state` | Selection | pending / processed |

## Security

| Group | Access |
|-------|--------|
| `newsassistant.newsassistant_group_user` | Read labels; create/edit strategies and digests (no delete) |
| `newsassistant.newsassistant_group_admin` | Full access including delete |

## Configuration

1. Create strategies in **Strategy Digest → Configuration → Strategies**
2. Upload PDF documents or add a description
3. Click **Distill Prompt** to generate labels and evaluation prompt
4. Set strategy state to **Active** to include it in evaluations
5. The evaluation cron runs hourly and assigns labels to newly scraped articles

## Dependencies

- `newsassistant` — base module
- `queue_job` — OCA background job processing
- `INFOMANIAK_AI_API_KEY` — environment variable (required)
- `pdfminer.six` — Python package for PDF text extraction (required)

## License

LGPL-3
