## ADDED Requirements

### Requirement: Pretty URL paths for actions

The system SHALL define a `path` field on all window actions to enable Odoo 18 path-based routing. Each action's path SHALL be unique and follow the pattern `[a-z][a-z0-9_-]*`.

#### Scenario: Articles action has pretty URL
- **WHEN** user navigates to the Articles menu
- **THEN** the URL SHALL be `/odoo/articles`

#### Scenario: Article form view has pretty URL
- **WHEN** user opens article with ID 61
- **THEN** the URL SHALL be `/odoo/articles/61`

#### Scenario: Sources action has pretty URL
- **WHEN** user navigates to the Sources menu
- **THEN** the URL SHALL be `/odoo/sources`

#### Scenario: Source form view has pretty URL
- **WHEN** user opens source with ID 5
- **THEN** the URL SHALL be `/odoo/sources/5`

#### Scenario: Pipeline monitor has pretty URL
- **WHEN** user navigates to Pipeline Monitor
- **THEN** the URL SHALL be `/odoo/pipeline-monitor`

### Requirement: Action path configuration

The following actions SHALL have path fields configured:
- `news_article_action`: path = "articles"
- `news_source_action`: path = "sources"
- `pipeline_monitor_action`: path = "pipeline-monitor"

#### Scenario: Path values are valid
- **WHEN** the module is loaded
- **THEN** all action paths SHALL match the pattern `[a-z][a-z0-9_-]*`
- **THEN** all action paths SHALL be unique across the system
