## ADDED Requirements

### Requirement: Articles support archive/unarchive
The system SHALL support archiving and unarchiving articles using Odoo's standard `active` field pattern. Archived articles SHALL be hidden from default list and kanban views.

#### Scenario: Archive an article
- **WHEN** user archives an article (via Action menu or list action)
- **THEN** the article's `active` field is set to False
- **AND** the article disappears from the default article list

#### Scenario: View archived articles
- **WHEN** user applies the "Archived" filter in search view
- **THEN** archived articles are displayed in the list

#### Scenario: Unarchive an article
- **WHEN** user unarchives an article
- **THEN** the article's `active` field is set to True
- **AND** the article appears in the default article list
- **AND** the article's `state` remains unchanged

### Requirement: Skipped articles are automatically archived
The system SHALL automatically archive articles when they are marked as skipped, whether by AI detection or manual action.

#### Scenario: AI detects non-article content
- **WHEN** the AI extraction determines content is not a valid article
- **THEN** the article state is set to "skipped"
- **AND** the article is archived (active=False)
- **AND** the status_message contains the skip reason

#### Scenario: User manually skips an article
- **WHEN** user triggers the Skip action on an article
- **THEN** the article state is set to "skipped"
- **AND** the article is archived (active=False)

### Requirement: Archived articles are used for URL deduplication
The system SHALL check ALL articles (including archived) when determining if a URL already exists during the scraping process.

#### Scenario: URL exists as archived article
- **WHEN** the scraper discovers a URL that matches an archived article
- **THEN** the scraper skips creating a new article for that URL

#### Scenario: URL exists as active article
- **WHEN** the scraper discovers a URL that matches an active article
- **THEN** the scraper skips creating a new article for that URL

### Requirement: Status message field for errors and skip reasons
The system SHALL use a `status_message` field (renamed from `error_message`) to store both error messages and skip reasons.

#### Scenario: Article has extraction error
- **WHEN** article extraction fails with an error
- **THEN** the status_message contains the error description
- **AND** the state is set to "error"

#### Scenario: Article is skipped with reason
- **WHEN** article is skipped (AI or manual)
- **THEN** the status_message contains the skip reason
- **AND** the state is set to "skipped"

### Requirement: Skip status visible in GUI
The system SHALL display the skip status and reason prominently in the article GUI.

#### Scenario: List view shows status message
- **WHEN** viewing articles in list view
- **THEN** the status_message is available as an optional column

#### Scenario: Form view shows skip banner
- **WHEN** viewing a skipped article in form view
- **THEN** a prominent alert/banner displays the skip reason

### Requirement: Admin actions in dropdown menu
The system SHALL provide Re-fetch, Skip, and Reset actions via the Action dropdown menu instead of header buttons.

#### Scenario: Re-fetch from action menu
- **WHEN** admin user opens Action menu on an article
- **THEN** "Re-fetch" action is available (unless article is skipped)
- **AND** selecting it queues a re-fetch job

#### Scenario: Skip from action menu
- **WHEN** admin user opens Action menu on an article
- **THEN** "Skip" action is available (unless article is already skipped)
- **AND** selecting it marks the article as skipped and archives it

#### Scenario: Reset from action menu
- **WHEN** admin user opens Action menu on a skipped article
- **THEN** "Reset" action is available
- **AND** selecting it sets state to pending and clears status_message

### Requirement: Search view includes archive filter
The system SHALL provide an "Archived" filter in the article search view to show archived articles.

#### Scenario: Filter archived articles
- **WHEN** user selects "Archived" filter
- **THEN** only archived articles (active=False) are displayed

#### Scenario: Default view excludes archived
- **WHEN** user views articles without filters
- **THEN** only active articles (active=True) are displayed
