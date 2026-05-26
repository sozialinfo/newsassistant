# News Assistant — Blog

AI-powered content triage and automatic blog publishing for News Assistant.

## Overview

This addon adds Stage 3 to the News Assistant pipeline. For each scraped article it asks the AI
whether the article is relevant to a configurable content strategy, then either discards it,
leaves it for human review, or automatically generates a teaser and publishes it as an Odoo blog
post. Header images are taken from the article where available, with Pixabay as a fallback.

Requires `newsassistant` (base module) and the Odoo `website_blog` module.

## Features

- Three-way AI triage: `relevant` / `uncertain` / `discard` — driven by a free-text content strategy prompt
- Automatic AI teaser generation for relevant articles
- Automatic blog post creation with a backlink to the source article
- Header image selection: article's own image first; Pixabay API search as fallback
- Configurable stage mappings (which kanban stages represent Shortlist, Published, Discard)
- Manual **Digest Now** button on the article form view
- Batch **Digest Selected** action from the article list view
- Daily cron job to process all articles that have not yet been evaluated

## Pipeline

```
ir.cron (daily)
    └─▶ news.article._cron_digest_all_impl()
            └─▶ [per unprocessed article]
                    └─▶ article.with_delay()._digest_article()
                            ├─▶ _evaluate_relevance()    → "relevant" / "uncertain" / "discard"
                            │       └─▶ _call_ai()       (temperature=0.1)
                            ├─▶ [discard]   → move to Discard stage; digest_state = processed
                            ├─▶ [uncertain] → leave in current stage for human review
                            └─▶ [relevant]  → _handle_relevant()
                                    ├─▶ move to Shortlist stage
                                    ├─▶ _generate_teaser()    → _call_ai() (temperature=0.7)
                                    └─▶ _create_blog_post()
                                            └─▶ _get_header_image_for_blog()
                                                    ├─▶ article.header_image  (preferred)
                                                    └─▶ _search_pixabay() + download  (fallback)
```

## Configuration

Go to **News Assistant → Configuration → Settings**:

| Parameter | Description |
|---|---|
| Content Strategy | Free-text prompt defining what counts as relevant, uncertain, or to be discarded. The AI uses this as its evaluation criteria. |
| Teaser Prompt | Instructions for the AI on teaser style, tone, and length. |
| Target Blog | The Odoo blog where relevant articles will be published. |
| Pixabay API Key | Optional. Used to search for a header image when the article has none. |
| Shortlist Stage | Kanban stage to move relevant articles to (pending human review before publish). |
| Published Stage | Kanban stage for auto-published articles. |
| Discard Stage | Kanban stage for discarded articles. |

**Content Strategy** and **Target Blog** must be set before the digest pipeline will produce blog
posts. If either is missing, articles are left unprocessed and a warning is logged.

## Usage

### Set up the content strategy

1. Go to **News Assistant → Configuration → Settings**.
2. Write a content strategy. Example:

   > Mark as **relevant** if the article covers social policy, welfare reform, poverty, social
   > work practice, or NGO management in Switzerland. Mark as **uncertain** if the topic is
   > tangentially related. Mark as **discard** if it is off-topic, an event advertisement, or
   > a press release with no editorial content.

3. Set **Target Blog** to the blog where posts should be published.
4. Optionally set a **Teaser Prompt** and a **Pixabay API Key**.

### Run the digest

**Automatically**: The daily cron processes all articles with `digest_state = pending`.

**Manually (single article)**: Open an article and click **Digest Now**.

**Manually (batch)**: In the article list view, select multiple articles, then
**Action → Digest Selected**.

### Review results

- **Relevant** articles move to the Shortlist stage and have a blog post linked via the
  **Blog Posts** smart button on the article form.
- **Uncertain** articles stay in their current stage for human review. Move them manually
  after reading the content.
- **Discarded** articles move to the Discard stage. Open the article to read the AI's
  reasoning in the **Blog Reasoning** field.

### View published blog posts

Go to **Website → Blog** to see published posts. Each post has a **Source Article** field
linking back to the originating `news.article` record.

## Error Handling

| Condition | Behaviour |
|---|---|
| Content Strategy not set | Article left as `pending`; warning logged |
| Target Blog not set | Teaser generated but no blog post created; warning logged |
| AI returns unexpected decision | Treated as `uncertain`; article left for human review |
| Pixabay API unavailable | Blog post created without a header image |
| Pixabay returns no results | Blog post created without a header image |
| Blog post creation fails | Error logged; `digest_state` stays `pending` so it can be retried |

## Security

Inherits security groups from `newsassistant`:

| Group | Access |
|---|---|
| `newsassistant.newsassistant_group_user` | Read articles, trigger digest actions, view blog posts |
| `newsassistant.newsassistant_group_admin` | Full access |

No additional record rules. Blog post access follows `website_blog` access controls.

## Dependencies

- `newsassistant` — base module (required)
- `website_blog` — Odoo blog system (required)
- `INFOMANIAK_AI_API_KEY` — environment variable (required)
- `PIXABAY_API_KEY` — system parameter (optional, also set via Settings UI)

## Testing

```bash
make test-module MODULE=newsassistant_blog
```

## License

LGPL-3
