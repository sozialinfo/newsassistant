## ADDED Requirements

### Requirement: Content strategy system parameter
The system SHALL use the `newsassistant_blog.content_strategy` system parameter to store the prompt used for relevance evaluation. This prompt SHALL define what makes an article relevant, uncertain, or discardable.

#### Scenario: Content strategy prompt used for relevance
- **WHEN** the digest evaluates an article's relevance
- **THEN** the system SHALL use the prompt from `newsassistant_blog.content_strategy`
- **THEN** the prompt SHALL be combined with the article content and sent to the LLM

#### Scenario: Content strategy not configured
- **WHEN** `newsassistant_blog.content_strategy` is empty or not set
- **THEN** digest processing SHALL fail with a clear error message
- **THEN** the error SHALL be logged

### Requirement: Teaser prompt system parameter
The system SHALL use the `newsassistant_blog.teaser_prompt` system parameter to store the prompt used for teaser generation. This prompt SHALL define the style and format of generated teasers.

#### Scenario: Teaser prompt used for generation
- **WHEN** the system generates a teaser for a relevant article
- **THEN** the system SHALL use the prompt from `newsassistant_blog.teaser_prompt`

#### Scenario: Teaser prompt not configured
- **WHEN** `newsassistant_blog.teaser_prompt` is empty or not set
- **THEN** teaser generation SHALL fail with a clear error message
- **THEN** the article SHALL still be marked as relevant
- **THEN** no blog post SHALL be created

### Requirement: Target blog system parameter
The system SHALL use the `newsassistant_blog.blog_id` system parameter to specify which blog to publish posts to. The value SHALL be a valid `blog.blog` record ID.

#### Scenario: Valid blog ID configured
- **WHEN** `newsassistant_blog.blog_id` is set to a valid blog ID
- **THEN** blog posts SHALL be created in that blog

#### Scenario: Invalid blog ID configured
- **WHEN** `newsassistant_blog.blog_id` is set but the blog does not exist
- **THEN** blog post creation SHALL fail with a clear error
- **THEN** the error SHALL be logged

### Requirement: Default parameter values
The system SHALL NOT provide default values for content strategy or teaser prompts. These MUST be configured by the user. The module MAY provide example prompts in documentation.

#### Scenario: Module installed without configuration
- **WHEN** the newsassistant_blog module is installed
- **THEN** the digest cron SHALL NOT process any articles until prompts are configured
- **THEN** running digest without configuration SHALL log an error indicating missing configuration
