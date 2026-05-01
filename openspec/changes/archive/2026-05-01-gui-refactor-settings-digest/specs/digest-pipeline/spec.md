## MODIFIED Requirements

### Requirement: Blog tab always visible on article form
The Blog tab in the `news.article` form view (injected by `newsassistant_blog`) SHALL be visible at all times when the module is installed, regardless of whether the article has a teaser. Previously this tab was conditionally hidden when no teaser existed (i.e. for discarded or unprocessed articles). The `blog_reasoning` group inside the tab retains its own `invisible="not blog_reasoning"` guard, so the reasoning section only shows when populated.

#### Scenario: Blog tab visible for discarded article
- **WHEN** an article has been processed by the digest pipeline and discarded (no teaser generated)
- **THEN** the Blog tab SHALL be visible
- **THEN** the `digest_state` badge SHALL show `processed`
- **THEN** the `blog_reasoning` section SHALL be visible if reasoning was recorded

#### Scenario: Blog tab visible for pending article
- **WHEN** an article has not yet been processed by the digest pipeline
- **THEN** the Blog tab SHALL be visible
- **THEN** the `digest_state` badge SHALL show `pending`
- **THEN** the teaser section SHALL be empty

#### Scenario: Blog tab visible for relevant article with teaser
- **WHEN** an article has been processed and a teaser was generated
- **THEN** the Blog tab SHALL be visible
- **THEN** the teaser content SHALL be shown in the Teaser group
