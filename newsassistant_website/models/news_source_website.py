"""Website scraping extension for news.source."""
import base64
import json
import logging
import time
from urllib.parse import urljoin, urlparse

from odoo import _, api, fields, models

from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.newsassistant.models.news_source import normalize_url, parse_ai_json

from .jina_utils import fetch_page, markdown_to_html
from .image_utils import select_header_image

_logger = logging.getLogger(__name__)


class NewsSourceWebsite(models.Model):
    """Extends news.source with website scraping capabilities."""

    _inherit = "news.source"

    def action_scrape_now(self):
        """Manual trigger: queue a scrape job for this source."""
        self.ensure_one()
        self.with_delay(
            channel="root.newsassistant",
            description=f"Manual scrape: {self.name}",
        )._scrape_listing()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Scrape Started"),
                "message": _("Scraping source in background..."),
                "type": "info",
                "sticky": False,
            },
        }

    @api.model
    def _cron_scrape_all(self):
        """Cron entry point: enqueue a scrape job for each active website source."""
        sources = self.search([("active", "=", True), ("source_type", "=", "website")])
        for source in sources:
            source.with_delay(
                channel="root.newsassistant",
                description=f"Scrape listing: {source.name}",
            )._scrape_listing()

    def _create_listing_log(self, level, message, duration=None, entries=None, job_id=None):
        """Create a news.log record for a listing scrape operation."""
        Log = self.env["news.log"]
        LogEntry = self.env["news.log.entry"]

        log_vals = {
            "timestamp": fields.Datetime.now(),
            "level": level,
            "category": "listing",
            "message": message,
            "duration": duration,
            "source_id": self.id,
            "job_id": job_id,
        }

        log = Log.create(log_vals)

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

    def _scrape_listing(self):
        """Queue job: fetch the listing page and discover article URLs.

        Stage 1: Fetches the listing page via Jina Reader API, uses AI to extract
        article URLs, then creates one news.snapshot per article page (which
        auto-triggers extraction on each).
        """
        self.ensure_one()
        _logger.info("Scraping listing for source: %s (%s)", self.name, self.url)

        start_time = time.time()
        log_entries = []

        job_id_ctx = self.env.context.get("job_uuid")
        job_id = None
        if job_id_ctx:
            job = self.env["queue.job"].search([("uuid", "=", job_id_ctx)], limit=1)
            job_id = job.id if job else None

        def add_entry(level, message, duration=None, metadata=None):
            log_entries.append({
                "timestamp": fields.Datetime.now(),
                "level": level,
                "message": message,
                "duration": duration,
                "metadata": metadata,
            })

        add_entry("info", f"Starting listing scrape for {self.name}", metadata={"url": self.url})

        # Fetch listing page via Jina
        jina_start = time.time()
        try:
            content, _ = fetch_page(self.url)
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
            add_entry("error", f"Jina fetch failed: {e}", duration=jina_duration)
            self.write({"state": "error", "error_message": str(e)})
            self._create_listing_log(
                level="error",
                message=f"Fetch failed: {e}",
                duration=time.time() - start_time,
                entries=log_entries,
                job_id=job_id,
            )
            _logger.warning("Fetch error for source %s: %s", self.name, e)
            return

        # AI: discover article URLs from markdown content
        system_prompt = (
            "/no_think\n"
            "You are a news extraction assistant. Given markdown content from a news listing page, "
            "extract all news article links from the MAIN CONTENT AREA (not navigation menus).\n\n"
            "INCLUDE: Individual article links that typically have:\n"
            "- Specific, descriptive titles (not just 'News' or category names)\n"
            "- Publication dates near them\n"
            "- URLs containing patterns like /artikel/, /article/, /post/, /blog/, or date segments\n\n"
            "EXCLUDE:\n"
            "- Navigation menu links\n"
            "- Category/topic index pages (URLs often ending in /news or /category/)\n"
            "- Links with generic titles like 'News', 'Aktuell', 'Blog' that lead to listing pages\n"
            "- Pagination, social media, and footer links\n\n"
            "Return ONLY a JSON object with two fields:\n"
            '- "language": the ISO 639-1 language code of the page content (e.g. "de", "fr", "en")\n'
            '- "articles": a JSON array of objects, each with "title" (string) and "url" (string) fields\n\n'
            "Extract URLs exactly as they appear in the markdown links [text](url). "
            'Return a single valid JSON object like {"language": "de", "articles": [{...}, {...}]}. '
            "No markdown formatting, no explanation, no code fences."
        )

        add_entry("info", "Calling LLM for article URL extraction")
        try:
            ai_result = self._call_infomaniak_ai(system_prompt, content)
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
        except RetryableJobError:
            raise
        except Exception as e:
            error_msg = f"AI extraction error: {e}"
            add_entry("error", error_msg)
            self.write({"state": "error", "error_message": error_msg})
            self._create_listing_log(
                level="error",
                message=error_msg,
                duration=time.time() - start_time,
                entries=log_entries,
                job_id=job_id,
            )
            _logger.exception("AI error for source %s", self.name)
            return

        # Parse AI response
        detected_language = None
        try:
            parsed = parse_ai_json(ai_response, expect_array=False)
            # New format: {"language": "de", "articles": [...]}
            if isinstance(parsed, dict) and "articles" in parsed:
                articles_data = parsed.get("articles", [])
                detected_language = parsed.get("language") or None
            elif isinstance(parsed, list):
                # Fallback: old array format still accepted
                articles_data = parsed
            else:
                raise ValueError("Expected a JSON object with 'articles' key or a JSON array")
            if not isinstance(articles_data, list):
                raise ValueError("'articles' must be a JSON array")
            discovered_urls = [item.get("url", "") for item in articles_data if item.get("url")]
            add_entry(
                "info",
                f"Parsed {len(articles_data)} article links from response"
                + (f" (language: {detected_language})" if detected_language else ""),
                metadata={"discovered_urls": discovered_urls, "language": detected_language},
            )
        except (json.JSONDecodeError, ValueError) as e:
            error_msg = f"Invalid AI response (not valid JSON): {e}"
            add_entry("error", error_msg)
            self.write({"state": "error", "error_message": error_msg})
            self._create_listing_log(
                level="error",
                message=error_msg,
                duration=time.time() - start_time,
                entries=log_entries,
                job_id=job_id,
            )
            _logger.warning("Malformed AI response for source %s", self.name)
            return

        # For each discovered URL: fetch article page and create snapshot
        new_count = 0
        created_snapshot_ids = []

        for item in articles_data:
            title = item.get("title", "").strip()
            url = item.get("url", "").strip()
            if not url:
                continue

            # Resolve relative and protocol-relative URLs
            if url.startswith("//"):
                url = urlparse(self.url).scheme + ":" + url
            elif not url.startswith(("http://", "https://")):
                url = urljoin(self.url, url)

            normalized = normalize_url(url)

            # Skip listing page URL itself
            if normalized == normalize_url(self.url):
                continue

            # Skip non-http URLs
            if not normalized.startswith(("http://", "https://")):
                continue

            # Skip binary resources
            path_lower = urlparse(normalized).path.lower()
            skip_extensions = (
                ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
                ".zip", ".rar", ".gz", ".tar",
                ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
                ".mp3", ".mp4", ".avi", ".mov",
            )
            if path_lower.endswith(skip_extensions):
                continue

            # Dedup: skip if article with this URL already exists
            existing = self.env["news.article"].with_context(active_test=False).search(
                [("url", "=", normalized)], limit=1
            )
            if existing:
                continue

            # Enqueue per-article snapshot creation as a job
            self.with_delay(
                channel="root.newsassistant",
                description=f"Fetch article: {(title or normalized)[:50]}",
            )._fetch_and_create_snapshot(normalized, title)
            new_count += 1

        # Update source state
        total_duration = time.time() - start_time
        self.write({
            "state": "ok",
            "error_message": False,
            "last_scrape_date": fields.Datetime.now(),
        })

        add_entry("info", f"Listing scrape complete: {new_count} new articles enqueued")
        self._create_listing_log(
            level="success",
            message=f"Found {len(articles_data)} articles, {new_count} new enqueued",
            duration=total_duration,
            entries=log_entries,
            job_id=job_id,
        )
        _logger.info("Source %s: discovered %d articles, %d new", self.name, len(articles_data), new_count)

    def _fetch_and_create_snapshot(self, article_url, title=""):
        """Queue job: fetch an article page via Jina and create a news.snapshot.

        The snapshot creation auto-triggers AI extraction via news.snapshot.create().

        Args:
            article_url: The canonical article URL to fetch.
            title: Optional title hint from the listing page.
        """
        self.ensure_one()
        _logger.info("Fetching article page for snapshot: %s", article_url)

        try:
            markdown_content, images_dict = fetch_page(article_url)
        except RetryableJobError:
            raise
        except ValueError as e:
            _logger.warning("Jina fetch failed for %s: %s", article_url, e)
            return

        if not markdown_content or not markdown_content.strip():
            _logger.warning("No content returned from Jina for %s", article_url)
            return

        # Convert Markdown → HTML (canonical format for snapshots)
        html_content = markdown_to_html(markdown_content)

        # Create the snapshot (this auto-enqueues _extract_articles via create())
        snapshot = self.env["news.snapshot"].create({
            "source_id": self.id,
            "raw_content": html_content,
            "url": article_url,
        })

        # Store images_dict on snapshot for later use by website-specific extraction
        # We do this by patching the extraction: override _extract_articles in website module
        # to also handle image selection. Use context to pass images_dict.
        snapshot.with_context(
            website_article_url=article_url,
            website_article_title=title,
            website_images_dict=images_dict,
        )._extract_articles_website()

        _logger.info("Snapshot created for %s (id=%d)", article_url, snapshot.id)


