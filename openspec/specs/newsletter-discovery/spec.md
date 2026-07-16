## ADDED Requirements

### Requirement: Newsletter article section discovery
When a listing snapshot is created from an inbound newsletter email, the `newsassistant_email` module's `_discover_articles()` override SHALL send the newsletter HTML to the AI to identify individual article sections. For each section, the system SHALL create a child snapshot containing that section's HTML content.

#### Scenario: Newsletter with 6 articles creates 6 child snapshots
- **WHEN** a newsletter email containing 6 articles is received and `_discover_articles()` runs
- **THEN** the AI SHALL be called with the newsletter HTML to split it into article sections
- **THEN** the AI SHALL return a JSON array of objects, each with `title` and `content` fields
- **THEN** 6 child snapshots SHALL be created, one per article section
- **THEN** each child snapshot's `parent_id` SHALL point to the listing snapshot
- **THEN** each child snapshot's `raw_content` SHALL contain the article section HTML

#### Scenario: Newsletter child snapshot enqueues extraction
- **WHEN** a child snapshot is created from a newsletter article section
- **THEN** a queue job for `_extract_articles()` SHALL be enqueued for the child snapshot
- **THEN** the child snapshot SHALL be processed as a single article (existing pipeline)

#### Scenario: Newsletter with no identifiable articles
- **WHEN** the AI cannot identify any article sections in the newsletter
- **THEN** no child snapshots SHALL be created
- **THEN** a `news.log` record SHALL be created with level `warning`

### Requirement: Newsletter discovery AI prompt
The AI prompt for newsletter section discovery SHALL instruct the model to identify individual articles within the newsletter HTML and return a JSON array of `{title, content}` objects. The content field SHALL contain the article's HTML as it appears in the newsletter.

#### Scenario: AI prompt handles newsletter structure
- **WHEN** `_discover_articles()` is called on a newsletter listing snapshot
- **THEN** the AI system prompt SHALL be specific to newsletter article extraction
- **THEN** the prompt SHALL NOT use the `/no_think` prefix (the existing convention for single-article extraction remains unchanged)