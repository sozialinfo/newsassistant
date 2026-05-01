## ADDED Requirements

### Requirement: Auto-link stages on newsassistant_blog install
When `newsassistant_blog` is installed, the system SHALL automatically find the standard stages (Shortlist, Published, Discarded) by name and store their IDs in the corresponding `ir.config_parameter` keys. If a standard stage is not found by name, the system SHALL create it and then store its ID.

#### Scenario: Standard stages exist at install time
- **WHEN** `newsassistant_blog` is installed and stages named "Shortlist", "Published", and "Discarded" already exist
- **THEN** the system SHALL link them as shortlist_stage, published_stage, and discard_stage in settings
- **THEN** no new stages SHALL be created

#### Scenario: Standard stages do not exist at install time
- **WHEN** `newsassistant_blog` is installed and the standard stage names are not found
- **THEN** the system SHALL create the missing stages with appropriate sequence and fold values
- **THEN** the newly created stages SHALL be linked in settings

#### Scenario: Some stages exist and some do not
- **WHEN** `newsassistant_blog` is installed and only some standard stages exist
- **THEN** existing stages SHALL be linked, missing ones SHALL be created and linked

### Requirement: Auto-create "News" blog on newsassistant_blog install
When `newsassistant_blog` is installed, the system SHALL check if a `blog.blog` record named "News" exists. If it does, it SHALL be linked as the default blog in settings. If it does not, the system SHALL create it and link it.

#### Scenario: "News" blog already exists at install time
- **WHEN** `newsassistant_blog` is installed and a blog named "News" already exists
- **THEN** that blog SHALL be linked as the default blog in settings
- **THEN** no duplicate blog SHALL be created

#### Scenario: "News" blog does not exist at install time
- **WHEN** `newsassistant_blog` is installed and no blog named "News" exists
- **THEN** a new `blog.blog` record named "News" SHALL be created
- **THEN** that new blog SHALL be linked as the default blog in settings