class NewsSnapshotWebsite(models.Model):
    """Website-specific article extraction from snapshots."""

    _inherit = "news.snapshot"

    def _extract_articles_website(self):
        """Website-specific extraction: calls base extraction then adds header image, URL, and language.

        This is called instead of the base _extract_articles() for website-sourced snapshots,
        to add header image selection, URL tracking, and language detection.
        """
        self.ensure_one()
        article_url = self.env.context.get("website_article_url", "")
        article_title = self.env.context.get("website_article_title", "")
        images_dict = self.env.context.get("website_images_dict", {})

        # Run base extraction
        self._extract_articles()

        # Find the article just created
        article = self.env["news.article"].search(
            [("snapshot_id", "=", self.id)], limit=1
        )
        if not article:
            return

        vals = {}

        # Store the article URL (needed for dedup)
        if article_url and not article.url:
            vals["url"] = normalize_url(article_url)

        # Select header image
        if images_dict:
            image_data, filename = select_header_image(images_dict, base_url=article_url)
            if image_data:
                vals["header_image"] = base64.b64encode(image_data).decode("utf-8")
                vals["header_image_filename"] = filename

        # Use title hint if AI didn't extract one
        if article_title and (not article.title or article.title == "Untitled"):
            vals["title"] = article_title

        if vals:
            article.write(vals)
