## ADDED Requirements

### Requirement: Pixabay API key configuration
The system SHALL provide a configuration option for the Pixabay API key in Settings.

#### Scenario: API key configured via Settings UI
- **WHEN** an administrator navigates to Settings
- **THEN** a "Pixabay API Key" field SHALL be available in the Newsfeed section
- **THEN** the value SHALL be stored as system parameter `newsassistant_blog.pixabay_api_key`

#### Scenario: API key not configured
- **WHEN** `newsassistant_blog.pixabay_api_key` is empty or not set
- **THEN** Pixabay fallback SHALL be skipped
- **THEN** a warning SHALL be logged indicating the missing API key

### Requirement: Search Pixabay using article title
The system SHALL use the article title as search query when fetching fallback images from Pixabay.

#### Scenario: Search request format
- **WHEN** querying Pixabay for a fallback image
- **THEN** the request SHALL use the article title as the `q` parameter
- **THEN** the request SHALL specify `orientation=horizontal`
- **THEN** the request SHALL specify `image_type=photo`

#### Scenario: Title with special characters
- **WHEN** the article title contains special characters or non-ASCII text
- **THEN** the search query SHALL be properly URL-encoded

### Requirement: Select suitable Pixabay image
The system SHALL select the first Pixabay result meeting the minimum dimension requirements.

#### Scenario: Suitable result found
- **WHEN** Pixabay returns images meeting 1000x400 minimum dimensions
- **THEN** the system SHALL download from the `largeImageURL` field
- **THEN** the first suitable result SHALL be used

#### Scenario: No suitable results
- **WHEN** Pixabay returns no results OR all results are below minimum dimensions
- **THEN** the system SHALL proceed without a fallback image
- **THEN** a warning SHALL be logged

### Requirement: Handle Pixabay API errors gracefully
The system SHALL handle Pixabay API errors without failing blog post creation.

#### Scenario: API timeout
- **WHEN** the Pixabay API request times out (10 seconds)
- **THEN** the system SHALL proceed without a fallback image
- **THEN** an error SHALL be logged with timeout details

#### Scenario: Rate limit exceeded
- **WHEN** Pixabay returns HTTP 429 (rate limit)
- **THEN** the queue job SHALL raise RetryableJobError with 60-second delay

#### Scenario: Other API errors
- **WHEN** Pixabay returns a non-200, non-429 response
- **THEN** the system SHALL proceed without a fallback image
- **THEN** an error SHALL be logged with response details

### Requirement: Store Pixabay source reference
The system SHALL record the Pixabay source in attachment metadata when using a Pixabay image.

#### Scenario: Pixabay image used
- **WHEN** a Pixabay image is attached to a blog post
- **THEN** the attachment description SHALL indicate "Source: Pixabay"
- **THEN** the Pixabay page URL SHALL be stored for reference
