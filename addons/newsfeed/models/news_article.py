import json
import logging
import time

import requests

from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.queue_job.exception import RetryableJobError

_logger = logging.getLogger(__name__)

# AI configuration
AI_TIMEOUT = 120
TRANSIENT_HTTP_CODES = {408, 429, 500, 502, 503, 504}


class NewsArticle(models.Model):
    _inherit = "news.article"

    # Digest state tracking
    digest_state = fields.Selection(
        [
            ("pending", "Pending"),
            ("processed", "Processed"),
        ],
        default="pending",
        readonly=True,
        index=True,
        string="Digest State",
    )
    teaser = fields.Text(
        string="Teaser",
        readonly=True,
        help="AI-generated teaser for blog publishing",
    )

    # Reverse link to blog post
    blog_post_ids = fields.One2many(
        "blog.post",
        "news_article_id",
        string="Blog Posts",
    )
    blog_post_count = fields.Integer(
        compute="_compute_blog_post_count",
        string="Blog Posts",
    )

    def _compute_blog_post_count(self):
        for article in self:
            article.blog_post_count = len(article.blog_post_ids)

    def action_view_blog_post(self):
        """Open the blog post on the website for editing."""
        self.ensure_one()
        if not self.blog_post_ids:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("No Blog Post"),
                    "message": _("No blog post has been created for this article yet."),
                    "type": "warning",
                    "sticky": False,
                },
            }

        blog_post = self.blog_post_ids[0]
        # Open blog post on website with edit mode
        return {
            "type": "ir.actions.act_url",
            "url": f"{blog_post.website_url}?enable_editor=1",
            "target": "new",
        }

    # -------------------------------------------------------------------------
    # Configuration Helpers
    # -------------------------------------------------------------------------

    def _get_content_strategy(self):
        """Get the content strategy prompt from system parameters.

        Returns:
            str: The content strategy prompt.

        Raises:
            UserError: If the parameter is not configured.
        """
        strategy = self.env["ir.config_parameter"].sudo().get_param(
            "newsfeed.content_strategy", default=""
        )
        if not strategy or not strategy.strip():
            raise UserError(
                _("Newsfeed content strategy is not configured. "
                  "Please set the 'newsfeed.content_strategy' system parameter.")
            )
        return strategy.strip()

    def _get_teaser_prompt(self):
        """Get the teaser generation prompt from system parameters.

        Returns:
            str: The teaser prompt.

        Raises:
            UserError: If the parameter is not configured.
        """
        prompt = self.env["ir.config_parameter"].sudo().get_param(
            "newsfeed.teaser_prompt", default=""
        )
        if not prompt or not prompt.strip():
            raise UserError(
                _("Newsfeed teaser prompt is not configured. "
                  "Please set the 'newsfeed.teaser_prompt' system parameter.")
            )
        return prompt.strip()

    def _get_target_blog(self):
        """Get and validate the target blog from system parameters.

        Returns:
            blog.blog: The target blog record.

        Raises:
            UserError: If the parameter is not configured or blog doesn't exist.
        """
        blog_id_str = self.env["ir.config_parameter"].sudo().get_param(
            "newsfeed.blog_id", default=""
        )
        if not blog_id_str or not blog_id_str.strip():
            raise UserError(
                _("Newsfeed target blog is not configured. "
                  "Please set the 'newsfeed.blog_id' system parameter.")
            )

        try:
            blog_id = int(blog_id_str.strip())
        except ValueError:
            raise UserError(
                _("Invalid newsfeed.blog_id value: '%s'. Must be a valid blog ID.")
                % blog_id_str
            )

        blog = self.env["blog.blog"].browse(blog_id).exists()
        if not blog:
            raise UserError(
                _("Target blog with ID %d does not exist. "
                  "Please update the 'newsfeed.blog_id' system parameter.")
                % blog_id
            )
        return blog

    # -------------------------------------------------------------------------
    # Manual Trigger Actions
    # -------------------------------------------------------------------------

    def action_digest_now(self):
        """Button action: manually trigger digest processing for this article."""
        self.ensure_one()
        if self.state != "scraped":
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Cannot Process"),
                    "message": _("Article must be in 'Scraped' state to process. Current state: %s") % self.state,
                    "type": "warning",
                    "sticky": False,
                },
            }

        # Reset digest state if already processed (allow re-processing)
        if self.digest_state == "processed":
            self.write({"digest_state": "pending", "teaser": False})

        self.with_delay(
            channel="root.newsassistant",
            description=f"Manual digest: {self.title[:50]}",
        )._digest_article()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Digest Started"),
                "message": _("Processing article in background..."),
                "type": "info",
                "sticky": False,
            },
        }

    def action_digest_selected(self):
        """Server action: trigger digest for selected articles from list view."""
        scraped_articles = self.filtered(lambda a: a.state == "scraped")
        skipped = len(self) - len(scraped_articles)

        if not scraped_articles:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("No Articles to Process"),
                    "message": _("None of the selected articles are in 'Scraped' state."),
                    "type": "warning",
                    "sticky": False,
                },
            }

        # Reset digest state for already processed articles
        already_processed = scraped_articles.filtered(lambda a: a.digest_state == "processed")
        if already_processed:
            already_processed.write({"digest_state": "pending", "teaser": False})

        # Queue digest jobs
        for article in scraped_articles:
            article.with_delay(
                channel="root.newsassistant",
                description=f"Manual digest: {article.title[:50]}",
            )._digest_article()

        message = _("Queued %d article(s) for digest processing.") % len(scraped_articles)
        if skipped:
            message += _(" Skipped %d article(s) not in 'Scraped' state.") % skipped

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Digest Started"),
                "message": message,
                "type": "info",
                "sticky": False,
            },
        }

    # -------------------------------------------------------------------------
    # AI Helpers
    # -------------------------------------------------------------------------

    def _call_ai(self, system_prompt, user_content, temperature=0.1):
        """Call the Infomaniak AI chat completion API.

        Args:
            system_prompt: The system prompt instructing the AI.
            user_content: The user message content.
            temperature: Temperature for response generation (default 0.1).

        Returns:
            dict with keys:
                - content: The parsed content string from the AI response
                - usage: Token usage dict
                - request: Original request details for logging
                - duration_ms: Response time in milliseconds

        Raises:
            RetryableJobError: On transient API errors.
            ValueError: On malformed AI response.
        """
        import os

        api_key = os.environ.get("INFOMANIAK_AI_API_KEY")
        if not api_key:
            raise UserError(
                _("Infomaniak AI API key not configured. "
                  "Set the INFOMANIAK_AI_API_KEY environment variable.")
            )

        product_id = self.env["ir.config_parameter"].sudo().get_param(
            "newsassistant.infomaniak_product_id", default="103794"
        )
        url = f"https://api.infomaniak.com/2/ai/{product_id}/openai/v1/chat/completions"

        model = "qwen3"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        start_time = time.time()
        try:
            response = requests.post(
                url, json=payload, headers=headers, timeout=AI_TIMEOUT
            )
        except requests.exceptions.Timeout:
            raise RetryableJobError(
                "Infomaniak AI API timeout", seconds=300, ignore_retry=False
            )
        except requests.exceptions.ConnectionError as e:
            raise RetryableJobError(
                f"Infomaniak AI API connection error: {e}",
                seconds=300,
                ignore_retry=False,
            )
        duration_ms = int((time.time() - start_time) * 1000)

        if response.status_code in TRANSIENT_HTTP_CODES:
            raise RetryableJobError(
                f"Infomaniak AI API returned {response.status_code}",
                seconds=300,
                ignore_retry=False,
            )

        if response.status_code != 200:
            raise ValueError(
                f"Infomaniak AI API error {response.status_code}: {response.text[:500]}"
            )

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise ValueError(f"Unexpected AI response structure: {e}")

        usage = data.get("usage", {})

        return {
            "content": content,
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            "request": {
                "model": model,
                "temperature": temperature,
                "system_prompt": system_prompt,
                "user_content": user_content[:1000] + "..." if len(user_content) > 1000 else user_content,
            },
            "response": {
                "content": content,
                "status_code": response.status_code,
            },
            "duration_ms": duration_ms,
        }

    def _parse_ai_json(self, raw_text):
        """Parse JSON from AI response, handling markdown fences and thinking blocks."""
        import re

        text = raw_text.strip()

        # Remove thinking blocks
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

        # Strip markdown code fences
        if text.startswith("```"):
            first_newline = text.find("\n")
            if first_newline != -1:
                text = text[first_newline + 1:]
        if text.endswith("```"):
            text = text[:-3].strip()

        return json.loads(text)

    # -------------------------------------------------------------------------
    # Digest Pipeline
    # -------------------------------------------------------------------------

    @staticmethod
    def _cron_digest_all():
        """Cron entry point: enqueue a digest job for each unprocessed article.

        This is a static method called by the cron. We need to get the model
        from the environment passed by Odoo.
        """
        from odoo import api, SUPERUSER_ID
        # This method is called directly by cron, so we need to handle
        # the environment ourselves
        pass

    def _cron_digest_all_impl(self):
        """Implementation of cron digest - find and queue unprocessed articles."""
        # Find articles that are scraped but not yet processed by digest
        articles = self.search([
            ("state", "=", "scraped"),
            ("digest_state", "=", "pending"),
        ])

        _logger.info(
            "Digest cron: found %d unprocessed articles",
            len(articles),
        )

        for article in articles:
            article.with_delay(
                channel="root.newsassistant",
                description=f"Digest: {article.title[:50]}",
            )._digest_article()

        return len(articles)

    def _digest_article(self):
        """Queue job: evaluate article relevance and process accordingly.

        Two-step process:
        1. Evaluate relevance using content strategy prompt
        2. If relevant, generate teaser and create blog post
        """
        self.ensure_one()
        _logger.info("Digest processing article: %s (%s)", self.title, self.url)

        start_time = time.time()
        log_entries = []

        # Try to get current job ID from context
        job_id = self.env.context.get("job_uuid")
        if job_id:
            job = self.env["queue.job"].search([("uuid", "=", job_id)], limit=1)
            job_id = job.id if job else None

        def add_entry(level, message, duration=None, metadata=None):
            log_entries.append({
                "timestamp": fields.Datetime.now(),
                "level": level,
                "message": message,
                "duration": duration,
                "metadata": metadata,
            })

        add_entry(
            "info",
            f"Starting digest for: {self.title[:50]}",
            metadata={"url": self.url, "source": self.source_id.name},
        )

        # Check configuration
        try:
            content_strategy = self._get_content_strategy()
        except UserError as e:
            add_entry("error", str(e))
            self._create_digest_log(
                level="error",
                message=f"Configuration error: {e}",
                duration=time.time() - start_time,
                entries=log_entries,
                job_id=job_id,
            )
            _logger.error("Digest config error for %s: %s", self.title, e)
            return

        # Step 1: Evaluate relevance
        decision, reasoning = self._evaluate_relevance(
            content_strategy, log_entries, add_entry
        )

        if decision is None:
            # Error occurred during evaluation
            self._create_digest_log(
                level="error",
                message=f"Relevance evaluation failed: {self.title[:50]}",
                duration=time.time() - start_time,
                entries=log_entries,
                job_id=job_id,
            )
            return

        # Update digest state
        self.write({"digest_state": "processed"})

        # Handle decision
        if decision == "discard":
            self._handle_discard(reasoning, log_entries, add_entry)
        elif decision == "uncertain":
            self._handle_uncertain(reasoning, log_entries, add_entry)
        elif decision == "relevant":
            self._handle_relevant(reasoning, log_entries, add_entry, job_id, start_time)
            return  # _handle_relevant creates its own log

        # Create log for discard/uncertain
        total_duration = time.time() - start_time
        self._create_digest_log(
            level="success",
            message=f"Digest complete ({decision}): {self.title[:50]}",
            duration=total_duration,
            entries=log_entries,
            job_id=job_id,
        )

    def _evaluate_relevance(self, content_strategy, log_entries, add_entry):
        """Evaluate article relevance using AI.

        Returns:
            tuple: (decision, reasoning) or (None, None) on error
        """
        system_prompt = (
            "/no_think\n"
            f"{content_strategy}\n\n"
            "Based on the above content strategy, evaluate the following article.\n"
            "Return a JSON object with exactly these fields:\n"
            '- "decision": one of "relevant", "uncertain", or "discard"\n'
            '- "reasoning": brief explanation (1-2 sentences)\n\n'
            "Return ONLY valid JSON, no markdown, no explanation outside the JSON."
        )

        # Prepare article content for evaluation
        article_content = f"Title: {self.title}\n\n"
        if self.summary:
            article_content += f"Summary: {self.summary}\n\n"
        if self.content:
            # Strip HTML tags for cleaner input
            from html import unescape
            import re
            clean_content = re.sub(r"<[^>]+>", " ", self.content)
            clean_content = unescape(clean_content)
            clean_content = re.sub(r"\s+", " ", clean_content).strip()
            article_content += f"Content: {clean_content[:5000]}"

        add_entry("info", "Calling LLM for relevance evaluation")

        try:
            ai_result = self._call_ai(
                system_prompt,
                article_content,
                temperature=0.1,  # Low temperature for deterministic judgment
            )
            add_entry(
                "info",
                f"LLM response received ({ai_result['usage']['total_tokens']} tokens)",
                duration=ai_result["duration_ms"] / 1000,
                metadata={
                    "request": ai_result["request"],
                    "response": ai_result["response"],
                    "usage": ai_result["usage"],
                },
            )
        except RetryableJobError:
            raise
        except Exception as e:
            add_entry("error", f"AI call failed: {e}")
            _logger.exception("AI error evaluating article %s", self.url)
            return None, None

        # Parse response
        try:
            result = self._parse_ai_json(ai_result["content"])
            decision = result.get("decision", "").lower()
            reasoning = result.get("reasoning", "")

            if decision not in ("relevant", "uncertain", "discard"):
                raise ValueError(f"Invalid decision: {decision}")

            add_entry(
                "info",
                f"Decision: {decision}",
                metadata={"decision": decision, "reasoning": reasoning},
            )
            return decision, reasoning

        except (json.JSONDecodeError, ValueError) as e:
            add_entry(
                "error",
                f"Failed to parse AI response: {e}",
                metadata={"raw_response": ai_result["content"][:500]},
            )
            _logger.warning(
                "Malformed AI response for article %s: %s",
                self.url,
                ai_result["content"][:500],
            )
            return None, None

    def _handle_discard(self, reasoning, log_entries, add_entry):
        """Handle discard decision: move to Discarded stage."""
        discarded_stage = self.env.ref(
            "newsassistant.news_article_stage_discarded",
            raise_if_not_found=False,
        )
        if discarded_stage:
            self.write({"stage_id": discarded_stage.id})
            add_entry(
                "info",
                f"Moved to Discarded stage: {reasoning}",
            )
        else:
            add_entry("warning", "Discarded stage not found")

        _logger.info("Article discarded: %s - %s", self.title, reasoning)

    def _handle_uncertain(self, reasoning, log_entries, add_entry):
        """Handle uncertain decision: leave in New stage for human review."""
        add_entry(
            "info",
            f"Left in New stage for human review: {reasoning}",
        )
        _logger.info("Article uncertain: %s - %s", self.title, reasoning)

    def _handle_relevant(self, reasoning, log_entries, add_entry, job_id, start_time):
        """Handle relevant decision: generate teaser, create blog post, move to Relevant."""
        # Move to Relevant stage
        relevant_stage = self.env.ref(
            "newsassistant.news_article_stage_relevant",
            raise_if_not_found=False,
        )
        if relevant_stage:
            self.write({"stage_id": relevant_stage.id})
            add_entry("info", f"Moved to Relevant stage: {reasoning}")
        else:
            add_entry("warning", "Relevant stage not found")

        # Generate teaser
        teaser = self._generate_teaser(log_entries, add_entry)

        if teaser:
            # Create blog post
            self._create_blog_post(teaser, log_entries, add_entry)

        # Create success log
        total_duration = time.time() - start_time
        self._create_digest_log(
            level="success",
            message=f"Digest complete (relevant): {self.title[:50]}",
            duration=total_duration,
            entries=log_entries,
            job_id=job_id,
        )
        _logger.info("Article relevant: %s - %s", self.title, reasoning)

    def _generate_teaser(self, log_entries, add_entry):
        """Generate teaser for relevant article.

        Returns:
            str: Generated teaser or None on failure
        """
        try:
            teaser_prompt = self._get_teaser_prompt()
        except UserError as e:
            add_entry("error", f"Teaser prompt not configured: {e}")
            _logger.error("Teaser prompt error: %s", e)
            return None

        system_prompt = (
            "/no_think\n"
            f"{teaser_prompt}\n\n"
            "Generate a teaser for the following article. "
            "Return ONLY the teaser text, no quotes, no explanation."
        )

        article_content = f"Title: {self.title}\n\n"
        if self.summary:
            article_content += f"Summary: {self.summary}\n\n"
        if self.content:
            from html import unescape
            import re
            clean_content = re.sub(r"<[^>]+>", " ", self.content)
            clean_content = unescape(clean_content)
            clean_content = re.sub(r"\s+", " ", clean_content).strip()
            article_content += f"Content: {clean_content[:3000]}"

        add_entry("info", "Calling LLM for teaser generation")

        try:
            ai_result = self._call_ai(
                system_prompt,
                article_content,
                temperature=0.7,  # Higher temperature for creative output
            )
            teaser = ai_result["content"].strip()

            # Store teaser
            self.write({"teaser": teaser})

            add_entry(
                "info",
                f"Teaser generated ({len(teaser)} chars)",
                duration=ai_result["duration_ms"] / 1000,
                metadata={
                    "teaser": teaser,
                    "usage": ai_result["usage"],
                },
            )
            return teaser

        except RetryableJobError:
            raise
        except Exception as e:
            add_entry("error", f"Teaser generation failed: {e}")
            _logger.exception("Teaser generation error for %s", self.url)
            return None

    def _create_blog_post(self, teaser, log_entries, add_entry):
        """Create blog post with teaser and source link.

        Returns:
            blog.post: Created post or None on failure
        """
        # Check for existing blog post (deduplication)
        existing = self.env["blog.post"].search([
            ("news_article_id", "=", self.id),
        ], limit=1)
        if existing:
            add_entry(
                "info",
                f"Blog post already exists: {existing.id}",
            )
            return existing

        # Get target blog
        try:
            blog = self._get_target_blog()
        except UserError as e:
            add_entry("error", f"Target blog not configured: {e}")
            _logger.error("Target blog error: %s", e)
            return None

        # Format content with teaser and source link
        from urllib.parse import urlparse
        domain = urlparse(self.url).netloc

        content = f"""
<p>{teaser}</p>
<p><a href="{self.url}" target="_blank" rel="noopener noreferrer">
    Read the full article at {domain} →
</a></p>
"""

        # Create blog post
        try:
            post = self.env["blog.post"].create({
                "name": self.title,
                "blog_id": blog.id,
                "content": content,
                "news_article_id": self.id,
                "is_published": True,
            })
            add_entry(
                "info",
                f"Blog post created: {post.id}",
                metadata={"post_id": post.id, "blog_id": blog.id},
            )
            _logger.info("Created blog post %d for article %s", post.id, self.title)
            return post

        except Exception as e:
            add_entry("error", f"Blog post creation failed: {e}")
            _logger.exception("Blog post creation error for %s", self.url)
            return None

    def _create_digest_log(self, level, message, duration=None, entries=None, job_id=None):
        """Create a digest log record using the existing news.log model."""
        Log = self.env["news.log"]
        LogEntry = self.env["news.log.entry"]

        log = Log.create({
            "timestamp": fields.Datetime.now(),
            "level": level,
            "category": "digest",
            "message": message,
            "duration": duration,
            "source_id": self.source_id.id,
            "article_id": self.id,
            "job_id": job_id,
        })

        if entries:
            for entry_data in entries:
                metadata = entry_data.get("metadata")
                if metadata and not isinstance(metadata, str):
                    metadata = json.dumps(metadata, ensure_ascii=False)
                LogEntry.create({
                    "log_id": log.id,
                    "timestamp": entry_data.get("timestamp", fields.Datetime.now()),
                    "level": entry_data.get("level", "info"),
                    "message": entry_data.get("message", ""),
                    "duration": entry_data.get("duration"),
                    "metadata": metadata,
                })

        return log
