"""Inbound email handler for news.snapshot."""
import logging
import re

from bs4 import BeautifulSoup

from odoo import fields, models

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
        """Handle inbound email: create snapshot, auto-create source if needed.

        Called by Odoo's mail framework when a new email arrives at the alias.

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
            # Create without source — use a fallback
            domain = "unknown"

        # Lookup or auto-create the news.source for this domain
        source = self._get_or_create_email_source(domain)

        # Sanitize email HTML body
        clean_body = sanitize_email_html(body) if body else ""

        # Create the snapshot — use skip_snapshot_extraction so the base
        # create() doesn't enqueue on the generic channel; we enqueue below
        # on the dedicated email sub-channel for immediate processing.
        create_vals = {
            "source_id": source.id,
            "raw_content": clean_body,
        }
        if custom_values:
            create_vals.update(custom_values)

        snapshot = self.env["news.snapshot"].with_context(
            skip_snapshot_extraction=True
        ).create(create_vals)

        # Enqueue extraction on the email-specific channel (higher priority,
        # separate from the website scraping backlog)
        snapshot.with_delay(
            channel="root.email_extraction",
            description=f"Email extraction: {snapshot.name}",
        )._extract_articles()

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
        # Use a temporary source record for the AI call
        # We call the AI via a dummy source or directly
        try:
            system_prompt = (
                "/no_think\n"
                "You are a knowledgeable assistant. Given an email domain, return ONLY the "
                "well-known publication or newsletter name associated with that domain. "
                "Return just the name, nothing else. If you don't know it, return the domain itself."
            )
            user_content = f"Email domain: {domain}"

            # Call AI via a minimal news.source record context
            # We use an existing source or create temp env
            dummy = self.env["news.source"].new({"name": domain, "source_type": "email"})
            result = dummy._call_infomaniak_ai(system_prompt, user_content)
            name = result.get("content", "").strip()

            # Clean up the name
            name = name.strip('"\'').strip()
            if name and len(name) <= 100:
                return name
        except Exception as e:
            _logger.warning("AI source naming failed for domain %s: %s", domain, e)

        # Fallback: use domain
        return domain
