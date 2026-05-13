import json
import logging
import threading
import time
from datetime import datetime

from odoo import api, fields, models
from odoo.addons.queue_job.exception import RetryableJobError

from .news_source import parse_ai_json

_logger = logging.getLogger(__name__)


class NewsSnapshot(models.Model):
    """Raw content capture between a news source and its extracted articles.

    A snapshot represents a point-in-time capture of content from a news source.
    Website sources create one snapshot per article page (fetched via Jina).
    Email sources create one snapshot per received email.

    On creation, a queue job is automatically enqueued to extract articles.
    """

    _name = "news.snapshot"
    _description = "News Snapshot"
    _rec_name = "name"
    _order = "captured_at desc, id desc"

    name = fields.Char(
        compute="_compute_name",
        store=True,
        string="Snapshot",
    )
    source_id = fields.Many2one(
        "news.source",
        string="Source",
        required=True,
        ondelete="cascade",
        index=True,
    )
    url = fields.Char(
        string="URL",
        index=True,
        help="Exact URL of the web page that was fetched to produce this snapshot.",
    )
    raw_content = fields.Html(
        string="Raw Content",
        sanitize=False,
        help="Captured HTML content — the raw input for article extraction.",
    )
    captured_at = fields.Datetime(
        string="Captured At",
        default=fields.Datetime.now,
        readonly=True,
        index=True,
    )
    article_ids = fields.One2many(
        "news.article",
        "snapshot_id",
        string="Articles",
    )
    article_count = fields.Integer(
        compute="_compute_article_count",
        string="Article Count",
    )

    @api.depends("source_id", "captured_at")
    def _compute_name(self):
        for snapshot in self:
            if snapshot.source_id and snapshot.captured_at:
                dt_str = fields.Datetime.context_timestamp(
                    snapshot, snapshot.captured_at
                ).strftime("%Y-%m-%d %H:%M")
                snapshot.name = f"{snapshot.source_id.name} – {dt_str}"
            elif snapshot.source_id:
                snapshot.name = snapshot.source_id.name
            else:
                snapshot.name = "Snapshot"

    def _compute_article_count(self):
        for snapshot in self:
            snapshot.article_count = len(snapshot.article_ids)

    @api.model_create_multi
    def create(self, vals_list):
        """Create snapshots and auto-enqueue article extraction for each.

        Enqueueing is suppressed when context key ``skip_snapshot_extraction=True``
        is set (used in test fixtures and demo data loading to avoid unwanted AI calls).

        During test runs, use ``trap_jobs()`` from OCA queue_job to intercept
        enqueued jobs without making real API calls.
        """
        snapshots = super().create(vals_list)
        if not self.env.context.get("skip_snapshot_extraction"):
            for snapshot in snapshots:
                snapshot.with_delay(
                    channel="root.newsassistant",
                    description=f"Extract articles: {snapshot.name}",
                )._extract_articles()
        return snapshots

    # -------------------------------------------------------------------------
    # Article Extraction
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # Extraction Prompt
    # -------------------------------------------------------------------------

    _EXTRACTION_SYSTEM_PROMPT = (
        "/no_think\n"
        "You are a news extraction assistant. Given HTML content, first determine if this "
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
        '  "language": "ISO 639-1 language code of the article (e.g. \\"de\\", \\"fr\\", \\"en\\")",\n'
        '  "summary": "2-3 sentence summary (string)",\n'
        '  "content": "full article as clean HTML"\n'
        "}\n\n"
        "For the content field: Use semantic HTML tags (h2, h3, p, ul, ol, li, strong, em). "
        "Do NOT include html, head, body, nav, header, footer, script, style tags. "
        "Just the article body content. No navigation, no boilerplate, no ads.\n"
        "Keep the original language. Do not translate.\n"
        "IMPORTANT: Return a single valid JSON object. No markdown formatting, no code fences."
    )

    def _extract_articles(self):
        """Queue job: extract articles from this snapshot's raw HTML content.

        Reads raw_content (HTML) and calls Infomaniak AI to extract structured
        article data. Creates a news.article record for each valid article found.
        Creates a news.log record summarising the result.
        """
        self.ensure_one()
        _logger.info("Extracting articles from snapshot: %s", self.name)

        start_time = time.time()
        log_entries = []

        job_id = self._resolve_job_id()

        def add_entry(level, message, duration=None, metadata=None):
            log_entries.append({
                "timestamp": fields.Datetime.now(),
                "level": level,
                "message": message,
                "duration": duration,
                "metadata": metadata,
            })

        add_entry("info", f"Starting extraction for snapshot: {self.name}")

        if not self.raw_content or not self.raw_content.strip():
            add_entry("warning", "Snapshot has no raw content — skipping extraction")
            self._create_snapshot_log(
                level="warning",
                message="No content to extract",
                duration=time.time() - start_time,
                entries=log_entries,
                job_id=job_id,
            )
            _logger.warning("Snapshot %s has no raw_content", self.name)
            return

        ai_result, ai_response = self._extraction_call_ai(add_entry, start_time, log_entries, job_id)
        if ai_result is None:
            return

        article_data = self._extraction_parse_response(ai_response, add_entry, start_time, log_entries, job_id)
        if article_data is None:
            return

        if article_data.get("is_article") is False:
            reason = article_data.get("reason", "Content is not a single article")
            add_entry("warning", f"Not an article: {reason}", metadata={"reason": reason})
            self._create_snapshot_log(
                level="warning",
                message=f"Skipped (not an article): {reason}",
                duration=time.time() - start_time,
                entries=log_entries,
                job_id=job_id,
            )
            _logger.info("Snapshot %s is not an article: %s", self.name, reason)
            return

        article = self._extraction_create_article(article_data, add_entry)

        self._create_snapshot_log(
            level="success",
            message=f"Extracted: {article.title[:50]}",
            duration=time.time() - start_time,
            entries=log_entries,
            article_id=article.id,
            job_id=job_id,
        )
        _logger.info("Successfully extracted article from snapshot: %s", article.title)

    def _resolve_job_id(self):
        """Resolve the current queue.job record ID from context."""
        job_id_ctx = self.env.context.get("job_uuid")
        if not job_id_ctx:
            return None
        job = self.env["queue.job"].search([("uuid", "=", job_id_ctx)], limit=1)
        return job.id if job else None

    def _extraction_call_ai(self, add_entry, start_time, log_entries, job_id):
        """Call the AI for article extraction.

        Returns:
            tuple: (ai_result dict, ai_response str) or (None, None) on error.
        """
        add_entry("info", "Calling LLM for content extraction")
        try:
            ai_result = self.source_id._call_infomaniak_ai(
                self._EXTRACTION_SYSTEM_PROMPT, self.raw_content
            )
            ai_response = ai_result["content"]
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
            return ai_result, ai_response
        except Exception as e:
            if isinstance(e, RetryableJobError):
                raise
            _logger.exception("AI error extracting from snapshot %s", self.name)
            add_entry("error", f"AI extraction failed: {e}")
            self._create_snapshot_log(
                level="error",
                message=f"AI extraction failed: {e}",
                duration=time.time() - start_time,
                entries=log_entries,
                job_id=job_id,
            )
            return None, None

    def _extraction_parse_response(self, ai_response, add_entry, start_time, log_entries, job_id):
        """Parse the AI response JSON.

        Returns:
            dict: Parsed article data, or None on error.
        """
        try:
            article_data = parse_ai_json(ai_response, expect_array=False)
            if isinstance(article_data, list) and article_data:
                article_data = article_data[0]
            if not isinstance(article_data, dict):
                raise ValueError("Expected a JSON object")
            return article_data
        except (ValueError, Exception) as e:
            add_entry(
                "error",
                f"Failed to parse AI response: {e}",
                metadata={"error": str(e), "raw_response_preview": ai_response[:500]},
            )
            _logger.warning("Malformed AI response for snapshot %s: %s", self.name, ai_response[:500])
            self._create_snapshot_log(
                level="error",
                message=f"Invalid AI response: {e}",
                duration=time.time() - start_time,
                entries=log_entries,
                job_id=job_id,
            )
            return None

    def _extraction_create_article(self, article_data, add_entry):
        """Create or update a news.article from parsed article data.

        Returns:
            news.article: The created or updated article record.
        """
        add_entry("info", "Successfully parsed article data from LLM response")

        Article = self.env["news.article"]
        vals = {
            "snapshot_id": self.id,
            "title": article_data.get("title") or "Untitled",
            "state": "scraped",
            "scrape_date": fields.Datetime.now(),
        }
        if article_data.get("date"):
            try:
                datetime.strptime(article_data["date"], "%Y-%m-%d")
                vals["date"] = article_data["date"]
            except (ValueError, TypeError):
                vals["date"] = fields.Date.today()
        else:
            vals["date"] = fields.Date.today()
        if article_data.get("summary"):
            vals["summary"] = article_data["summary"]
        if article_data.get("content"):
            vals["content"] = article_data["content"]
        if article_data.get("language"):
            lang_code = article_data["language"].strip().lower()[:2]
            lang = self.env["res.lang"].with_context(active_test=False).search(
                [("code", "=like", lang_code + "%")], limit=1
            )
            if lang:
                vals["lang_id"] = lang.id

        # Avoid duplicate articles for the same snapshot
        existing = Article.search([("snapshot_id", "=", self.id)], limit=1)
        if existing:
            add_entry("info", f"Article already exists for snapshot, updating: {existing.title}")
            existing.write({k: v for k, v in vals.items() if k != "snapshot_id"})
            return existing

        article = Article.create(vals)
        add_entry(
            "info",
            f"Article created/updated: {article.title[:50]}",
            metadata={"article_id": article.id, "title": article.title},
        )
        return article

    def _create_snapshot_log(self, level, message, duration=None, entries=None, article_id=None, job_id=None):
        """Create a news.log record for this snapshot's extraction."""
        Log = self.env["news.log"]
        LogEntry = self.env["news.log.entry"]

        log = Log.create({
            "timestamp": fields.Datetime.now(),
            "level": level,
            "category": "extraction",
            "message": message,
            "duration": duration,
            "source_id": self.source_id.id,
            "snapshot_id": self.id,
            "article_id": article_id,
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
