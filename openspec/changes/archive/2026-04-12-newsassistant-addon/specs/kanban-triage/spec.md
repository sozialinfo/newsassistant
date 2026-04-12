## ADDED Requirements

### Requirement: Article stage model
The system SHALL provide a `news.article.stage` model with fields: `name` (Char, required, translatable), `sequence` (Integer), and `fold` (Boolean, default False). Default stages SHALL be created via data XML: New (sequence 10, not folded), Relevant (sequence 20, not folded), Archived (sequence 30, folded), Discarded (sequence 40, folded).

#### Scenario: Default stages exist after install
- **WHEN** the module is installed
- **THEN** four stages SHALL exist: New, Relevant, Archived, Discarded
- **THEN** stages SHALL be ordered by sequence

#### Scenario: Archived and Discarded are folded
- **WHEN** the kanban view is rendered
- **THEN** the Archived and Discarded columns SHALL be folded by default

### Requirement: Article model
The system SHALL provide a `news.article` model with fields: `title` (Char, required), `source_id` (Many2one → news.source, required), `url` (Char, required, indexed), `date` (Date), `summary` (Text), `content` (Text), `stage_id` (Many2one → news.article.stage, default: "New" stage), `scrape_date` (Datetime).

#### Scenario: New article gets default stage
- **WHEN** a new `news.article` record is created without specifying a stage
- **THEN** the `stage_id` SHALL default to the "New" stage

### Requirement: Kanban view for articles
The system SHALL provide a kanban view for `news.article` grouped by `stage_id`. Each kanban card SHALL display: title (bold/prominent), source name, article date, and a truncated summary (first ~200 characters). Users SHALL be able to drag cards between stages.

#### Scenario: View articles in kanban
- **WHEN** the user navigates to the News Articles menu
- **THEN** articles SHALL be displayed in a kanban view grouped by stage
- **THEN** each card SHALL show title, source name, date, and truncated summary

#### Scenario: Drag article to different stage
- **WHEN** the user drags an article card from "New" to "Relevant"
- **THEN** the article's `stage_id` SHALL be updated to "Relevant"

### Requirement: Article form view
The system SHALL provide a form view for `news.article` displaying all fields. The `content` field SHALL be displayed prominently as the main reading area. The form SHALL be read-only by default (articles are created by the scraper, not manually).

#### Scenario: Read article content
- **WHEN** the user clicks on a kanban card
- **THEN** a form view SHALL open showing the full article content, title, source, date, summary, and url

### Requirement: Article list view
The system SHALL provide a list (tree) view for `news.article` showing title, source name, date, stage, and scrape date. The list SHALL support filtering by source, stage, and date range.

#### Scenario: Filter articles by source
- **WHEN** the user filters the article list by a specific source
- **THEN** only articles from that source SHALL be displayed

#### Scenario: Filter articles by stage
- **WHEN** the user filters by the "Relevant" stage
- **THEN** only articles in the "Relevant" stage SHALL be displayed

### Requirement: Menu structure
The system SHALL provide a top-level menu "News Assistant" with sub-menus: "Articles" (default, opens kanban view), "Sources" (opens list view of sources).

#### Scenario: Navigate to articles
- **WHEN** the user clicks "News Assistant" → "Articles"
- **THEN** the kanban view of articles SHALL be displayed

#### Scenario: Navigate to sources
- **WHEN** the user clicks "News Assistant" → "Sources"
- **THEN** the list view of news sources SHALL be displayed
