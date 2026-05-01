## 1. Base Module — news.snapshot Model

- [x] 1.1 Create `news/snapshot.py` model with fields: source_id, raw_content (Html), captured_at, article_ids, article_count, name (computed)
- [x] 1.2 Add `_extract_articles()` method on `news.snapshot` that calls Infomaniak AI with HTML content and creates `news.article` records
- [x] 1.3 Override `create()` on `news.snapshot` to auto-enqueue `_extract_articles()` queue job on the `root.newsassistant` channel
- [x] 1.4 Add snapshot views: list view (name, source, captured_at, article_count) and form view (all fields + articles tab)
- [x] 1.5 Add `snapshot_ids` One2many to `news.source` and display Snapshots tab in source form view
- [x] 1.6 Register `news.snapshot` in security CSV with appropriate access rights

## 2. Base Module — Source Types and Article Refactor

- [x] 2.1 Add `source_type` Selection field (website/email, default=website) to `news.source`
- [x] 2.2 Add `sender_domain` Char field to `news.source` for email-type sources
- [x] 2.3 Update `news.source` form view to show URL for website sources and sender_domain for email sources (using `attrs`/`invisible`)
- [x] 2.4 Add source type filters to source list search view
- [x] 2.5 Refactor `news.article`: replace `source_id` Many2one with `snapshot_id` Many2one (required, ondelete=cascade) to `news.snapshot`
- [x] 2.6 Add `source_id` as stored computed field on `news.article` derived from `snapshot_id.source_id`
- [x] 2.7 Move AI extraction prompt logic from `news_source.py` into `news.snapshot._extract_articles()` — base module reads HTML, not Markdown
- [x] 2.8 Update `news.log` model: add `snapshot_id` Many2one field and `email` category option
- [x] 2.9 Update demo data in `newsassistant`: add email-type source demo record, update existing demo to use snapshots

## 3. Base Module — Cleanup and Utility Relocation

- [x] 3.1 Remove Jina-specific functions from `news_source.py` (`fetch_page`, `should_skip_image_url`, `validate_and_download_image`, `select_header_image`) — these move to `newsassistant_website`
- [x] 3.2 Keep shared utilities in base: `parse_ai_json`, `normalize_url`, `clean_html`, `_call_infomaniak_ai`
- [x] 3.3 Remove website-specific cron job data from `newsassistant` (moves to `newsassistant_website`)
- [x] 3.4 Update `newsassistant/__manifest__.py`: bump version, update depends list if needed, remove queue_job from data if moved

## 4. newsassistant_website Module — New Module

- [x] 4.1 Create `newsassistant_website/` module skeleton: `__init__.py`, `__manifest__.py` (depends: newsassistant, queue_job)
- [x] 4.2 Create `models/news_source_website.py` extending `news.source` with `_scrape_listing()`, `_cron_scrape_all()` for website sources
- [x] 4.3 Move `fetch_page()` (Jina API) into `newsassistant_website` utilities
- [x] 4.4 Move image selection utilities (`select_header_image`, `validate_and_download_image`, `should_skip_image_url`) into `newsassistant_website`
- [x] 4.5 Implement Markdown→HTML conversion in website module (before storing in `news.snapshot.raw_content`)
- [x] 4.6 Implement per-article snapshot creation: for each discovered URL, create a `news.snapshot` with the article page HTML (website module fetches via Jina then creates snapshot)
- [x] 4.7 Create daily cron job in `newsassistant_website` for scraping all active website sources
- [x] 4.8 Move queue_job channel and function definitions to `newsassistant_website` data
- [x] 4.9 Add security CSV for `newsassistant_website` (inherits base groups)
- [x] 4.10 Add demo data for `newsassistant_website` with website-type source snapshots
- [x] 4.11 Create `newsassistant_website/tests/` with tests for: Jina fetch, listing scrape, article snapshot creation, image selection

## 5. newsassistant_email Module — New Module

- [x] 5.1 Create `newsassistant_email/` module skeleton: `__init__.py`, `__manifest__.py` (depends: newsassistant, mail)
- [x] 5.2 Extend `news.snapshot` in `newsassistant_email` to inherit `mail.alias.mixin`
- [x] 5.3 Implement `message_new()` override on extended `news.snapshot`: extract sender domain, lookup/create source, sanitize HTML, create snapshot
- [x] 5.4 Implement sender domain extraction from `email_from` header
- [x] 5.5 Implement auto-source creation: call `_call_infomaniak_ai()` to name the source from domain, fallback to domain name on failure
- [x] 5.6 Implement HTML sanitization for inbound emails: strip scripts, tracking pixels, remove 1×1 images
- [x] 5.7 Create `data/mail_alias_data.xml` with default mail alias record for `news.snapshot` model (alias_name=`newsassistant`)
- [x] 5.8 Extend `res.config.settings` in `newsassistant_email` to add email alias name field
- [x] 5.9 Create settings view extension showing "Email Alias" section under News Assistant
- [x] 5.10 Add security CSV for `newsassistant_email`
- [x] 5.11 Add demo data for `newsassistant_email` with an email-type source
- [x] 5.12 Create `newsassistant_email/tests/` with tests for: message_new, domain routing, auto-source creation, AI naming, HTML sanitization, fallback behavior

## 6. Tests — Update Existing Tests

- [x] 6.1 Update `test_news_source.py` in base module to reflect new source model (source_type field, snapshot relationship, article_count via snapshots)
- [x] 6.2 Update `test_scraping_pipeline.py`: remove Jina mocks from base tests, add snapshot-based extraction tests
- [x] 6.3 Update `test_queue_jobs.py`: update channel and job function references
- [x] 6.4 Update `test_article_state.py`: update article creation to use snapshot_id instead of source_id
- [x] 6.5 Update `test_header_image.py`: move to `newsassistant_website` test suite
- [x] 6.6 Update remaining base tests for snapshot model changes
- [x] 6.7 Ensure `newsassistant_blog` tests still pass (blog module depends on base only, articles still have source_id via computed field)

## 7. Translations

- [x] 7.1 Extract POT from running instance for all three modules
- [x] 7.2 Update/create `newsassistant/i18n/de.po` and `fr.po` with new snapshot model strings
- [x] 7.3 Create `newsassistant_website/i18n/de.po` and `fr.po`
- [x] 7.4 Create `newsassistant_email/i18n/de.po` and `fr.po`
- [x] 7.5 Install translations and verify no fuzzy/untranslated entries

## 8. Fresh Instance and Smoke Test

- [x] 8.4 Run full test suite for all modules and confirm green (88+60+28+46=222 tests)
- [x] 8.1 Rebuild fresh instance with all modules: newsassistant, newsassistant_website, newsassistant_email, newsassistant_blog
- [x] 8.2 Verify demo data installs correctly (website sources, email source, snapshots)
- [x] 8.3 Run smoke test: login page 200, assets loading, modules installed
