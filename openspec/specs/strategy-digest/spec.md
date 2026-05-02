## ADDED Requirements

### Requirement: Strategy digest model
The system SHALL provide a `strategy.digest` model with fields: `name` (Char, required), `date_from` (Date, required), `date_to` (Date, required), `strategy_ids` (Many2many → `strategy.strategy`), `article_ids` (Many2many → `news.article`), `brief` (Html, AI-generated), `state` (Selection: `draft` / `done`, default `draft`). The `strategy_ids` and `article_ids` are populated automatically when generating the brief, but can also be edited manually.

#### Scenario: Create a new digest record
- **WHEN** a user creates a new strategy digest with name and date range
- **THEN** the record SHALL be saved with state = draft
- **THEN** strategy_ids and article_ids SHALL be initially empty

#### Scenario: Digest date range is required
- **WHEN** a user attempts to save a digest without date_from or date_to
- **THEN** the system SHALL raise a validation error

### Requirement: Automatic strategy and article resolution
The system SHALL provide a method that, given the digest's `date_from` and `date_to`, resolves: (a) all active `strategy.strategy` records whose date range overlaps the digest period (or that have no dates), and (b) all `news.article` records with at least one `strategy_label_ids` entry and a `date` within the period.

#### Scenario: Resolve strategies for period
- **WHEN** the digest period is Jan–Dec 2026
- **THEN** strategies with no dates SHALL be included
- **THEN** strategies overlapping the period SHALL be included
- **THEN** strategies entirely outside the period SHALL be excluded

#### Scenario: Resolve articles for period
- **WHEN** the digest period is Jan–Dec 2026
- **THEN** only articles with date within the period AND at least one strategy_label_ids SHALL be included
- **THEN** articles outside the date range SHALL be excluded
- **THEN** articles with no strategy labels SHALL be excluded

### Requirement: Generate AI brief
The system SHALL provide an action button "Generate Brief" on the `strategy.digest` form. When triggered, it SHALL: resolve strategies and articles for the period, construct a prompt including strategy names/prompts and article summaries (title, summary, source, date), call the AI (qwen3 via Infomaniak), and store the returned HTML in `brief`. The brief SHALL be in the language of the current user (`self.env.user.lang`). The prompt SHALL instruct the AI to produce an executive summary and a detailed analysis with footnote-style source references, targeting no more than 2 A4 pages of content. Article titles and source names are kept in their original language; only the AI-generated prose is in the user's language.

#### Scenario: Generate brief with articles and strategies
- **WHEN** a user clicks "Generate Brief" on a digest with resolved articles and strategies
- **THEN** the system SHALL call the AI with the article and strategy data
- **THEN** the AI-generated HTML SHALL be stored in the `brief` field
- **THEN** the digest state SHALL be set to `done`
- **THEN** the strategy_ids and article_ids fields SHALL be populated

#### Scenario: Generate brief with no articles in period
- **WHEN** a user clicks "Generate Brief" but no labelled articles exist in the period
- **THEN** the system SHALL raise a UserError informing the user
- **THEN** the brief SHALL NOT be overwritten

#### Scenario: Brief regeneration is allowed
- **WHEN** a user clicks "Generate Brief" on a digest already in state done
- **THEN** the system SHALL regenerate the brief (overwrite)
- **THEN** the state SHALL remain done

#### Scenario: Brief language follows user language
- **WHEN** the current user's language is set to German (de_DE)
- **THEN** the AI prose in the brief SHALL be in German
- **THEN** article titles and source names SHALL remain in their original language

### Requirement: Strategy digest list and form views
The system SHALL provide a list view and a form view for `strategy.digest` accessible via a new "Strategy Digest" top-level menu item (or sub-menu under News Assistant). The list view SHALL show name, date_from, date_to, and state. The form view SHALL display all fields including the HTML brief editor.

#### Scenario: Navigate to strategy digests
- **WHEN** a user clicks "Strategy Digest" in the menu
- **THEN** the list view of strategy.digest records SHALL be displayed

#### Scenario: Brief is editable after generation
- **WHEN** a user opens a digest in state done
- **THEN** the `brief` Html field SHALL be editable (not readonly)
- **THEN** the user MAY freely edit the generated text

### Requirement: PDF export of strategy digest
The system SHALL provide a QWeb PDF report for `strategy.digest`. The report SHALL use `t-call="web.external_layout"` to inherit company logo, fonts, brand colours, header, and footer. The `ir.actions.report` record SHALL NOT set `paperformat_id`, so it falls back to `env.company.paperformat_id` (configured via General Settings → Configure Document Layout). The report SHALL include: digest name and period as title, executive summary section, detailed analysis section with source footnotes, and a list of referenced articles with URLs.

#### Scenario: Export digest to PDF
- **WHEN** a user clicks the Print / Download PDF action on a strategy.digest record
- **THEN** a PDF SHALL be generated using the company's configured paper format
- **THEN** the PDF SHALL include the company logo and branding from company settings
- **THEN** the PDF SHALL show the digest name, period, and the generated brief content

#### Scenario: Paper format follows company settings
- **WHEN** the company is configured with US Letter paper format
- **THEN** the exported PDF SHALL use US Letter dimensions
- **WHEN** the company is configured with A4 paper format
- **THEN** the exported PDF SHALL use A4 dimensions

#### Scenario: PDF includes article source list
- **WHEN** the brief references articles with footnotes
- **THEN** the PDF SHALL include a sources section listing each referenced article's title, source name, date, and URL
