# Newsassistant Blog

AI-powered content curation and automatic blog publishing for News Assistant.

## Features

- Three-way AI triage: relevant, uncertain, discard — based on a configurable content strategy
- Automatic teaser generation for relevant articles
- Automatic blog post creation with source attribution
- Header image selection: article image first, Pixabay fallback
- Configurable pipeline stages (Shortlist, Published, Discard)
- Batch digest action from the article list view
- Daily cron job to process all unprocessed articles

## Models

### news.article (extended)

| Field | Type | Description |
|-------|------|-------------|
| `digest_state` | Selection | Whether the article has been evaluated (pending/processed) |
| `teaser` | Text | AI-generated teaser for blog publishing |
| `blog_reasoning` | Text | AI reasoning for article relevance |
| `blog_post_ids` | One2many | Linked blog posts |
| `blog_post_count` | Integer | Number of linked blog posts (computed) |

### blog.post (extended)

| Field | Type | Description |
|-------|------|-------------|
| `news_article_id` | Many2one | Source news article |

## Security

Inherits security groups from `newsassistant`:

| Group | Access |
|-------|--------|
| `newsassistant.newsassistant_group_user` | Read articles, trigger digest actions |
| `newsassistant.newsassistant_group_admin` | Full access |

No additional record rules. Relies on `website_blog` access controls for `blog.post`.

## Configuration

After installation, configure the following in **News Assistant → Configuration → Settings**:

| Parameter | Description |
|-----------|-------------|
| Content Strategy | Prompt defining relevance criteria (relevant / uncertain / discard) |
| Teaser Prompt | Prompt defining teaser style and length |
| Target Blog | Blog where curated articles will be published |
| Pixabay API Key | Optional: fallback image source |
| Shortlist Stage | Stage for articles pending human review |
| Published Stage | Stage for auto-published articles |
| Discard Stage | Stage for discarded articles |

## Dependencies

- `newsassistant` — base module
- `website_blog` — Odoo blog system
- `INFOMANIAK_AI_API_KEY` — environment variable (required)
- `PIXABAY_API_KEY` — system parameter (optional)

## License

LGPL-3
