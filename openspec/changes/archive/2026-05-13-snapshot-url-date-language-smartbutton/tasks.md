## 1. Snapshot URL field

- [x] 1.1 Add `url` field (Char, optional, index=True) to `news.snapshot` model
- [x] 1.2 Show `url` in snapshot form view (widget="url", below source_id)
- [x] 1.3 Pass article URL when creating snapshot in `news_source_website.py` `_scrape_article_page()`

## 2. Source language field

- [x] 2.1 Add `language` field (Char, optional) to `news.source` model
- [x] 2.2 Extend listing LLM response schema to include `language` (ISO 639-1 code)
- [x] 2.3 Store detected language on `news.source` after successful listing scrape
- [x] 2.4 Show `language` field in news source form view (user-editable)

## 3. Article date mandatory with today default

- [x] 3.1 Add `required=True, default=fields.Date.today` to `news.article.date` field
- [x] 3.2 Update `_extraction_create_article()` in `news_snapshot.py` to fall back to `fields.Date.today()` when AI returns no date

## 4. Blog post language-aware link text

- [x] 4.1 Update teaser system prompt to return JSON `{"teaser": "...", "read_more": "..."}` instead of plain text, instructing AI to write `read_more` in the article's language
- [x] 4.2 Update `_generate_teaser()` to parse JSON response and store `teaser` field
- [x] 4.3 Update `_create_blog_post()` to use `read_more` from teaser result (with English fallback if missing)
- [x] 4.4 Update tests that mock teaser AI response to return JSON format

## 5. Article SmartButton for snapshot

- [x] 5.1 Add `snapshot_count` computed field to `news.article` (Integer: 1 if snapshot_id else 0)
- [x] 5.2 Add `action_view_snapshot()` method to `news.article` returning act_window for the linked snapshot
- [x] 5.3 Add SmartButton to article form view `button_box` (admin only, invisible when snapshot_count == 0)
