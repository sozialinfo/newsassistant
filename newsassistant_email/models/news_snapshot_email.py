"""Inbound email handler for news.snapshot."""
import json
import logging
import re
import time

from bs4 import BeautifulSoup

from odoo import _, fields, models
from odoo.addons.queue_job.exception import RetryableJobError

from odoo.addons.newsassistant.models.news_source import parse_ai_json

_logger = logging.getLogger(__name__)


def extract_domain(email_from):
    """Extract the domain from an email address string.

    Handles formats like:
    - user@example.com
    - "Display Name" <user@example.com>
    - user@example.com, other@example.com (takes first)

    Args:
        email_from: The From header string.

    Returns:
        The domain string (e.g. 'example.com') or None if not parseable.
    """
    if not email_from:
        return None
    # Extract email address from angle brackets or plain
    match = re.search(r"[\w.+-]+@([\w.-]+\.[a-zA-Z]{2,})", email_from)
    if match:
        return match.group(1).lower()
    return None


def sanitize_email_html(html_content):
    """Sanitize inbound email HTML for storage.

    Removes:
    - <script> and <style> tags
    - Tracking pixels (1x1 images)
    - Common email-specific junk elements

    Args:
        html_content: Raw HTML from email body.

    Returns:
        Sanitized HTML string.
    """
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, "lxml")

    # Remove scripts and styles
    for tag in soup.find_all(["script", "style", "noscript"]):
        tag.decompose()

    # Remove tracking pixels (1x1 images)
    for img in soup.find_all("img"):
        width = img.get("width", "")
        height = img.get("height", "")
        try:
            if int(width) <= 1 and int(height) <= 1:
                img.decompose()
                continue
        except (ValueError, TypeError):
            pass
        # Also remove by common tracking URL patterns
        src = img.get("src", "")
        if any(pattern in src.lower() for pattern in ["track", "pixel", "beacon", "open.gif"]):
            img.decompose()

    # Remove hidden elements often used for tracking
    for tag in soup.find_all(style=re.compile(r"display\s*:\s*none")):
        tag.decompose()

    return str(soup)


