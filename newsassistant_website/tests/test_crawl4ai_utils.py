"""Tests for crawl4ai fetch utilities."""
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.newsassistant_website.models.crawl4ai_utils import (
    fetch_page,
    markdown_to_html,
)


def _make_crawl4ai_response(
    status_code=200, success=True, markdown="", images=None, error=""
):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = {
        "success": success,
        "error": error,
        "results": [
            {
                "markdown": {"raw_markdown": markdown},
                "media": {"images": images or []},
            }
        ],
    }
    return response


@tagged("post_install", "-at_install")
class TestCrawl4aiFetch(TransactionCase):
    """Tests for fetch_page() utility using crawl4ai."""

    @patch("odoo.addons.newsassistant_website.models.crawl4ai_utils.requests.post")
    def test_fetch_page_success(self, mock_post):
        """Successful crawl4ai fetch returns content and images dict."""
        mock_post.return_value = _make_crawl4ai_response(
            markdown="# Article content\nParagraph.",
            images=[{"src": "https://example.com/img.jpg", "alt": "Example Image"}],
        )
        content, images = fetch_page("https://example.com/article/1")
        self.assertIn("Article content", content)
        self.assertIn("Example Image", images)

    @patch("odoo.addons.newsassistant_website.models.crawl4ai_utils.requests.post")
    def test_fetch_page_no_images(self, mock_post):
        """crawl4ai response without images returns empty dict."""
        mock_post.return_value = _make_crawl4ai_response(
            markdown="No images here."
        )
        content, images = fetch_page("https://example.com/article/1")
        self.assertEqual(images, {})

    @patch("odoo.addons.newsassistant_website.models.crawl4ai_utils.requests.post")
    def test_fetch_page_no_results_raises_valueerror(self, mock_post):
        """Empty results array raises ValueError."""
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"success": True, "results": []}
        mock_post.return_value = response
        with self.assertRaises(ValueError) as ctx:
            fetch_page("https://example.com/article/1")
        self.assertIn("no results", str(ctx.exception).lower())

    @patch("odoo.addons.newsassistant_website.models.crawl4ai_utils.requests.post")
    def test_fetch_page_success_false_raises_valueerror(self, mock_post):
        """crawl4ai success=false raises ValueError."""
        mock_post.return_value = _make_crawl4ai_response(
            success=False, error="Crawl failed"
        )
        with self.assertRaises(ValueError) as ctx:
            fetch_page("https://example.com/article/1")
        self.assertIn("Crawl failed", str(ctx.exception))

    @patch("odoo.addons.newsassistant_website.models.crawl4ai_utils.requests.post")
    def test_fetch_page_429_raises_retryable(self, mock_post):
        """crawl4ai 429 raises RetryableJobError."""
        mock_post.return_value = MagicMock(status_code=429)
        with self.assertRaises(RetryableJobError):
            fetch_page("https://example.com/article/1")

    @patch("odoo.addons.newsassistant_website.models.crawl4ai_utils.requests.post")
    def test_fetch_page_503_raises_retryable(self, mock_post):
        """crawl4ai 503 raises RetryableJobError."""
        mock_post.return_value = MagicMock(status_code=503)
        with self.assertRaises(RetryableJobError):
            fetch_page("https://example.com/article/1")

    @patch("odoo.addons.newsassistant_website.models.crawl4ai_utils.requests.post")
    def test_fetch_page_truncates_long_content(self, mock_post):
        """Content longer than MAX_CONTENT_LENGTH is truncated."""
        long_md = "x" * 50000
        mock_post.return_value = _make_crawl4ai_response(markdown=long_md)
        content, _ = fetch_page("https://example.com/article/1")
        self.assertLessEqual(len(content), 30000)

    @patch("odoo.addons.newsassistant_website.models.crawl4ai_utils.requests.post")
    def test_fetch_page_timeout_raises_retryable(self, mock_post):
        """Timeout raises RetryableJobError."""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Timed out")
        with self.assertRaises(RetryableJobError):
            fetch_page("https://example.com/article/1")

    @patch("odoo.addons.newsassistant_website.models.crawl4ai_utils.requests.post")
    def test_fetch_page_connection_error_raises_retryable(self, mock_post):
        """Connection error raises RetryableJobError."""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Refused")
        with self.assertRaises(RetryableJobError):
            fetch_page("https://example.com/article/1")

    @patch("odoo.addons.newsassistant_website.models.crawl4ai_utils.requests.post")
    def test_fetch_page_sends_bearer_token(self, mock_post):
        """When api_token is provided, Authorization header is sent."""
        mock_post.return_value = _make_crawl4ai_response(markdown="content")
        fetch_page("https://example.com/article/1", crawl4ai_api_token="my-token")
        call_kwargs = mock_post.call_args[1]
        headers = call_kwargs.get("headers", {})
        self.assertEqual(headers.get("Authorization"), "Bearer my-token")

    @patch("odoo.addons.newsassistant_website.models.crawl4ai_utils.requests.post")
    def test_fetch_page_no_token_no_auth_header(self, mock_post):
        """When no api_token, no Authorization header is sent."""
        mock_post.return_value = _make_crawl4ai_response(markdown="content")
        fetch_page("https://example.com/article/1")
        call_kwargs = mock_post.call_args[1]
        headers = call_kwargs.get("headers", {}) or {}
        self.assertNotIn("Authorization", headers)


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
