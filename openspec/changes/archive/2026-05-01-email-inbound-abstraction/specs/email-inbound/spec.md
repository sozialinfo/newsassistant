## ADDED Requirements

### Requirement: Email inbound module
The system SHALL provide a `newsassistant_email` module that depends on `newsassistant` and `mail`. This module SHALL implement Odoo's inbound email aliasing for `news.snapshot`.

#### Scenario: Module installs independently
- **WHEN** `newsassistant_email` is installed alongside `newsassistant`
- **THEN** inbound email capture functionality SHALL be available
- **THEN** the base module SHALL function without `newsassistant_email`

### Requirement: Inbound email alias on news.snapshot
The `newsassistant_email` module SHALL configure a `mail.alias` for the `news.snapshot` model. The alias name SHALL be configurable via Settings (default: `newsassistant`). All emails sent to `<alias>@<domain>` SHALL be processed to create `news.snapshot` records.

#### Scenario: Email received at alias creates snapshot
- **WHEN** an email is sent to `newsassistant@companydomain.com`
- **THEN** a `news.snapshot` record SHALL be created with the email body HTML as `raw_content`

#### Scenario: Alias name is configurable
- **WHEN** an admin changes the alias name in Settings to "newsletters"
- **THEN** emails sent to `newsletters@companydomain.com` SHALL be processed
- **THEN** the old alias SHALL no longer receive emails

### Requirement: Sender domain routing
When an inbound email is received, the system SHALL extract the sender's domain from the `From` header and look up a `news.source` record with `source_type='email'` and matching `sender_domain`.

#### Scenario: Known sender domain routes to existing source
- **WHEN** an email arrives from `newsletter@techcrunch.com`
- **THEN** the system SHALL look up a source with `sender_domain='techcrunch.com'`
- **THEN** the snapshot SHALL be created with that source's `source_id`

#### Scenario: Unknown sender domain creates new source
- **WHEN** an email arrives from `hello@unknownnewsletter.com` with no matching source
- **THEN** a new `news.source` record SHALL be created with `source_type='email'` and `sender_domain='unknownnewsletter.com'`
- **THEN** the snapshot SHALL be linked to the newly created source

### Requirement: AI-based source naming for auto-created sources
When a new `news.source` is auto-created from an incoming email, the system SHALL call the Infomaniak AI API to determine the publication name from the sender domain. If the AI call fails or returns an unusable response, the domain name SHALL be used as the source name.

#### Scenario: AI names new email source
- **WHEN** an email from `digest@morningbrew.com` triggers auto-source creation
- **THEN** the system SHALL call AI with the sender domain `morningbrew.com`
- **THEN** the new source `name` SHALL be set to the AI-returned publication name (e.g. "Morning Brew")

#### Scenario: AI naming fallback to domain
- **WHEN** the AI call fails or returns an empty response
- **THEN** the new source `name` SHALL be set to the sender domain (e.g. "morningbrew.com")

### Requirement: Email HTML sanitization before storage
Before storing email body HTML in `news.snapshot.raw_content`, the system SHALL sanitize it to remove scripts, tracking pixels, excessive inline styles, and non-content elements (navigation, footer divs).

#### Scenario: Email HTML is sanitized
- **WHEN** an email body contains `<script>` tags and tracking pixel `<img>` elements
- **THEN** the stored `raw_content` SHALL NOT contain `<script>` tags
- **THEN** the stored `raw_content` SHALL NOT contain tracking pixel images (1x1 px images)

### Requirement: Email alias settings
The `newsassistant_email` module SHALL add a settings section for email configuration including the alias name field.

#### Scenario: Admin configures email alias
- **WHEN** an admin opens Settings and navigates to News Assistant
- **THEN** an "Email Alias" field SHALL be visible and editable
- **THEN** saving the settings SHALL update the mail alias name
