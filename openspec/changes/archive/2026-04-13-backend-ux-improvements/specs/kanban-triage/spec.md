## MODIFIED Requirements

### Requirement: Article model
The system SHALL provide a `news.article` model with fields: `title` (Char, required), `source_id` (Many2one → news.source, required), `url` (Char, required, indexed), `date` (Date), `summary` (Text), `content` (Text), `stage_id` (Many2one → news.article.stage, default: "New" stage), `scrape_date` (Datetime). The model SHALL set `_rec_name = "title"` to ensure the article title is used as the display name in form headers, breadcrumbs, and Many2one dropdowns.

#### Scenario: New article gets default stage
- **WHEN** a new `news.article` record is created without specifying a stage
- **THEN** the `stage_id` SHALL default to the "New" stage

#### Scenario: Form header shows article title
- **WHEN** user opens an article form view
- **THEN** the header SHALL display the article title (not "news,article,ID")

#### Scenario: Article appears in Many2one with title
- **WHEN** article is referenced in a Many2one field elsewhere
- **THEN** the dropdown SHALL display the article title
