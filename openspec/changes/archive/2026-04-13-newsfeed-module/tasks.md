## 1. Module Structure

- [x] 1.1 Create `addons/newsfeed/` directory with `__init__.py`
- [x] 1.2 Create `__manifest__.py` with dependencies on `newsassistant` and `website_blog`
- [x] 1.3 Create `models/__init__.py` and `models/news_article.py` skeleton
- [x] 1.4 Create `models/blog_post.py` skeleton for blog.post extension
- [x] 1.5 Create `security/ir.model.access.csv` with appropriate access rights
- [x] 1.6 Create `data/ir_config_parameter_data.xml` with empty system parameter placeholders

## 2. Data Model Extensions

- [x] 2.1 Extend `news.article` with `digest_state` field (Selection: pending/processed, default pending)
- [x] 2.2 Extend `news.article` with `teaser` field (Text)
- [x] 2.3 Extend `blog.post` with `news_article_id` field (Many2one → news.article)
- [x] 2.4 Add SQL constraint or unique index to prevent duplicate blog posts per article

## 3. Configuration Helpers

- [x] 3.1 Create helper method `_get_content_strategy()` to read `newsfeed.content_strategy` parameter
- [x] 3.2 Create helper method `_get_teaser_prompt()` to read `newsfeed.teaser_prompt` parameter
- [x] 3.3 Create helper method `_get_target_blog()` to read and validate `newsfeed.blog_id` parameter
- [x] 3.4 Add validation that raises clear error when required parameters are missing

## 4. Digest Pipeline Core

- [x] 4.1 Implement `_cron_digest_all()` method to find unprocessed scraped articles
- [x] 4.2 Create `data/ir_cron_data.xml` with daily scheduled action for digest
- [x] 4.3 Implement `_digest_article()` queue job method skeleton
- [x] 4.4 Implement relevance scoring LLM call using content strategy prompt
- [x] 4.5 Parse AI response to extract decision (relevant/uncertain/discard) and reasoning
- [x] 4.6 Update article `digest_state` to `processed` after evaluation

## 5. Stage Transitions

- [x] 5.1 Implement logic to move article to "Relevant" stage when decision is `relevant`
- [x] 5.2 Implement logic to move article to "Discarded" stage when decision is `discard`
- [x] 5.3 Verify article stays in "New" stage when decision is `uncertain`

## 6. Teaser Generation

- [x] 6.1 Implement teaser generation LLM call (only for relevant articles)
- [x] 6.2 Use higher temperature for creative teaser output
- [x] 6.3 Store generated teaser in article's `teaser` field
- [x] 6.4 Handle teaser generation failure gracefully (log error, skip blog post)

## 7. Blog Publishing

- [x] 7.1 Implement blog post creation with article title as name
- [x] 7.2 Format blog post content with teaser and source link
- [x] 7.3 Set `news_article_id` on created blog post
- [x] 7.4 Set `is_published = True` and `blog_id` from configuration
- [x] 7.5 Add deduplication check before creating blog post

## 8. Logging Integration

- [x] 8.1 Add `digest` category to logging calls
- [x] 8.2 Log successful digest processing with decision and reasoning
- [x] 8.3 Log errors (AI failures, missing configuration, etc.)
- [x] 8.4 Include LLM request/response metadata in log entries

## 9. Views and UI

- [x] 9.1 Add `digest_state` and `teaser` fields to article form view
- [x] 9.2 Add `news_article_id` field to blog post form view (optional, for traceability)
- [x] 9.3 Consider adding digest status indicator to kanban card (optional enhancement)

## 10. Testing

- [x] 10.1 Test digest cron finds correct articles (scraped, pending digest_state)
- [x] 10.2 Test three-way decision routing (relevant/uncertain/discard)
- [x] 10.3 Test teaser generation and storage
- [x] 10.4 Test blog post creation with correct content and links
- [x] 10.5 Test deduplication prevents duplicate blog posts
- [x] 10.6 Test error handling when configuration is missing
- [x] 10.7 Test manual stage override after digest decision
