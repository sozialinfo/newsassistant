## 1. Modify fetch_page() to Return Images

- [x] 1.1 Update `fetch_page()` in `newsassistant/models/news_source.py` to request JSON format with `Accept: application/json` and `X-With-Images-Summary: all` headers
- [x] 1.2 Parse JSON response and extract `data.content` and `data.images`
- [x] 1.3 Return tuple `(content, images_dict)` instead of just content
- [x] 1.4 Update all callers of `fetch_page()` to handle the new tuple return value

## 2. Add header_image Field to news.article

- [x] 2.1 Add `header_image = fields.Binary()` field to `news.article` model in `newsassistant/models/news_article.py`
- [x] 2.2 Add `header_image_filename = fields.Char()` field to store original filename

## 3. Implement Image Validation Logic

- [x] 3.1 Create `_should_skip_image_url(url)` helper to check for logo/icon/footer/svg patterns
- [x] 3.2 Create `_validate_and_download_image(url)` helper that downloads image, checks format (JPEG/PNG/WebP), validates dimensions (1000x400 min), and checks orientation (landscape)
- [x] 3.3 Create `_select_header_image(images_dict)` method that iterates images, skips non-content URLs, validates each candidate, and returns first valid image binary or None

## 4. Integrate Image Selection into Article Extraction

- [x] 4.1 Update `_fetch_and_extract()` to unpack `(content, images_dict)` from `fetch_page()`
- [x] 4.2 After successful content extraction, call `_select_header_image(images_dict)`
- [x] 4.3 If valid image found, store in `header_image` and `header_image_filename` fields
- [x] 4.4 Add log entry indicating image extraction result (found/not found)

## 5. Display Header Image in Kanban View

- [x] 5.1 Update article Kanban view XML to display `header_image` on cards
- [x] 5.2 Style the image display appropriately for card layout

## 6. Add Pixabay Configuration

- [x] 6.1 Add `newsfeed_pixabay_api_key` field to `res.config.settings` model in newsfeed module
- [x] 6.2 Add getter/setter methods for `newsfeed.pixabay_api_key` system parameter
- [x] 6.3 Add Pixabay API Key field to Settings view in `res_config_settings_views.xml`

## 7. Implement Pixabay Integration

- [x] 7.1 Create `_get_pixabay_api_key()` helper method to retrieve API key from config
- [x] 7.2 Create `_search_pixabay(title)` method to query Pixabay API with article title, orientation=horizontal, image_type=photo
- [x] 7.3 Create `_download_pixabay_image(result)` method to download from `largeImageURL` and validate dimensions
- [x] 7.4 Add error handling for timeout, rate limit (RetryableJobError), and other API errors

## 8. Modify Blog Post Creation with Header Image

- [x] 8.1 Create `_create_header_image_attachment(image_data, filename, blog_post)` method to create ir.attachment for blog post
- [x] 8.2 Create `_set_blog_cover_properties(blog_post, attachment)` method to set cover_properties JSON
- [x] 8.3 Create `_get_header_image_for_blog()` orchestration method: use article.header_image if available, else Pixabay fallback
- [x] 8.4 Update `_create_blog_post()` to call header image logic after creating the post
- [x] 8.5 Add log entries indicating image source (article/Pixabay/none)

## 9. Testing and Verification

- [x] 9.1 Test article scraping with page that has suitable images - verify extraction
- [x] 9.2 Test article scraping with page without suitable images - verify graceful handling
- [x] 9.3 Test Pixabay fallback when article has no image
- [x] 9.4 Test without Pixabay API key configured - verify warning logged
- [x] 9.5 Verify Kanban view displays header images correctly
- [x] 9.6 Verify blog posts display header images correctly on website
