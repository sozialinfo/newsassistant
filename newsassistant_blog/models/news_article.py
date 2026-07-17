import base64
import json
import logging
import mimetypes
import os
import re
import time
from functools import partial
from html import unescape
from urllib.parse import urlparse

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.json import scriptsafe as json_scriptsafe

from odoo.addons.newsassistant.models.news_source import parse_ai_json
from odoo.addons.queue_job.exception import RetryableJobError

_logger = logging.getLogger(__name__)

TRANSIENT_HTTP_CODES = {408, 429, 500, 502, 503, 504}
AI_TIMEOUT = 120


class NewsArticle(models.Model):
    _inherit = "news.article"
    _description = "News Article (Blog Extension)"

    # Digest state tracking
    digest_state = fields.Selection(
        [
            ("pending", "Pending"),
            ("processed", "Processed"),
        ],
        default="pending",
        readonly=True,
        index=True,
        string="Evaluation Status",
    )
    teaser = fields.Text(
        string="Teaser",
        readonly=True,
        help="AI-generated teaser for blog publishing",
    )
    blog_reasoning = fields.Text(
        string="Reasoning",
        readonly=True,
        help="AI reasoning for why this article is relevant for the blog",
    )

    # Reverse link to blog post
    blog_post_ids = fields.One2many(
        "blog.post",
        "news_article_id",
        string="Blog Posts",
    )
    blog_post_count = fields.Integer(
        compute="_compute_blog_post_count",
        string="Blog Post Count",
    )

    def _compute_blog_post_count(self):
        """Count blog posts per article using a single batched query."""
        counts = {}
        if self.ids:
            result = self.env["blog.post"].read_group(
                [("news_article_id", "in", self.ids)],
                ["news_article_id"],
                ["news_article_id"],
            )
            counts = {row["news_article_id"][0]: row["news_article_id_count"] for row in result}
        for article in self:
            article.blog_post_count = counts.get(article.id, 0)

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

    def _get_config_param_or_raise(self, key, error_msg):
        val = self.env["ir.config_parameter"].sudo().get_param(key, default="")
        if not val or not val.strip():
            raise UserError(_(error_msg))
        return val.strip()

    def _get_content_strategy(self):
        return self._get_config_param_or_raise(
            "newsassistant_blog.content_strategy",
            "Newsassistant Blog content strategy is not configured. "
            "Please set the 'newsassistant_blog.content_strategy' system parameter."
        )

    def _get_teaser_prompt(self):
        return self._get_config_param_or_raise(
            "newsassistant_blog.teaser_prompt",
            "Newsassistant Blog teaser prompt is not configured. "
            "Please set the 'newsassistant_blog.teaser_prompt' system parameter."
        )

    def _get_target_blog(self):
        blog_id_str = self._get_config_param_or_raise(
            "newsassistant_blog.blog_id",
            "Newsassistant Blog target blog is not configured. "
            "Please set the 'newsassistant_blog.blog_id' system parameter."
        )

        try:
            blog_id = int(blog_id_str.strip())
        except ValueError:
            raise UserError(
                _("Invalid newsassistant_blog.blog_id value: '%s'. Must be a valid blog ID.")
                % blog_id_str
            )

        blog = self.env["blog.blog"].browse(blog_id).exists()
        if not blog:
            raise UserError(
                _("Target blog with ID %d does not exist. "
                  "Please update the 'newsassistant_blog.blog_id' system parameter.")
                % blog_id
            )
        return blog

    def _get_pixabay_api_key(self):
        """Get the Pixabay API key from system parameters.

        Returns:
            str: The API key, or None if not configured.
        """
        api_key = self.env["ir.config_parameter"].sudo().get_param(
            "newsassistant_blog.pixabay_api_key", default=""
        )
        return api_key.strip() if api_key else None

    def _get_pipeline_stage(self, param_key, fallback_name):
        """Get a pipeline stage from settings, falling back to name lookup.

        Args:
            param_key: ir.config_parameter key storing the stage ID (str).
            fallback_name: Stage name to search by if the parameter is unset.

        Returns:
            news.article.stage: The stage record, or empty recordset if not found.
        """
        stage_id_str = self.env["ir.config_parameter"].sudo().get_param(param_key, default="")
        if stage_id_str:
            try:
                stage = self.env["news.article.stage"].browse(int(stage_id_str))
                if stage.exists():
                    return stage
            except (ValueError, TypeError):
                pass
        # Fallback: search by name
        return self.env["news.article.stage"].search([("name", "=", fallback_name)], limit=1)

    def _search_pixabay(self, query):
        """Search Pixabay for images matching the query.

        Args:
            query: Search query (typically article title).

        Returns:
            list: List of image results from Pixabay API, or empty list on failure.

        Raises:
            RetryableJobError: On rate limit or transient errors.
        """
        api_key = self._get_pixabay_api_key()
        if not api_key:
            _logger.debug("Pixabay API key not configured")
            return []

        # Prepare search query - use first ~50 chars for better results
        search_query = query[:50].strip()
        if not search_query:
            return []

        url = "https://pixabay.com/api/"
        params = {
            "key": api_key,
            "q": search_query,
            "image_type": "photo",
            "orientation": "horizontal",
            "min_width": 1000,
            "min_height": 400,
            "safesearch": "true",
            "per_page": 5,
        }

        try:
            response = requests.get(url, params=params, timeout=15)
        except requests.exceptions.Timeout:
            raise RetryableJobError(
                "Pixabay API timeout",
                seconds=300,
                ignore_retry=False,
            )
        except requests.exceptions.ConnectionError as e:
            raise RetryableJobError(
                f"Pixabay API connection error: {e}",
                seconds=300,
                ignore_retry=False,
            )

        if response.status_code == 429:
            raise RetryableJobError(
                "Pixabay API rate limit exceeded",
                seconds=600,
                ignore_retry=False,
            )

        if response.status_code in TRANSIENT_HTTP_CODES:
            raise RetryableJobError(
                f"Pixabay API returned {response.status_code}",
                seconds=300,
                ignore_retry=False,
            )

        if response.status_code != 200:
            _logger.warning(
                "Pixabay API error %d: %s",
                response.status_code,
                response.text[:200],
            )
            return []

        try:
            data = response.json()
            return data.get("hits", [])
        except (ValueError, KeyError) as e:
            _logger.warning("Failed to parse Pixabay response: %s", e)
            return []

    def _download_pixabay_image(self, hit):
        """Download an image from Pixabay search result.

        Args:
            hit: A single result from Pixabay API hits.

        Returns:
            tuple: (image_data, filename) or (None, None) on failure.
        """
        # Prefer largeImageURL for blog headers
        image_url = hit.get("largeImageURL") or hit.get("webformatURL")
        if not image_url:
            return None, None

        try:
            response = requests.get(
                image_url,
                timeout=15,
                headers={"User-Agent": "NewsAssistant/1.0"},
            )
            if response.status_code != 200:
                _logger.debug(
                    "Pixabay image download failed: HTTP %s",
                    response.status_code,
                )
                return None, None

            # Generate filename from Pixabay image ID
            pixabay_id = hit.get("id", "pixabay")
            filename = f"pixabay_{pixabay_id}.jpg"

            return response.content, filename

        except requests.exceptions.RequestException as e:
            _logger.debug("Pixabay image download error: %s", e)
            return None, None

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
            self.write({"digest_state": "pending", "teaser": ""})

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

        Returns:
            dict with keys: content, usage, request, response, duration_ms
        """
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
        """Parse JSON from AI response using the core module's robust parser."""
        return parse_ai_json(raw_text, expect_array=False)

    # -------------------------------------------------------------------------
    # Digest Pipeline
    # -------------------------------------------------------------------------

    @api.model
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

        add_entry = partial(self._add_digest_entry, log_entries)

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

        # Handle decision
        if decision == "discard":
            self._handle_discard(reasoning, log_entries, add_entry)
            self.write({"digest_state": "processed"})
        elif decision == "uncertain":
            self._handle_uncertain(reasoning, log_entries, add_entry)
            self.write({"digest_state": "processed"})
        elif decision == "relevant":
            self._handle_shortlist(reasoning, log_entries, add_entry, job_id, start_time)
            self.write({"digest_state": "processed"})
            return  # _handle_shortlist creates its own log

        # Create log for discard/uncertain
        total_duration = time.time() - start_time
        self._create_digest_log(
            level="success",
            message=f"Digest complete ({decision}): {self.title[:50]}",
            duration=total_duration,
            entries=log_entries,
            job_id=job_id,
        )

    def _add_digest_entry(self, log_entries, level, message, duration=None, metadata=None):
        """Append a structured log entry to the log_entries list."""
        log_entries.append({
            "timestamp": fields.Datetime.now(),
            "level": level,
            "message": message,
            "duration": duration,
            "metadata": metadata,
        })

    def _clean_article_content(self, max_chars=None):
        """Return cleaned article text: stripped HTML, decoded entities, collapsed whitespace."""
        article_content = f"Title: {self.title}\n\n"
        if self.summary:
            article_content += f"Summary: {self.summary}\n\n"
        if self.content:
            clean_content = re.sub(r"<[^>]+>", " ", self.content)
            clean_content = unescape(clean_content)
            clean_content = re.sub(r"\s+", " ", clean_content).strip()
            if max_chars:
                clean_content = clean_content[:max_chars]
            article_content += f"Content: {clean_content}"
        return article_content

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
            '- "reasoning": brief explanation (1-2 sentences) written in the same language as the article\n\n'
            "Return ONLY valid JSON, no markdown, no explanation outside the JSON."
        )

        # Prepare article content for evaluation
        article_content = self._clean_article_content(max_chars=5000)

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
        """Handle discard decision: move to configured discard stage."""
        discard_stage = self._get_pipeline_stage(
            "newsassistant_blog.discard_stage_id", "Discarded"
        )
        self.write({"blog_reasoning": reasoning})
        if discard_stage:
            self.write({"stage_id": discard_stage.id})
            add_entry(
                "info",
                f"Moved to {discard_stage.name} stage: {reasoning}",
            )
        else:
            add_entry("warning", "Discard stage not found")

        _logger.info("Article discarded: %s - %s", self.title, reasoning)

    def _handle_uncertain(self, reasoning, log_entries, add_entry):
        """Handle uncertain decision: move to Shortlist stage for human review."""
        shortlist_stage = self._get_pipeline_stage(
            "newsassistant_blog.shortlist_stage_id", "Shortlist"
        )
        if shortlist_stage:
            self.write({"stage_id": shortlist_stage.id, "blog_reasoning": reasoning})
            add_entry("info", f"Moved to {shortlist_stage.name} stage for human review: {reasoning}")
        else:
            self.write({"blog_reasoning": reasoning})
            add_entry("warning", f"Shortlist stage not found; reasoning stored: {reasoning}")
        _logger.info("Article uncertain: %s - %s", self.title, reasoning)

    def _handle_shortlist(self, reasoning, log_entries, add_entry, job_id, start_time):
        """Handle relevant decision: store reasoning, generate teaser, create blog post, move directly to Published."""
        self.write({"blog_reasoning": reasoning})
        add_entry("info", f"Relevant: {reasoning}")

        # Generate teaser
        teaser_result = self._generate_teaser(log_entries, add_entry)

        if teaser_result:
            # Create blog post
            self._create_blog_post(teaser_result, log_entries, add_entry)

        # Create success log
        total_duration = time.time() - start_time
        self._create_digest_log(
            level="success",
            message=f"Digest complete (relevant): {self.title[:50]}",
            duration=total_duration,
            entries=log_entries,
            job_id=job_id,
        )
        _logger.info("Article shortlisted: %s - %s", self.title, reasoning)

    def _generate_teaser(self, log_entries, add_entry):
        """Generate teaser for relevant article.

        Returns:
            dict: {"teaser": str, "read_more": str} or None on failure.
                  "read_more" is the "Read full article…" link text in the article's language.
        """
        try:
            teaser_prompt = self._get_teaser_prompt()
        except UserError as e:
            add_entry("error", f"Teaser prompt not configured: {e}")
            _logger.error("Teaser prompt error: %s", e)
            return None

        source_language = self.lang_id.name or self.lang_id.code or ""
        language_hint = (
            f" The article is in language '{source_language}'."
            if source_language
            else ""
        )

        system_prompt = (
            "/no_think\n"
            f"{teaser_prompt}\n\n"
            "Generate a teaser for the following article."
            f"{language_hint}\n\n"
            "Return a JSON object with exactly two fields:\n"
            '- "teaser": the teaser text (in the article\'s language)\n'
            '- "read_more": a short link text such as "Read the full article at example.com" '
            "written in the same language as the article\n\n"
            "Return ONLY valid JSON, no markdown, no code fences, no explanation."
        )

        article_content = self._clean_article_content(max_chars=3000)

        add_entry("info", "Calling LLM for teaser generation")

        try:
            ai_result = self._call_ai(
                system_prompt,
                article_content,
                temperature=0.7,  # Higher temperature for creative output
            )
            raw = ai_result["content"].strip()

            # Parse JSON response
            try:
                parsed = self._parse_ai_json(raw)
                teaser = parsed.get("teaser", "").strip()
                read_more = parsed.get("read_more", "").strip()
            except (json.JSONDecodeError, ValueError, AttributeError):
                # Fallback: treat the whole response as teaser text (backward compat)
                _logger.warning(
                    "Teaser response was not JSON for %s, treating as plain text", self.url
                )
                teaser = raw
                read_more = ""

            if not teaser:
                add_entry("error", "Teaser generation returned empty teaser")
                return None

            # Store teaser
            self.write({"teaser": teaser})

            add_entry(
                "info",
                f"Teaser generated ({len(teaser)} chars)",
                duration=ai_result["duration_ms"] / 1000,
                metadata={
                    "teaser": teaser,
                    "read_more": read_more,
                    "usage": ai_result["usage"],
                },
            )
            return {"teaser": teaser, "read_more": read_more}

        except RetryableJobError:
            raise
        except Exception as e:
            add_entry("error", f"Teaser generation failed: {e}")
            _logger.exception("Teaser generation error for %s", self.url)
            return None

    def _create_header_image_attachment(self, image_data, filename, blog_post):
        """Create an ir.attachment for the blog post header image.

        Args:
            image_data: Binary image content.
            filename: Original filename of the image.
            blog_post: The blog.post record to attach the image to.

        Returns:
            ir.attachment: The created attachment record.
        """
        # Determine mimetype from filename
        mimetype, _ = mimetypes.guess_type(filename)
        if not mimetype:
            mimetype = "image/jpeg"  # Default fallback

        attachment = self.env["ir.attachment"].create({
            "name": filename,
            "datas": base64.b64encode(image_data).decode("utf-8"),
            "res_model": "blog.post",
            "res_id": blog_post.id,
            "mimetype": mimetype,
        })
        return attachment

    def _set_blog_cover_properties(self, blog_post, attachment):
        blog_post.write({"cover_properties": json_scriptsafe.dumps({
            "background-image": f"url(/web/image/{attachment.id})",
            "background_color_class": "o_cc3",
            "opacity": "0.4",
            "resize_class": "o_half_screen_height",
        })})

    def _get_header_image_for_blog(self, add_entry):
        """Get header image for blog post: article image or Pixabay fallback.

        Args:
            add_entry: Logging callback function.

        Returns:
            tuple: (image_data, filename, source) where source is 'article', 'pixabay', or None
        """
        # Try article's extracted header image first
        if self.header_image:
            image_data = base64.b64decode(self.header_image)
            filename = self.header_image_filename or "header_image.jpg"
            add_entry(
                "info",
                f"Header image: from article ({filename})",
            )
            return image_data, filename, "article"

        # Try Pixabay fallback
        add_entry("info", "No article header image, trying Pixabay fallback")
        try:
            hits = self._search_pixabay(self.title)
            if hits:
                for hit in hits:
                    image_data, filename = self._download_pixabay_image(hit)
                    if image_data:
                        add_entry(
                            "info",
                            f"Header image: from Pixabay ({filename})",
                            metadata={"pixabay_id": hit.get("id")},
                        )
                        return image_data, filename, "pixabay"
        except RetryableJobError:
            raise
        except Exception as e:
            _logger.warning("Pixabay search failed: %s", e)
            add_entry("warning", f"Pixabay search failed: {e}")

        # No image available
        add_entry(
            "warning",
            "Header image: none (no suitable image found)",
        )
        return None, None, None

    def _create_blog_post(self, teaser_result, log_entries, add_entry):
        """Create blog post with teaser and source link.

        Args:
            teaser_result: dict with "teaser" (str) and "read_more" (str) keys,
                           or a plain str for backward compatibility.

        Returns:
            blog.post: Created post or None on failure
        """
        # Support both dict (new) and plain str (legacy/fallback)
        if isinstance(teaser_result, dict):
            teaser = teaser_result.get("teaser", "")
            read_more = teaser_result.get("read_more", "")
        else:
            teaser = teaser_result
            read_more = ""

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
        domain = urlparse(self.url).netloc if self.url else ""
        # Use AI-generated link text if available, else English fallback
        if not read_more:
            read_more = f"Read the full article at {domain}" if domain else "Read the full article"

        # Substitute {domain} placeholder in AI-generated read_more text
        if domain and "{domain}" in read_more:
            read_more = read_more.replace("{domain}", domain)

        content = f"""
<p>{teaser}</p>
<p><a href="{self.url}" class="btn btn-primary" target="_blank" rel="noopener noreferrer">
    {read_more}
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

            # Move article to configured published stage
            published_stage = self._get_pipeline_stage(
                "newsassistant_blog.published_stage_id", "Published"
            )
            if published_stage:
                self.write({"stage_id": published_stage.id})
                add_entry("info", f"Moved to {published_stage.name} stage")
            else:
                add_entry("warning", "Published stage not found, article stage not updated")

            # Add header image to blog post
            image_data, filename, source = self._get_header_image_for_blog(add_entry)
            if image_data:
                attachment = self._create_header_image_attachment(
                    image_data, filename, post
                )
                self._set_blog_cover_properties(post, attachment)
                add_entry(
                    "info",
                    f"Blog post header image attached ({source})",
                    metadata={"attachment_id": attachment.id},
                )

            return post

        except Exception as e:
            add_entry("error", f"Blog post creation failed: {e}")
            _logger.exception("Blog post creation error for %s", self.url)
            return None

    def _create_digest_log(self, level, message, duration=None, entries=None, job_id=None):
        """Create a digest log record using the existing news.log model.

        Args:
            level (str): Log severity level (e.g. 'info', 'warning', 'error').
            message (str): Human-readable description of the digest operation.
            duration (float, optional): Execution time in seconds.
            entries (list of dict, optional): Per-step log entry data. Each dict may
                contain 'timestamp', 'level', 'message', 'duration', 'metadata'.
            job_id (int, optional): ID of the associated queue job.

        Returns:
            news.log: The created log record.
        """
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
            now = fields.Datetime.now()
            entry_vals = []
            for entry_data in entries:
                metadata = entry_data.get("metadata")
                if metadata and not isinstance(metadata, str):
                    metadata = json_scriptsafe.dumps(metadata, ensure_ascii=False)
                entry_vals.append({
                    "log_id": log.id,
                    "timestamp": entry_data.get("timestamp", now),
                    "level": entry_data.get("level", "info"),
                    "message": entry_data.get("message", ""),
                    "duration": entry_data.get("duration"),
                    "metadata": metadata,
                })
            if entry_vals:
                LogEntry.create(entry_vals)

        return log
