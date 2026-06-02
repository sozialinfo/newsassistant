# News Assistant - Strategy Base

**Version:** 18.0.1.0.0  
**License:** LGPL-3

Base module providing the shared `strategy.strategy` model plus unified strategy evaluation infrastructure.

## Features

- Strategy management: define strategies with PDF documents, date ranges
- Prompt tab shell for sister module prompt injection
- AI-powered prompt distillation from PDF content
- Unified cron dispatches evaluation to all installed sister modules
- `strategy.distill.confirm` wizard with overwrite protection

## Models

### strategy.strategy

| Field | Type | Description |
|-------|------|-------------|
| `name` | Char | Strategy name |
| `state` | Selection | Draft / Active / Archived |
| `date_from` | Date | Valid from |
| `date_to` | Date | Valid until |
| `description` | Text | Optional notes |
| `document_ids` | Many2many | Linked PDF attachments |
| `prompt` | Text | Extensible prompt tab (sister modules inject here) |

### strategy.distill.confirm

Wizard model for confirming prompt overwrite during distillation.

## Security

| Group | Access |
|-------|--------|
| `newsassistant_group_user` | Read, Create, Write `strategy.strategy` |
| `newsassistant_group_admin` | Full CRUD on `strategy.strategy` |
| `newsassistant_group_user` | Read+Write `strategy.distill.confirm` |

## Configuration

No post-install configuration required. Strategy records are created via **News Assistant → Strategies**.

## Dependencies

- `newsassistant` — base module
- `queue_job` — background job processing

## License

LGPL-3