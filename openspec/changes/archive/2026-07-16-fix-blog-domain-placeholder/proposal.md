## Why

When the system auto-publishes a blog post, the source link text contains the literal string `{domain}` instead of the actual source domain (e.g. "Vollständigen Artikel auf {domain} lesen →"). The link also lacks primary button styling and includes an unnecessary arrow symbol.

## What Changes

- Substitute `{domain}` in the AI-generated `read_more` text with the actual source domain extracted from the article URL
- Style the source link as a primary button (`btn btn-primary`) in the blog post content
- Remove the `→` symbol from the link text, the AI prompt example, and the English fallback
- Update the AI prompt example to reflect the new format (no `{domain}`, no `→`)
- Update the spec and tests to match the new behavior

## Capabilities

### New Capabilities
None

### Modified Capabilities
- `blog-publishing`: The link text format changes — the `{domain}` placeholder is replaced with the actual domain after AI generation, the link is styled as a primary button, and the `→` symbol is removed

## Impact

- `newsassistant_blog/models/news_article.py`: `_generate_teaser()` prompt and `_create_blog_post()` content generation
- `newsassistant_blog/tests/test_digest_pipeline.py`: Updated test expectations
- `openspec/specs/blog-publishing/spec.md`: Updated spec for the new link format