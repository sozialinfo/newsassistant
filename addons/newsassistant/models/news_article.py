import json
import logging

from odoo import api, fields, models

from odoo.addons.queue_job.exception import RetryableJobError

from .news_source import (
    fetch_page,
    normalize_url,
    parse_ai_json,
)

_logger = logging.getLogger(__name__)


class NewsArticle(models.Model):
    _name = "news.article"
    _description = "News Article"
    _rec_name = "title"
    _order = "scrape_date desc, date desc, id desc"

    title = fields.Char(required=True)
    source_id = fields.Many2one("news.source", required=True, ondelete="cascade")
    url = fields.Char(required=True, index=True)
    date = fields.Date()
    summary = fields.Text()
    content = fields.Html(sanitize=True, sanitize_overridable=True)
    stage_id = fields.Many2one(
        "news.article.stage",
        string="Stage",
        default=lambda self: self._default_stage_id(),
        group_expand="_read_group_stage_ids",
    )
    scrape_date = fields.Datetime(readonly=True)
    active = fields.Boolean(default=True)

    # Extraction state tracking
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("scraped", "Scraped"),
            ("error", "Error"),
            ("skipped", "Skipped"),
        ],
        default="pending",
        readonly=True,
        index=True,
    )
    status_message = fields.Text(readonly=True)
    retry_count = fields.Integer(default=0, readonly=True)
    last_error_date = fields.Datetime(readonly=True)
    log_ids = fields.One2many("news.log", "article_id", string="Logs")

    _sql_constraints = [
        ("url_unique", "UNIQUE(url)", "An article with this URL already exists."),
    ]

    @api.model
    def _default_stage_id(self):
        """Return the 'New' stage as default."""
        return self.env.ref(
            "newsassistant.news_article_stage_new", raise_if_not_found=False
        )

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        """Always show all stages in kanban, even empty ones."""
        return self.env["news.article.stage"].search([])

    def action_refetch(self):
        """Button action: manually re-fetch and re-extract article content."""
        self.ensure_one()
        self.with_delay(
            channel="root.newsassistant",
            description=f"Manual re-fetch: {self.title[:50]}",
        )._fetch_and_extract()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Re-fetch Started",
                "message": f"Re-fetching article in background...",
                "type": "info",
                "sticky": False,
            },
        }

    def action_skip(self):
        """Mark article as skipped and archive it."""
        self.ensure_one()
        self.write({"state": "skipped", "active": False})

    def action_reset(self):
        """Reset skipped article to pending state and unarchive."""
        self.ensure_one()
        self.write({
            "state": "pending",
            "status_message": False,
            "last_error_date": False,
            "retry_count": 0,
            "active": True,
        })

    def _create_log(self, level, message, duration=None, entries=None, job_id=None):
        """Create a unified log record with optional detail entries.

        Args:
            level: 'success', 'warning', or 'error'
            message: Summary message
            duration: Total duration in seconds (optional)
            entries: List of entry dicts with keys: level, message, duration, metadata (optional)
            job_id: Related queue job ID (optional)

        Returns:
            The created news.log record
        """
        Log = self.env["news.log"]
        LogEntry = self.env["news.log.entry"]

        log = Log.create({
            "timestamp": fields.Datetime.now(),
            "level": level,
            "category": "extraction",
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

    def _fetch_and_extract(self):
        """Queue job: fetch article page and extract content using AI.

        Stage 2 of the two-stage pipeline. Fetches the individual article
        page using Jina Reader API (renders JavaScript, handles PDFs),
        and uses AI to extract structured content.
        """
        import time
        self.ensure_one()
        _logger.info("Extracting article: %s (%s)", self.title, self.url)

        start_time = time.time()
        log_entries = []

        # Try to get current job ID from context
        job_id = self.env.context.get("job_uuid")
        if job_id:
            job = self.env["queue.job"].search([("uuid", "=", job_id)], limit=1)
            job_id = job.id if job else None

        # Helper to add log entry
        def add_entry(level, message, duration=None, metadata=None):
            log_entries.append({
                "timestamp": fields.Datetime.now(),
                "level": level,
                "message": message,
                "duration": duration,
                "metadata": metadata,
            })

        # Helper to set error state and create log
        def set_error(error_msg):
            self.write({
                "state": "error",
                "status_message": error_msg,
                "last_error_date": fields.Datetime.now(),
                "retry_count": self.retry_count + 1,
                "scrape_date": fields.Datetime.now(),
            })
            add_entry("error", error_msg)
            self._create_log(
                level="error",
                message=error_msg,
                duration=time.time() - start_time,
                entries=log_entries,
                job_id=job_id,
            )

        add_entry(
            "info",
            f"Starting extraction for: {self.title[:50]}",
            metadata={"url": self.url, "source": self.source_id.name},
        )

        # Fetch article page via Jina (renders JavaScript, handles PDFs)
        jina_start = time.time()
        try:
            content = fetch_page(self.url)
            jina_duration = time.time() - jina_start
            add_entry(
                "info",
                f"Jina fetch complete ({len(content)} chars)",
                duration=jina_duration,
                metadata={"url": self.url, "content_length": len(content)},
            )
        except RetryableJobError:
            raise
        except ValueError as e:
            jina_duration = time.time() - jina_start
            add_entry(
                "error",
                f"Jina fetch failed: {e}",
                duration=jina_duration,
                metadata={"url": self.url, "error": str(e)},
            )
            _logger.warning("Fetch error for article %s: %s", self.url, e)
            set_error(str(e))
            return

        if not content or not content.strip():
            add_entry("error", "No content returned from Jina", metadata={"url": self.url})
            _logger.warning("No content extracted from %s", self.url)
            set_error("No content could be extracted")
            return

        # AI Stage 2: validate and extract article content from markdown
        system_prompt = (
            "/no_think\n"
            "You are a news extraction assistant. Given markdown content, first determine if this "
            "is a SINGLE news article or blog post.\n\n"
            "It is NOT an article if it is:\n"
            "- A listing/index page showing multiple articles\n"
            "- A category or topic overview page\n"
            "- A navigation page, homepage, or search results\n"
            "- A page without substantial article body text\n\n"
            "If NOT an article, return: {\"is_article\": false, \"reason\": \"brief explanation\"}\n\n"
            "If it IS an article, extract the content and return:\n"
            "{\n"
            '  "is_article": true,\n'
            '  "title": "the article title (string)",\n'
            '  "date": "publication date YYYY-MM-DD or null",\n'
            '  "summary": "2-3 sentence summary (string)",\n'
            '  "content": "full article as clean HTML"\n'
            "}\n\n"
            "For the content field: Use semantic HTML tags (h2, h3, p, ul, ol, li, strong, em). "
            "Do NOT include html, head, body, nav, header, footer, script, style tags. "
            "Just the article body content. No navigation, no boilerplate, no ads.\n"
            "Keep the original language. Do not translate.\n"
            "IMPORTANT: Return a single valid JSON object. No markdown formatting, no code fences."
        )

        add_entry("info", "Calling LLM for content extraction")
        try:
            ai_result = self.source_id._call_infomaniak_ai(
                system_prompt, content
            )
            ai_response = ai_result["content"]
            # Log LLM interaction with full metadata
            add_entry(
                "info",
                f"LLM response received ({ai_result['usage']['total_tokens']} tokens)",
                duration=ai_result["duration_ms"] / 1000,
                metadata={
                    "request": ai_result["request"],
                    "response": ai_result["response"],
                    "usage": ai_result["usage"],
                    "timing": {"duration_ms": ai_result["duration_ms"]},
                },
            )
        except RetryableJobError:
            raise
        except Exception as e:
            _logger.exception("AI error extracting article %s", self.url)
            set_error(f"AI extraction failed: {e}")
            return

        # Parse AI response
        try:
            article_data = parse_ai_json(ai_response, expect_array=False)
            # If we got a list, take the first element
            if isinstance(article_data, list) and article_data:
                article_data = article_data[0]
            if not isinstance(article_data, dict):
                raise ValueError("Expected a JSON object")
        except (json.JSONDecodeError, ValueError) as e:
            add_entry(
                "error",
                f"Failed to parse AI response: {e}",
                metadata={"error": str(e), "raw_response_preview": ai_response[:500]},
            )
            _logger.warning(
                "Malformed AI response for article %s: %s",
                self.url,
                ai_response[:500],
            )
            set_error(f"Invalid AI response: {e}")
            return

        # Check if content was validated as NOT an article
        if article_data.get("is_article") is False:
            reason = article_data.get("reason", "Content is not a single article")
            add_entry(
                "warning",
                f"Not an article: {reason}",
                metadata={"url": self.url, "reason": reason},
            )
            self.write({
                "state": "skipped",
                "status_message": f"Not an article: {reason}",
                "scrape_date": fields.Datetime.now(),
                "active": False,
            })
            total_duration = time.time() - start_time
            self._create_log(
                level="warning",
                message=f"Skipped (not an article): {self.title[:50]}",
                duration=total_duration,
                entries=log_entries,
                job_id=job_id,
            )
            _logger.info("Skipped non-article: %s - %s", self.url, reason)
            return

        # Validated as article - log and proceed with extraction
        add_entry(
            "info",
            "Successfully parsed article data from LLM response",
            metadata={
                "extracted_title": article_data.get("title", "")[:100],
                "extracted_date": article_data.get("date"),
                "has_summary": bool(article_data.get("summary")),
                "has_content": bool(article_data.get("content")),
            },
        )

        # Update article with extracted data - success!
        vals = {
            "scrape_date": fields.Datetime.now(),
            "state": "scraped",
            "status_message": False,
            "last_error_date": False,
        }

        if article_data.get("title"):
            vals["title"] = article_data["title"]
        if article_data.get("date"):
            try:
                vals["date"] = article_data["date"]
            except Exception:
                _logger.warning(
                    "Invalid date format from AI for article %s: %s",
                    self.url,
                    article_data.get("date"),
                )
        if article_data.get("summary"):
            vals["summary"] = article_data["summary"]
        if article_data.get("content"):
            vals["content"] = article_data["content"]

        self.write(vals)

        total_duration = time.time() - start_time
        add_entry(
            "info",
            f"Article extraction complete: {self.title[:50]}",
            metadata={
                "url": self.url,
                "title": self.title,
                "date": str(self.date) if self.date else None,
                "has_summary": bool(self.summary),
                "has_content": bool(self.content),
            },
        )

        self._create_log(
            level="success",
            message=f"Extracted: {self.title[:50]}",
            duration=total_duration,
            entries=log_entries,
            job_id=job_id,
        )
        _logger.info("Successfully extracted article: %s", self.title)
