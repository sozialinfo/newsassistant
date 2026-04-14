## Why

Blog posts created from news articles lack visual appeal because they have no header images. Adding header images will improve presentation and engagement. The image should be extracted from the original article when possible, with Pixabay as a fallback for missing or unsuitable images.

## What Changes

- Modify `fetch_page()` in newsassistant module to return images alongside content from Jina API
- Add `header_image` field to `news.article` model to store extracted images
- Add image validation and selection logic during article scraping (1000x400 min, landscape, JPEG/PNG/WebP)
- Display header image in article Kanban view
- Add Pixabay API integration in newsfeed module as fallback when no suitable article image exists
- Add Pixabay API key configuration in Settings
- Attach header images to blog posts during creation using Odoo's `cover_properties` system

## Capabilities

### New Capabilities

- `article-header-image`: Extract, validate, and store header images from news articles during scraping. Includes image validation (format, dimensions, orientation) and storage as Binary field.
- `pixabay-fallback`: Fetch suitable stock images from Pixabay API when no article header image is available. Includes API integration, search by article title, and error handling.

### Modified Capabilities

- `blog-publishing`: Add header image attachment to blog posts during creation. Use article's header_image if available, fall back to Pixabay, create blog without image if both fail.

## Impact

- **newsassistant module**: Modified `fetch_page()` function signature (returns tuple), new `header_image` field on `news.article`, updated `_fetch_and_extract()` logic, Kanban view changes
- **newsfeed module**: New Pixabay integration, modified `_create_blog_post()`, new configuration field for API key
- **Dependencies**: Pixabay API (external service, requires API key), PIL/Pillow for image validation
- **Database**: New Binary field on `news.article` model
