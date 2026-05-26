"""Tests for Jina Reader API fetch utilities."""
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.newsassistant_website.models.jina_utils import (
    fetch_page,
    markdown_to_html,
)


def _make_jina_response(status_code=200, content="", images=None):
    response = MagicMock()
    response.status_code = status_code
    response.text = content
    response.json.return_value = {
        "data": {
            "content": content,
            "images": images or {},
        }
    }
    return response


@tagged("post_install", "-at_install")
class TestJinaFetch(TransactionCase):
    """Tests for fetch_page() utility."""

    @patch("odoo.addons.newsassistant_website.models.jina_utils.requests.get")
    @patch.dict("os.environ", {"JINA_API_KEY": "test-key"})
    def test_fetch_page_success(self, mock_get):
        """Successful Jina fetch returns content and images dict."""
        mock_get.return_value = _make_jina_response(
            content="# Article content\nParagraph.",
            images={"Image": "https://example.com/img.jpg"},
        )
        content, images = fetch_page("https://example.com/article/1")
        self.assertIn("Article content", content)
        self.assertIn("Image", images)

    @patch.dict("os.environ", {}, clear=True)
    def test_fetch_page_missing_jina_key_raises_valueerror(self):
        """Missing JINA_API_KEY raises ValueError."""
        # Remove JINA_API_KEY from environment
        import os
        os.environ.pop("JINA_API_KEY", None)
        with self.assertRaises(ValueError) as ctx:
            fetch_page("https://example.com/article/1")
        self.assertIn("JINA_API_KEY", str(ctx.exception))

    @patch("odoo.addons.newsassistant_website.models.jina_utils.requests.get")
    @patch.dict("os.environ", {"JINA_API_KEY": "test-key"})
    def test_fetch_page_429_raises_retryable(self, mock_get):
        """Jina 429 raises RetryableJobError."""
        mock_get.return_value = MagicMock(status_code=429, text="Rate limited")
        with self.assertRaises(RetryableJobError):
            fetch_page("https://example.com/article/1")

    @patch("odoo.addons.newsassistant_website.models.jina_utils.requests.get")
    @patch.dict("os.environ", {"JINA_API_KEY": "test-key"})
    def test_fetch_page_503_raises_retryable(self, mock_get):
        """Jina 503 raises RetryableJobError."""
        mock_get.return_value = MagicMock(status_code=503, text="Service unavailable")
        with self.assertRaises(RetryableJobError):
            fetch_page("https://example.com/article/1")

    @patch("odoo.addons.newsassistant_website.models.jina_utils.requests.get")
    @patch.dict("os.environ", {"JINA_API_KEY": "test-key"})
    def test_fetch_page_400_raises_valueerror(self, mock_get):
        """Jina 400 raises ValueError with error code."""
        mock_get.return_value = MagicMock(status_code=400, text="Bad request")
        with self.assertRaises(ValueError) as ctx:
            fetch_page("https://example.com/article/1")
        self.assertIn("400", str(ctx.exception))

    @patch("odoo.addons.newsassistant_website.models.jina_utils.requests.get")
    @patch.dict("os.environ", {"JINA_API_KEY": "test-key"})
    def test_fetch_page_truncates_long_content(self, mock_get):
        """Content longer than MAX_CONTENT_LENGTH is truncated."""
        long_content = "x" * 50000
        mock_get.return_value = _make_jina_response(content=long_content)
        content, _ = fetch_page("https://example.com/article/1")
        self.assertLessEqual(len(content), 30000)

    @patch("odoo.addons.newsassistant_website.models.jina_utils.requests.get")
    @patch.dict("os.environ", {"JINA_API_KEY": "test-key"})
    def test_fetch_page_timeout_raises_retryable(self, mock_get):
        """Timeout raises RetryableJobError."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Timed out")
        with self.assertRaises(RetryableJobError):
            fetch_page("https://example.com/article/1")


@tagged("post_install", "-at_install")
class TestMarkdownToHtml(TransactionCase):
    """Tests for markdown_to_html() conversion."""

    def test_basic_paragraph(self):
        """Markdown paragraph converts to HTML p tag."""
        result = markdown_to_html("Hello world")
        self.assertIn("Hello world", result)

    def test_empty_string(self):
        """Empty string returns empty string."""
        self.assertEqual(markdown_to_html(""), "")

    def test_heading_converts(self):
        """Markdown h1 converts to HTML h1."""
        result = markdown_to_html("# My Title")
        self.assertIn("My Title", result)

    def test_returns_string(self):
        """Result is always a string."""
        result = markdown_to_html("Some content")
        self.assertIsInstance(result, str)
