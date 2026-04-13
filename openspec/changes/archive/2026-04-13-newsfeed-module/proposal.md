## Why

The current News Assistant requires manual human triage of articles through a kanban board. This creates a bottleneck when dealing with ~60 sources producing many articles daily. We need an automated system that can evaluate article relevance against a content strategy, generate teasers, and publish curated content to the website—replacing the human in routine triage while preserving oversight for uncertain cases.

## What Changes

- Add a new `newsfeed` Odoo module that depends on `newsassistant` and `website_blog`
- Extend `news.article` with digest processing state and teaser field
- Extend `blog.post` with link back to source article for traceability
- Implement two-step AI pipeline: relevance scoring → teaser generation
- Auto-move articles to appropriate kanban stages based on AI decision
- Auto-publish relevant articles as blog posts with teaser + source link
- Add separate daily cron job for digest processing
- Add system parameters for content strategy prompt, teaser prompt, and target blog

## Capabilities

### New Capabilities

- `digest-pipeline`: Queue-based processing pipeline that evaluates articles against content strategy, makes triage decisions (relevant/uncertain/discard), and updates kanban stages
- `teaser-generation`: AI-powered teaser generation for relevant articles using configurable prompt
- `blog-publishing`: Automatic creation of published blog posts from relevant articles with teaser content and source attribution link
- `digest-configuration`: System parameters for content strategy prompt, teaser prompt, and target blog selection

### Modified Capabilities

- `kanban-triage`: Stage transitions now happen automatically via AI decisions, not just manually

## Impact

- **Models**: `news.article` extended with `digest_state`, `teaser` fields; `blog.post` extended with `news_article_id`
- **Dependencies**: New module depends on `website_blog` in addition to existing `newsassistant`
- **Queue Jobs**: New job channel or reuse `root.newsassistant` for digest jobs
- **Cron**: Additional scheduled action for daily digest processing
- **AI Costs**: Two LLM calls per article processed (relevance + teaser for relevant ones)
- **Logging**: New `digest` category in existing `news.log` for reasoning/debugging
