## Context

The News Assistant module currently scrapes ~60 Swiss social-sector news sources daily, extracting articles into a kanban board where humans triage them manually (New → Relevant → Archived/Discarded). This manual step creates a bottleneck.

The newsfeed module adds AI-powered automation that replaces the human triage step while preserving the kanban as an audit trail. It integrates with Odoo's `website_blog` module to publish curated content.

Key constraints:
- Must work with existing `queue_job` infrastructure
- Must preserve human oversight for uncertain cases
- Must not modify core newsassistant behavior—only extend it

## Goals / Non-Goals

**Goals:**
- Automate article triage using AI evaluation against user-defined content strategy
- Generate engaging teasers for relevant articles
- Publish curated content to Odoo blog automatically
- Provide traceability between blog posts and source articles
- Allow humans to review uncertain cases and override AI decisions

**Non-Goals:**
- Multiple content strategies (future enhancement)
- RSS feed generation (can be added via separate module)
- Full article content on blog (only teaser + link to source)
- Real-time processing (daily batch is sufficient)

## Decisions

### 1. Module Structure: Separate addon

**Decision**: Create `newsfeed` as a separate Odoo module depending on `newsassistant` and `website_blog`.

**Alternatives considered**:
- Extend newsassistant directly: Rejected because it would force website_blog dependency on users who don't need blog publishing
- Create as website_blog extension: Rejected because primary logic relates to article processing, not blog features

**Rationale**: Clean separation allows newsassistant to remain lightweight. Users can install newsfeed only if they want automated triage and blog publishing.

### 2. AI Pipeline: Two-step process

**Decision**: Use two separate LLM calls:
1. Relevance scoring (low temperature, deterministic)
2. Teaser generation (higher temperature, creative) — only for relevant articles

**Alternatives considered**:
- Single LLM call for both: Rejected because different tasks benefit from different temperatures and prompts
- Batch multiple articles per call: Rejected because it complicates error handling and makes individual retry impossible

**Rationale**: Separation allows tuning each step independently. Only relevant articles incur teaser generation cost.

### 3. Decision Model: Three-way classification

**Decision**: AI returns one of three decisions:
- `relevant` → Generate teaser, create blog post, move to Relevant stage
- `uncertain` → Leave in New stage for human review
- `discard` → Move to Discarded stage

**Alternatives considered**:
- Binary (relevant/discard): Rejected because it removes human oversight for edge cases
- Numeric score with thresholds: Rejected because user prefers natural language criteria in prompt

**Rationale**: Three-way model preserves human-in-the-loop for uncertain cases while fully automating clear decisions.

### 4. Configuration Storage: System parameters

**Decision**: Store configuration in `ir.config_parameter`:
- `newsfeed.content_strategy` — Relevance judgment prompt
- `newsfeed.teaser_prompt` — Teaser generation prompt  
- `newsfeed.blog_id` — Target blog ID for publishing

**Alternatives considered**:
- Dedicated model with form view: Rejected as overkill for single-strategy use case
- Hardcoded values: Rejected because user needs to customize prompts

**Rationale**: System parameters are simple, already used by newsassistant (e.g., `newsassistant.infomaniak_product_id`), and can be edited via Settings → Technical → Parameters.

### 5. Queue Architecture: One job per article

**Decision**: Cron triggers `_cron_digest_all()` which finds unprocessed articles and queues one `_digest_article()` job per article.

**Alternatives considered**:
- Batch processing (N articles per job): Rejected because individual jobs allow parallel processing and granular retry

**Rationale**: Consistent with existing newsassistant pattern. Allows concurrent processing within channel limits.

### 6. State Tracking: Field on news.article

**Decision**: Extend `news.article` with:
- `digest_state` (Selection: `pending`/`processed`) — Tracks whether digest has processed this article
- `teaser` (Text) — Stores generated teaser for relevant articles

**Alternatives considered**:
- Separate tracking model: Rejected because it adds complexity without clear benefit
- Store reasoning in field: Rejected in favor of using existing `news.log` with autovacuum

**Rationale**: Minimal extension to existing model. Reasoning goes to logs for debugging, not cluttering the article record.

### 7. Blog Post Link: Extend blog.post

**Decision**: Extend `blog.post` with `news_article_id` (Many2one → news.article) for traceability and deduplication.

**Rationale**: Prevents duplicate posts if digest runs multiple times. Allows tracing which article generated which post.

### 8. Publishing: Immediate, fully automated

**Decision**: Blog posts are created with `is_published = True` immediately when AI marks article as relevant.

**Alternatives considered**:
- Create as draft: Rejected because user wants full automation

**Rationale**: Humans can still unpublish or edit posts after the fact via standard Odoo blog interface.

## Risks / Trade-offs

**[Risk] AI makes wrong triage decisions** → Humans can review kanban board and override. Uncertain cases stay in New for human review.

**[Risk] Content strategy prompt is poorly written** → Bad results. Mitigation: Provide example prompt in documentation. User can iterate on prompt.

**[Risk] Teaser quality varies** → Mitigation: Separate teaser prompt allows tuning. User can edit individual posts via blog interface.

**[Risk] High AI costs with many articles** → Mitigation: Only relevant articles get teaser generation (second call). Discard/uncertain skip it.

**[Risk] Blog post links to dead/moved source URL** → Outside our control. Source URLs are from original scrape. No mitigation planned.

**[Trade-off] No real-time processing** → Daily cron is sufficient for news aggregation use case. Can be changed via cron settings.