class NewsSnapshotEmail(models.Model):
    """Extends news.snapshot with inbound email handling via mail.alias.mixin."""

    _name = "news.snapshot"
    _inherit = ["news.snapshot", "mail.thread", "mail.alias.mixin"]
    _description = "News Snapshot (Email)"

    def _alias_get_creation_values(self):
        """Return default values for the mail alias."""
        values = super()._alias_get_creation_values()
        values["alias_model_id"] = self.env["ir.model"]._get("news.snapshot").id
        return values

    @classmethod
    def _get_alias_model_name(cls, vals):
        return "news.snapshot"

    def message_new(self, msg_dict, custom_values=None):
        """Handle inbound email: create listing snapshot, auto-create source if needed.

        Called by Odoo's mail framework when a new email arrives at the alias.

        Creates a listing snapshot (``is_listing=True``) with the email body as
        raw content. The snapshot's ``_discover_articles()`` is then enqueued on
        the ``root.email_extraction`` channel to split the newsletter into
        individual article sections.

        Args:
            msg_dict: Dict with email metadata (email_from, body, subject, etc.)
            custom_values: Additional values to set on the created record.

        Returns:
            The created news.snapshot record.
        """
        email_from = msg_dict.get("email_from", "")
        body = msg_dict.get("body", "")
        subject = msg_dict.get("subject", "")

        _logger.info("Inbound email received from: %s, subject: %s", email_from, subject)

        # Extract sender domain
        domain = extract_domain(email_from)
        if not domain:
            _logger.warning("Could not extract domain from email_from: %s", email_from)
            domain = "unknown"

        # Lookup or auto-create the news.source for this domain
        source = self._get_or_create_email_source(domain)

        # Sanitize email HTML body
        clean_body = sanitize_email_html(body) if body else ""

        # Create the listing snapshot — use skip_snapshot_extraction so the base
        # create() doesn't enqueue on the generic channel; we enqueue below
        # on the dedicated email sub-channel for immediate processing.
        create_vals = {
            "source_id": source.id,
            "raw_content": clean_body,
            "is_listing": True,
        }
        if custom_values:
            create_vals.update(custom_values)

        snapshot = self.env["news.snapshot"].with_context(
            skip_snapshot_extraction=True
        ).create(create_vals)

        # Enqueue discovery on the email-specific channel (higher priority,
        # separate from the website scraping backlog)
        snapshot.with_delay(
            channel="root.email_extraction",
            description=f"Email discovery: {snapshot.name}",
        )._discover_articles()

        # Create an email inbound log entry
        try:
            self.env["news.log"].create({
                "timestamp": fields.Datetime.now(),
                "level": "success",
                "category": "email",
                "message": f"Email received from {email_from}: {subject[:80]}",
                "source_id": source.id,
                "snapshot_id": snapshot.id,
            })
        except Exception:
            _logger.exception("Failed to create email log")

        return snapshot

    # -------------------------------------------------------------------------
    # Newsletter Article Discovery
    # -------------------------------------------------------------------------

    _NEWSLETTER_SPLIT_PROMPT = (
        "/no_think\n"
        "You are a newsletter extraction assistant. Given the text content of a newsletter, "
        "identify all individual news articles or stories within it.\n\n"
        "Each article typically has:\n"
        "- A headline or title (often in h1, h2, or a styled heading tag)\n"
        "- A body paragraph or summary\n"
        "- Possibly a date, author, or read-more link\n\n"
        "EXCLUDE:\n"
        "- Navigation links, footer sections, social media links\n"
        "- Unsubscribe links, advertisement banners, sponsored content\n"
        "- Repeated headers/footers of the newsletter itself\n\n"
        "INCLUDE the COMPLETE article body text for each article, not just the teaser.\n"
        "The 'content' field must contain the full body of the article including all HTML\n"
        "paragraphs, lists, and formatting — everything a reader would see as the article.\n\n"
        "Return a JSON object with a single field:\n"
        '- "articles": a JSON array of objects, each with:\n'
        '    - "title": the article headline (string)\n'
        '    - "content": the FULL article body text with all HTML markup (string)\n\n'
        'Return a single valid JSON object like {"articles": [{"title": "...", "content": "..."}, ...]}. '
        "No markdown formatting, no explanation, no code fences."
    )

    def _discover_articles_email(self):
        """Discover article sections from a newsletter listing snapshot.

        Sends the newsletter HTML to the AI to identify individual article
        sections. For each section found, creates a child snapshot with
        ``parent_id`` pointing to this listing snapshot. Each child snapshot
        auto-enqueues ``_extract_articles()`` for single-article extraction.
        """
        self.ensure_one()
        _logger.info("Discovering articles from newsletter listing: %s", self.name)

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

        add_entry("info", f"Starting newsletter article discovery: {self.name}")

        if not self.raw_content or not self.raw_content.strip():
            add_entry("warning", "Newsletter has no content — skipping discovery")
            self._create_discovery_log(
                level="warning",
                message="No content to discover",
                duration=time.time() - start_time,
                entries=log_entries,
                job_id=job_id,
            )
            _logger.warning("Newsletter snapshot %s has no raw_content", self.name)
            return

        add_entry("info", "Calling LLM for newsletter article splitting")
        # Extract plain text to reduce token count and avoid timeout
        content_soup = BeautifulSoup(self.raw_content, "lxml")
        for tag_name in ("script", "style", "nav", "footer", "aside", "noscript", "svg", "iframe"):
            for tag in content_soup.find_all(tag_name):
                tag.decompose()
        clean_text = content_soup.get_text(separator="\n", strip=True)
        # Truncate to avoid AI timeout on very large newsletters
        if len(clean_text) > 20000:
            clean_text = clean_text[:20000]
        add_entry("info", f"Text content: {len(clean_text)} chars (was {len(self.raw_content)} chars HTML)")
        try:
            ai_result = self.source_id._call_infomaniak_ai(
                self._NEWSLETTER_SPLIT_PROMPT, clean_text, temperature=0.1
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
        except RetryableJobError:
            raise
        except Exception as e:
            _logger.exception("AI error discovering articles from newsletter %s", self.name)
            add_entry("error", f"AI newsletter splitting failed: {e}")
            self._create_discovery_log(
                level="error",
                message=f"AI newsletter splitting failed: {e}",
                duration=time.time() - start_time,
                entries=log_entries,
                job_id=job_id,
            )
            return

        # Parse AI response
        try:
            parsed = parse_ai_json(ai_response, expect_array=False)
            if isinstance(parsed, dict) and "articles" in parsed:
                articles_data = parsed["articles"]
            elif isinstance(parsed, list):
                articles_data = parsed
            else:
                raise ValueError("Expected a JSON object with 'articles' key")
            if not isinstance(articles_data, list):
                raise ValueError("'articles' must be a JSON array")
        except (ValueError, json.JSONDecodeError) as e:
            add_entry("error", f"Invalid AI response: {e}",
                      metadata={"raw_response_preview": ai_response[:500]})
            self._create_discovery_log(
                level="error",
                message=f"Invalid AI response: {e}",
                duration=time.time() - start_time,
                entries=log_entries,
                job_id=job_id,
            )
            return

        if not articles_data:
            add_entry("warning", "No articles identified in newsletter")
            self._create_discovery_log(
                level="warning",
                message="No articles found in newsletter",
                duration=time.time() - start_time,
                entries=log_entries,
                job_id=job_id,
            )
            return

        # Create articles directly from the newsletter split — the content is
        # already inline (no separate fetch needed), and the AI has already
        # extracted title + content. Child snapshots are created for audit
        # purposes but articles are created immediately to avoid the
        # single-article extraction prompt rejecting short teaser content.
        Article = self.env["news.article"]
        created_count = 0
        for article_item in articles_data:
            title = (article_item.get("title") or "").strip()
            content = (article_item.get("content") or "").strip()
            if not content:
                continue

            # Create a child snapshot for audit trail
            child = self.env["news.snapshot"].with_context(
                skip_snapshot_extraction=True
            ).create({
                "source_id": self.source_id.id,
                "parent_id": self.id,
                "raw_content": content,
                "is_listing": False,
            })

            # Create article directly from the newsletter split data
            now = fields.Datetime.now()
            article = Article.create({
                "snapshot_id": child.id,
                "title": title or "Untitled",
                "state": "scraped",
                "scrape_date": now,
                "date": fields.Date.today(),
                "summary": content[:200] if len(content) > 200 else content,
                "content": content,
            })
            created_count += 1
            add_entry("info", f"Article created: {title[:50]} (id={article.id})",
                      metadata={"article_id": article.id, "title": title, "child_id": child.id})

        add_entry("info", f"Discovery complete: {created_count} articles created")
        self._create_discovery_log(
            level="success",
            message=f"Discovered {created_count} articles from newsletter",
            duration=time.time() - start_time,
            entries=log_entries,
            job_id=job_id,
        )
        _logger.info("Newsletter %s: discovered %d articles", self.name, created_count)

    def _create_discovery_log(self, level, message, duration=None, entries=None, job_id=None, created_count=0):
        """Create a news.log record for a newsletter discovery operation."""
        Log = self.env["news.log"]
        LogEntry = self.env["news.log.entry"]

        log = Log.create({
            "timestamp": fields.Datetime.now(),
            "level": level,
            "category": "email",
            "message": message,
            "duration": duration,
            "source_id": self.source_id.id,
            "snapshot_id": self.id,
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

    def _get_or_create_email_source(self, domain):
        """Look up an email source by sender domain, or create one.

        Args:
            domain: The sender's email domain (e.g. 'example.com').

        Returns:
            A news.source record.
        """
        NewsSource = self.env["news.source"]

        # Look for existing email source with this domain
        source = NewsSource.search(
            [("source_type", "=", "email"), ("sender_domain", "=", domain)],
            limit=1,
        )
        if source:
            _logger.info("Found existing email source for domain %s: %s", domain, source.name)
            return source

        # Auto-create: ask AI for the publication name
        name = self._ai_get_source_name(domain)

        _logger.info("Creating new email source for domain %s with name '%s'", domain, name)
        source = NewsSource.create({
            "name": name,
            "source_type": "email",
            "sender_domain": domain,
            "active": True,
            "state": "ok",
        })
        return source

    def _ai_get_source_name(self, domain):
        """Use AI to determine the publication name for an email domain.

        Falls back to the domain name if AI call fails.

        Args:
            domain: The sender domain (e.g. 'morningbrew.com').

        Returns:
            A human-readable publication name string.
        """
        try:
            system_prompt = (
                "/no_think\n"
                "You are a knowledgeable assistant. Given an email domain, return ONLY the "
                "well-known publication or newsletter name associated with that domain. "
                "Return just the name, nothing else. If you don't know it, return the domain itself."
            )
            user_content = f"Email domain: {domain}"

            result = self.source_id._call_infomaniak_ai(system_prompt, user_content)
            name = result.get("content", "").strip()

            name = name.strip('"\'').strip()
            if name and len(name) <= 100:
                return name
        except RetryableJobError:
            raise
        except (KeyError, AttributeError) as e:
            _logger.warning("AI source naming failed for domain %s: %s", domain, e)

        # Fallback: use domain
        return domain
