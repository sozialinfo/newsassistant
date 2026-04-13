## ADDED Requirements

### Requirement: Blog post link to source article
The system SHALL extend `blog.post` with a `news_article_id` field (Many2one → news.article) to track which article generated the blog post.

#### Scenario: Blog post linked to article
- **WHEN** a blog post is created from a relevant article
- **THEN** the `news_article_id` SHALL reference the source `news.article`

#### Scenario: Traceability from blog to article
- **WHEN** viewing a blog post in the backend
- **THEN** the linked news article SHALL be accessible via the `news_article_id` field

### Requirement: Automatic blog post creation
The system SHALL automatically create a `blog.post` record when an article is marked as `relevant` and teaser generation succeeds. The blog post SHALL be published immediately (`is_published = True`).

#### Scenario: Blog post created for relevant article
- **WHEN** an article is marked `relevant` AND teaser generation succeeds
- **THEN** a `blog.post` SHALL be created in the configured target blog
- **THEN** the blog post SHALL have `is_published = True`

#### Scenario: No blog post for uncertain article
- **WHEN** an article is marked `uncertain`
- **THEN** no blog post SHALL be created

#### Scenario: No blog post for discarded article
- **WHEN** an article is marked `discard`
- **THEN** no blog post SHALL be created

### Requirement: Blog post content structure
The system SHALL create blog posts with: the article title as post name, the generated teaser as the main content, and a link to the original source URL.

#### Scenario: Blog post has article title
- **WHEN** a blog post is created from an article
- **THEN** the `name` field SHALL be the article title

#### Scenario: Blog post contains teaser and source link
- **WHEN** a blog post is created from an article
- **THEN** the `content` field SHALL include the generated teaser text
- **THEN** the `content` field SHALL include a link to the original article URL
- **THEN** the link SHALL indicate the source domain (e.g., "Read the full article at example.ch")

### Requirement: Deduplication of blog posts
The system SHALL NOT create duplicate blog posts for the same article. Before creating a blog post, the system SHALL check if a blog post with the same `news_article_id` already exists.

#### Scenario: No duplicate blog post
- **WHEN** the digest processes an article that already has a blog post
- **THEN** no new blog post SHALL be created
- **THEN** the existing blog post SHALL remain unchanged

### Requirement: Target blog configuration
The system SHALL publish blog posts to the blog specified by the `newsfeed.blog_id` system parameter. If not configured, blog post creation SHALL fail gracefully.

#### Scenario: Blog post created in configured blog
- **WHEN** `newsfeed.blog_id` is set to blog ID 3
- **THEN** new blog posts SHALL be created with `blog_id = 3`

#### Scenario: Missing blog configuration
- **WHEN** `newsfeed.blog_id` is not set or invalid
- **THEN** blog post creation SHALL be skipped
- **THEN** an error SHALL be logged
- **THEN** the article SHALL still be marked as relevant in the kanban
