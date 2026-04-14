## ADDED Requirements

### Requirement: Jina fetch returns images alongside content
The `fetch_page()` function SHALL request JSON format from Jina Reader API with image summary enabled, returning both markdown content and an images dictionary.

#### Scenario: Successful fetch with images
- **WHEN** `fetch_page(url)` is called
- **THEN** the function SHALL return a tuple `(content, images_dict)`
- **THEN** `content` SHALL contain the markdown text
- **THEN** `images_dict` SHALL contain image URLs keyed by label

#### Scenario: Page has no images
- **WHEN** `fetch_page(url)` is called for a page without images
- **THEN** the function SHALL return `(content, {})` with an empty images dictionary

### Requirement: Article model has header_image field
The `news.article` model SHALL have a `header_image` Binary field to store the extracted header image.

#### Scenario: Header image stored on article
- **WHEN** a valid header image is found during extraction
- **THEN** the image binary data SHALL be stored in `news.article.header_image`
- **THEN** the image SHALL be accessible for display in views

#### Scenario: No suitable image found
- **WHEN** no image passes validation during extraction
- **THEN** `news.article.header_image` SHALL remain empty/False

### Requirement: Extract and validate images during article scraping
The `_fetch_and_extract()` method SHALL process images from Jina response and store the first valid one as the article's header image.

#### Scenario: First valid image selected
- **WHEN** multiple images are returned from Jina
- **THEN** the system SHALL validate images in order
- **THEN** the first image passing all validation criteria SHALL be stored
- **THEN** remaining images SHALL NOT be processed

#### Scenario: All images fail validation
- **WHEN** all images fail validation criteria
- **THEN** article extraction SHALL complete successfully without a header image
- **THEN** a log entry SHALL note that no suitable image was found

### Requirement: Validate image format
The system SHALL only accept JPEG, PNG, or WebP images as header images.

#### Scenario: Accepted image formats
- **WHEN** an image has Content-Type `image/jpeg`, `image/png`, or `image/webp`
- **THEN** the image SHALL proceed to dimension validation

#### Scenario: Rejected image formats
- **WHEN** an image has Content-Type for SVG, GIF, ICO, or other formats
- **THEN** the image SHALL be skipped without downloading

### Requirement: Validate image dimensions
The system SHALL require minimum dimensions of 1000x400 pixels for header images.

#### Scenario: Image meets minimum dimensions
- **WHEN** an image has width >= 1000 pixels AND height >= 400 pixels
- **THEN** the image SHALL proceed to orientation validation

#### Scenario: Image too small
- **WHEN** an image has width < 1000 pixels OR height < 400 pixels
- **THEN** the image SHALL be rejected

### Requirement: Validate image orientation
The system SHALL require landscape orientation (width > height) for header images.

#### Scenario: Landscape image accepted
- **WHEN** an image has width > height
- **THEN** the image SHALL be accepted if other criteria are met

#### Scenario: Portrait or square image rejected
- **WHEN** an image has width <= height
- **THEN** the image SHALL be rejected

### Requirement: Skip non-content images by URL pattern
The system SHALL skip images whose URLs suggest they are not content images (logos, icons, etc.) without downloading them.

#### Scenario: Logo/icon URLs skipped
- **WHEN** an image URL contains "logo", "icon", "footer", "avatar", "sprite", or "button"
- **THEN** the image SHALL be skipped without downloading

#### Scenario: SVG extension skipped
- **WHEN** an image URL ends with ".svg"
- **THEN** the image SHALL be skipped without downloading

### Requirement: Display header image in Kanban view
The article Kanban view SHALL display the header image when available.

#### Scenario: Article with header image
- **WHEN** viewing an article card in Kanban view
- **THEN** the header image SHALL be displayed on the card

#### Scenario: Article without header image
- **WHEN** viewing an article card without a header image
- **THEN** the card SHALL display without an image placeholder
