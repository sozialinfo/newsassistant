"""Tests for email utility functions."""
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.newsassistant_email.models.news_snapshot_email import (
    extract_domain,
    sanitize_email_html,
)


@tagged("post_install", "-at_install")
class TestExtractDomain(TransactionCase):
    """Tests for extract_domain()."""

    def test_plain_email(self):
        """Plain email address extracts domain."""
        self.assertEqual(extract_domain("user@example.com"), "example.com")

    def test_display_name_format(self):
        """Display name format extracts domain."""
        self.assertEqual(extract_domain('"Newsletter" <news@substack.com>'), "substack.com")

    def test_subdomain_email(self):
        """Subdomain email returns full subdomain."""
        self.assertEqual(extract_domain("info@newsletter.example.com"), "newsletter.example.com")

    def test_uppercase_domain_is_lowercased(self):
        """Domain is returned in lowercase."""
        self.assertEqual(extract_domain("USER@EXAMPLE.COM"), "example.com")

    def test_empty_string_returns_none(self):
        """Empty string returns None."""
        self.assertIsNone(extract_domain(""))

    def test_none_returns_none(self):
        """None returns None."""
        self.assertIsNone(extract_domain(None))

    def test_no_at_sign_returns_none(self):
        """String without @ returns None."""
        self.assertIsNone(extract_domain("notanemail"))


@tagged("post_install", "-at_install")
class TestSanitizeEmailHtml(TransactionCase):
    """Tests for sanitize_email_html()."""

    def test_removes_script_tags(self):
        """Script tags are removed."""
        html = "<p>Hello</p><script>alert('xss')</script>"
        result = sanitize_email_html(html)
        self.assertNotIn("<script>", result)
        self.assertIn("Hello", result)

    def test_removes_style_tags(self):
        """Style tags are removed."""
        html = "<p>Content</p><style>body { color: red; }</style>"
        result = sanitize_email_html(html)
        self.assertNotIn("<style>", result)
        self.assertIn("Content", result)

    def test_removes_1x1_tracking_pixels(self):
        """1x1 tracking pixels are removed."""
        html = '<p>Content</p><img src="https://track.example.com/open.gif" width="1" height="1"/>'
        result = sanitize_email_html(html)
        self.assertNotIn('width="1"', result)
        self.assertIn("Content", result)

    def test_preserves_regular_images(self):
        """Regular content images are preserved."""
        html = '<p>Content</p><img src="https://example.com/photo.jpg" width="800" height="400"/>'
        result = sanitize_email_html(html)
        self.assertIn("photo.jpg", result)

    def test_empty_string(self):
        """Empty string returns empty string."""
        self.assertEqual(sanitize_email_html(""), "")

    def test_none_returns_empty(self):
        """None returns empty string."""
        self.assertEqual(sanitize_email_html(None), "")

    def test_preserves_content_text(self):
        """Regular text content is preserved."""
        html = "<p>Newsletter content here.</p><h2>Section Title</h2>"
        result = sanitize_email_html(html)
        self.assertIn("Newsletter content here", result)
        self.assertIn("Section Title", result)
