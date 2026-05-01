## ADDED Requirements

### Requirement: New article stage setting in core module
The `newsassistant` module SHALL extend `res.config.settings` with a `newsassistant_new_article_stage_id` field (Many2one → `news.article.stage`) backed by `ir.config_parameter` key `newsassistant.new_article_stage_id`. The default stage for new articles SHALL be read from this parameter.

#### Scenario: Admin configures default new article stage
- **WHEN** admin opens Settings and navigates to the News Assistant section
- **THEN** a "Default Stage for New Articles" field SHALL be visible
- **THEN** admin SHALL be able to select any existing `news.article.stage` record

#### Scenario: New article uses configured stage as default
- **WHEN** a new `news.article` is created and no stage is specified
- **THEN** the `stage_id` SHALL default to the stage configured in `newsassistant.new_article_stage_id`
- **THEN** if the parameter is not set, the system SHALL fall back to the "New" stage by name

#### Scenario: Changing the setting affects new articles
- **WHEN** admin changes the default new article stage in settings
- **THEN** subsequently created articles SHALL use the newly configured stage
- **THEN** existing articles SHALL NOT be affected
