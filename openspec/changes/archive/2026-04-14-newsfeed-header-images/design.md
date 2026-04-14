## Context

The newsassistant system processes news articles through a two-stage pipeline:
1. **Scraping** (newsassistant module): Fetches articles via Jina Reader API, extracts content with LLM
2. **Digest** (newsfeed module): Evaluates relevance, generates teasers, creates blog posts

Currently, `fetch_page()` requests plain text from Jina and discards image information. Blog posts are created as text-only with a teaser and source link.

The Jina Reader API supports a JSON response format with an `images` dictionary containing all images found on the page. Odoo's `blog.post` model uses `cover_properties` (JSON field) to reference header images stored as `ir.attachment` records.

## Goals / Non-Goals

**Goals:**
- Extract header images from articles during the existing Jina fetch (no additional API call)
- Validate images for header suitability (format, dimensions, orientation)
- Store validated images on `news.article` for reuse (Kanban display, blog creation)
- Provide Pixabay fallback when no suitable article image exists
- Attach header images to blog posts using Odoo's standard cover system

**Non-Goals:**
- Image optimization or resizing (use images as-is)
- Multiple image extraction per article (header only)
- Image caching or CDN integration
- AI-based image selection or quality assessment
- Storing images for articles that fail validation (only store if valid)

## Decisions

### Decision 1: Modify `fetch_page()` to return images

Change `fetch_page()` to request JSON format from Jina with `X-With-Images-Summary: all` header, returning a tuple `(content, images_dict)`.

**Alternatives considered:**
- Separate Jina call for images: Rejected - doubles API calls and latency
- New function `fetch_page_with_images()`: Rejected - code duplication, callers need updating anyway

**Rationale:** Single Jina call provides both content and images. The function signature change is contained and all callers are in the same module.

### Decision 2: Store image as Binary field on news.article

Add `header_image = fields.Binary()` to `news.article` model in newsassistant module. The image is downloaded and validated during `_fetch_and_extract()`.

**Alternatives considered:**
- Store image URL only: Rejected - external URLs may become unavailable
- Store as ir.attachment: Rejected - adds complexity, Binary field is simpler for single image
- Store in newsfeed module: Rejected - base module should own the data it extracts

**Rationale:** Binary field is simple, self-contained, and the image is immediately available for Kanban display and blog creation without additional fetches.

### Decision 3: Image validation criteria

Validate images with these criteria:
- **Format:** JPEG, PNG, or WebP (skip SVG, GIF, ICO)
- **Dimensions:** Minimum 1000x400 pixels
- **Orientation:** Landscape (width > height)

**Alternatives considered:**
- Looser criteria (800x400): Rejected - Odoo blog samples use 1000+ width
- Stricter aspect ratio: Rejected - unnecessarily restrictive

**Rationale:** Criteria match Odoo's blog header samples and ensure visually appealing headers. The 1000x400 minimum handles most responsive layouts.

### Decision 4: Skip non-content images by URL pattern

Before downloading, skip images with URLs containing: `.svg`, `logo`, `icon`, `footer`, `avatar`, `sprite`, `button`.

**Rationale:** These are rarely suitable header images. Skipping them reduces bandwidth and validation time.

### Decision 5: Pixabay integration in newsfeed module

Pixabay API key stored as `newsfeed.pixabay_api_key` system parameter with UI in Settings. Search uses article title, requests horizontal photos, selects first result meeting dimension requirements.

**Alternatives considered:**
- Unsplash API: Rejected - requires visible attribution
- Environment variable for API key: Rejected - inconsistent with existing config pattern (content_strategy, blog_id use ir.config_parameter)

**Rationale:** Pixabay offers royalty-free images with generous free tier (100 req/min). Configuration follows existing patterns in newsfeed module.

### Decision 6: Graceful degradation

If both article image and Pixabay fail, create the blog post without a header image and log a warning. Never block blog creation due to image issues.

**Rationale:** Header images are enhancement, not requirement. Better to publish text-only than fail entirely.

## Risks / Trade-offs

**Risk: fetch_page() signature change breaks callers**
→ Mitigation: All callers are in newsassistant module. Update them in same commit. Simple tuple unpacking.

**Risk: Large images consume database storage**
→ Mitigation: Only store one image per article. Images typically 100-500KB. Acceptable for the value provided.

**Risk: Image download adds latency to scraping**
→ Mitigation: Only download first valid candidate. Skip obviously unsuitable URLs. Set 15-second timeout per image.

**Risk: Pixabay rate limits (100/min)**
→ Mitigation: Queue jobs process sequentially. If rate limited, raise RetryableJobError with 60-second delay.

**Risk: Pixabay returns irrelevant images**
→ Mitigation: Use article title for search, require horizontal orientation. Accept that some results may be generic. Users can manually replace via Odoo's blog editor.

**Trade-off: No image resizing**
Images stored at original size. Keeps implementation simple but may result in larger storage. Odoo's website module handles responsive display.
