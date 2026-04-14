## MODIFIED Requirements

### Requirement: Create blog post with header image
The `_create_blog_post()` method SHALL attach a header image to the blog post when available, using the article's extracted image or a Pixabay fallback.

#### Scenario: Article has header image
- **WHEN** creating a blog post for an article with `header_image` populated
- **THEN** the image SHALL be stored as an `ir.attachment` linked to the blog post
- **THEN** the blog post's `cover_properties` SHALL reference the attachment

#### Scenario: Article has no header image, Pixabay succeeds
- **WHEN** creating a blog post for an article without `header_image`
- **THEN** the system SHALL query Pixabay for a fallback image
- **THEN** if Pixabay returns a suitable image, it SHALL be attached to the blog post

#### Scenario: Article has no header image, Pixabay fails
- **WHEN** creating a blog post for an article without `header_image`
- **THEN** if Pixabay fails or returns no suitable image
- **THEN** the blog post SHALL be created without a header image
- **THEN** a warning SHALL be logged indicating no image available

#### Scenario: Existing blog post (deduplication)
- **WHEN** a blog post already exists for the article
- **THEN** header image logic SHALL be skipped
- **THEN** the existing blog post SHALL be returned unchanged

### Requirement: Store image as Odoo attachment
The system SHALL store header images as `ir.attachment` records following Odoo's blog cover pattern.

#### Scenario: Attachment creation
- **WHEN** attaching a header image to a blog post
- **THEN** an `ir.attachment` record SHALL be created with:
  - `res_model`: 'blog.post'
  - `res_id`: the blog post ID
  - `datas`: base64-encoded image content
  - `name`: derived from source (article URL filename or "pixabay_header.jpg")
  - `mimetype`: the image's content type

### Requirement: Set blog cover properties
The system SHALL set the blog post's `cover_properties` JSON to display the header image.

#### Scenario: Cover properties format
- **WHEN** a header image attachment is created
- **THEN** `blog.post.cover_properties` SHALL be set to a JSON object containing:
  - `background-image`: `url(/web/image/{attachment_id})`
  - `background_color_class`: default Odoo value
  - `opacity`: default Odoo value
  - `resize_class`: `o_half_screen_height`

### Requirement: Log image source in digest entries
The digest log entries SHALL indicate the source of the header image (article, Pixabay, or none).

#### Scenario: Image from article
- **WHEN** blog post uses the article's extracted header image
- **THEN** log entry SHALL indicate "Header image: from article"

#### Scenario: Image from Pixabay
- **WHEN** blog post uses a Pixabay fallback image
- **THEN** log entry SHALL indicate "Header image: from Pixabay"

#### Scenario: No image available
- **WHEN** blog post is created without a header image
- **THEN** log entry SHALL indicate "Header image: none (no suitable image found)"
