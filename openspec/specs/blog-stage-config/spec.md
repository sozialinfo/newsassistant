## ADDED Requirements

### Requirement: Blog pipeline stage settings
The `newsassistant_blog` module SHALL extend `res.config.settings` with three stage configuration fields, each backed by `ir.config_parameter`:

- `newsassistant_blog_shortlist_stage_id` (Many2one → `news.article.stage`, key: `newsassistant_blog.shortlist_stage_id`) — stage for articles needing human review
- `newsassistant_blog_published_stage_id` (Many2one → `news.article.stage`, key: `newsassistant_blog.published_stage_id`) — stage for articles auto-published to the blog
- `newsassistant_blog_discard_stage_id` (Many2one → `news.article.stage`, key: `newsassistant_blog.discard_stage_id`) — stage for articles discarded by the pipeline

#### Scenario: Admin configures pipeline stages
- **WHEN** admin opens Settings and navigates to the Newsassistant Blog section
- **THEN** three stage fields SHALL be visible: Shortlist Stage, Published Stage, Discard Stage
- **THEN** each field SHALL allow selecting any `news.article.stage` record

#### Scenario: Digest pipeline uses shortlist stage
- **WHEN** the AI evaluates an article as relevant (human review needed / shortlisted)
- **THEN** the article's `stage_id` SHALL be set to the configured shortlist stage

#### Scenario: Digest pipeline uses published stage
- **WHEN** the pipeline successfully creates a blog post for an article
- **THEN** the article's `stage_id` SHALL be set to the configured published stage

#### Scenario: Digest pipeline uses discard stage
- **WHEN** the AI evaluates an article as discard
- **THEN** the article's `stage_id` SHALL be set to the configured discard stage

### Requirement: Default blog setting
The `newsassistant_blog` module SHALL store the target blog in `ir.config_parameter` key `newsassistant_blog.blog_id` and expose it as `newsfeed_blog_id` (Many2one → `blog.blog`) in `res.config.settings`.

#### Scenario: Admin configures target blog
- **WHEN** admin opens Settings → Newsassistant Blog
- **THEN** a "Target Blog" field SHALL be visible
- **THEN** admin SHALL be able to select any existing `blog.blog` record
