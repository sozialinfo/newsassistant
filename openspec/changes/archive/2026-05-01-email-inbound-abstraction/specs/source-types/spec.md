## ADDED Requirements

### Requirement: Source type field
The `news.source` model SHALL have a `source_type` field (Selection: `website` | `email`, required, default=`website`). The type SHALL determine which module handles content capture for that source.

#### Scenario: Create website source
- **WHEN** a user creates a news source without specifying type
- **THEN** `source_type` SHALL default to `website`

#### Scenario: Create email source
- **WHEN** a user creates a news source with type `email`
- **THEN** the source SHALL be saved with `source_type='email'`

### Requirement: Source type drives form view
The news source form view SHALL show type-specific fields based on `source_type`. Website sources SHALL show the URL field. Email sources SHALL show the sender domain field instead of URL.

#### Scenario: Website source shows URL field
- **WHEN** a user views a source with `source_type='website'`
- **THEN** the `url` field SHALL be visible and editable

#### Scenario: Email source shows domain field
- **WHEN** a user views a source with `source_type='email'`
- **THEN** the sender domain field SHALL be visible
- **THEN** the website URL field SHALL NOT be shown

### Requirement: Email source domain field
Email-type news sources SHALL have a `sender_domain` field (Char) representing the email domain (e.g. `substack.com`) used to match incoming emails to this source.

#### Scenario: Email source has sender domain
- **WHEN** an email source is created with sender_domain "substack.com"
- **THEN** inbound emails from any address @substack.com SHALL be routed to this source

### Requirement: Source type filter in list view
The news source list view search SHALL include a filter for source type (website | email).

#### Scenario: Filter by email sources
- **WHEN** a user applies the "Email Sources" filter
- **THEN** only sources with `source_type='email'` SHALL be displayed
