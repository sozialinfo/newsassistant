## ADDED Requirements

### Requirement: User security group

The system SHALL define a security group `newsassistant_group_user` with name "User" in the News Assistant category. This group SHALL have read/write access to `news.article`, `news.source`, and `news.article.stage` models.

#### Scenario: User group access to articles

- **WHEN** a user in `newsassistant_group_user` accesses articles
- **THEN** the user SHALL be able to read, create, edit, and delete articles

#### Scenario: User group access to sources

- **WHEN** a user in `newsassistant_group_user` accesses sources
- **THEN** the user SHALL be able to read, create, edit, and delete sources

### Requirement: Admin security group

The system SHALL define a security group `newsassistant_group_admin` with name "Admin" in the News Assistant category. This group SHALL imply `newsassistant_group_user`. This group SHALL have additional access to `news.source.log` and `news.article.log` models (read only).

#### Scenario: Admin group implies user

- **WHEN** a user is added to `newsassistant_group_admin`
- **THEN** the user SHALL automatically be a member of `newsassistant_group_user`

#### Scenario: Admin group access to logs

- **WHEN** a user in `newsassistant_group_admin` accesses scrape logs
- **THEN** the user SHALL be able to read `news.source.log` and `news.article.log` records

### Requirement: Admin-only UI elements

The following UI elements SHALL be visible only to users in `newsassistant_group_admin`:
- "Scrape Now" button on source form
- "Re-fetch", "Skip", "Reset" buttons on article form
- "Scrape Status" section on source form
- "Extraction Status" section on article form
- "Scrape History" section on source form
- "Extraction History" section on article form
- "Pipeline Monitor" menu item
- "Scrape Selected" server action on source list
- "Re-fetch Selected", "Mark as Skipped", "Reset to Pending" server actions on article list

#### Scenario: Admin sees debug tools

- **WHEN** an admin views a source form
- **THEN** "Scrape Now" button, "Scrape Status" section, and "Scrape History" section SHALL be visible

#### Scenario: User does not see debug tools

- **WHEN** a regular user views a source form
- **THEN** "Scrape Now" button, "Scrape Status" section, and "Scrape History" section SHALL NOT be visible

### Requirement: State filters visible to all

The state filters on article and source list views SHALL be visible to all users (both user and admin groups).

#### Scenario: User can filter by state

- **WHEN** a regular user views the article list
- **THEN** filters for Pending, Scraped, Error, Skipped states SHALL be available

### Requirement: Module category

The system SHALL define a module category "News Assistant" for grouping the security groups in the user settings interface.

#### Scenario: Groups appear in settings

- **WHEN** an administrator configures user access rights
- **THEN** "News Assistant" category SHALL appear with "User" and "Admin" group options
