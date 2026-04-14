"""Tests for Pixabay fallback image integration."""
import base64
import json
from io import BytesIO
from unittest.mock import MagicMock, patch

from PIL import Image

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.queue_job.exception import RetryableJobError


def _create_test_image(width, height, format="JPEG"):
    """Create a test image with specified dimensions."""
    img = Image.new("RGB", (width, height), color="green")
    buffer = BytesIO()
    img.save(buffer, format=format)
    return buffer.getvalue()


def _make_mock_response(status_code=200, text="", json_data=None, content_type="text/html", content=None):
    """Create a mock HTTP response."""
    response = MagicMock()
    response.status_code = status_code
    response.text = text
    response.content = content if content is not None else (text.encode("utf-8") if isinstance(text, str) else text)
    response.headers = {"Content-Type": content_type}
    if json_data:
        response.json.return_value = json_data
    return response


@tagged("post_install", "-at_install")
class TestPixabayFallback(TransactionCase):
    """Test Pixabay fallback image functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, queue_job__no_delay=True))
        cls.source = cls.env["news.source"].create({
            "name": "Test Source",
            "url": "https://example.com/news",
        })
        cls.stage_new = cls.env.ref("newsassistant.news_article_stage_new")

        # Create a test blog
        cls.blog = cls.env["blog.blog"].create({
            "name": "Test Blog",
        })
        # Set the blog_id in config
        cls.env["ir.config_parameter"].sudo().set_param(
            "newsfeed.blog_id", str(cls.blog.id)
        )

    def _create_scraped_article(self, title="Test Article", with_header_image=False):
        """Helper to create a scraped article ready for digest processing."""
        vals = {
            "title": title,
            "source_id": self.source.id,
            "url": f"https://example.com/article/{title.lower().replace(' ', '-')}",
            "stage_id": self.stage_new.id,
            "state": "scraped",
            "summary": "Test summary for the article.",
            "content": "<p>Test content</p>",
        }
        if with_header_image:
            test_image = _create_test_image(1200, 600)
            vals["header_image"] = base64.b64encode(test_image).decode("utf-8")
            vals["header_image_filename"] = "test_header.jpg"
        return self.env["news.article"].create(vals)

    def test_pixabay_not_called_when_api_key_missing(self):
        """Test that Pixabay is not called when API key is not configured."""
        # Ensure no API key is set
        self.env["ir.config_parameter"].sudo().set_param("newsfeed.pixabay_api_key", "")

        article = self._create_scraped_article()

        with patch("odoo.addons.newsfeed.models.news_article.requests.get") as mock_get:
            # Call the internal method that uses Pixabay
            result = article._search_pixabay("test query")

            # Pixabay API should not be called
            mock_get.assert_not_called()
            # Should return empty list
            self.assertEqual(result, [])

    def test_pixabay_search_with_valid_api_key(self):
        """Test Pixabay search when API key is configured."""
        # Set a test API key
        self.env["ir.config_parameter"].sudo().set_param(
            "newsfeed.pixabay_api_key", "test-api-key-12345"
        )

        article = self._create_scraped_article()

        # Mock successful Pixabay response
        pixabay_response = {
            "hits": [
                {
                    "id": 12345,
                    "largeImageURL": "https://pixabay.com/get/12345_1280.jpg",
                    "webformatURL": "https://pixabay.com/get/12345_640.jpg",
                    "imageWidth": 1920,
                    "imageHeight": 1080,
                },
            ],
            "totalHits": 1,
        }

        with patch("odoo.addons.newsfeed.models.news_article.requests.get") as mock_get:
            mock_get.return_value = _make_mock_response(
                200, json_data=pixabay_response
            )

            result = article._search_pixabay("technology news")

            # Verify API was called with correct parameters
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            self.assertEqual(call_args.kwargs.get("timeout"), 15)
            params = call_args.kwargs.get("params", {})
            self.assertEqual(params["key"], "test-api-key-12345")
            self.assertEqual(params["q"], "technology news")
            self.assertEqual(params["image_type"], "photo")
            self.assertEqual(params["orientation"], "horizontal")

            # Should return the hits
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["id"], 12345)

    def test_pixabay_rate_limit_raises_retryable_error(self):
        """Test that Pixabay rate limit (429) raises RetryableJobError."""
        self.env["ir.config_parameter"].sudo().set_param(
            "newsfeed.pixabay_api_key", "test-api-key"
        )

        article = self._create_scraped_article()

        with patch("odoo.addons.newsfeed.models.news_article.requests.get") as mock_get:
            mock_get.return_value = _make_mock_response(429, text="Rate limit exceeded")

            with self.assertRaises(RetryableJobError) as context:
                article._search_pixabay("test query")

            self.assertIn("rate limit", str(context.exception).lower())

    def test_pixabay_timeout_raises_retryable_error(self):
        """Test that Pixabay timeout raises RetryableJobError."""
        import requests

        self.env["ir.config_parameter"].sudo().set_param(
            "newsfeed.pixabay_api_key", "test-api-key"
        )

        article = self._create_scraped_article()

        with patch("odoo.addons.newsfeed.models.news_article.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

            with self.assertRaises(RetryableJobError) as context:
                article._search_pixabay("test query")

            self.assertIn("timeout", str(context.exception).lower())

    def test_pixabay_other_errors_return_empty_list(self):
        """Test that non-transient Pixabay errors return empty list (no exception)."""
        self.env["ir.config_parameter"].sudo().set_param(
            "newsfeed.pixabay_api_key", "test-api-key"
        )

        article = self._create_scraped_article()

        with patch("odoo.addons.newsfeed.models.news_article.requests.get") as mock_get:
            # Use 400 Bad Request - a non-transient error that should return empty list
            mock_get.return_value = _make_mock_response(400, text="Bad Request")

            result = article._search_pixabay("test query")

            self.assertEqual(result, [])

    def test_download_pixabay_image_success(self):
        """Test successful download of Pixabay image."""
        self.env["ir.config_parameter"].sudo().set_param(
            "newsfeed.pixabay_api_key", "test-api-key"
        )

        article = self._create_scraped_article()
        test_image = _create_test_image(1920, 1080)

        hit = {
            "id": 12345,
            "largeImageURL": "https://pixabay.com/get/12345_1280.jpg",
            "webformatURL": "https://pixabay.com/get/12345_640.jpg",
        }

        with patch("odoo.addons.newsfeed.models.news_article.requests.get") as mock_get:
            mock_get.return_value = _make_mock_response(
                200, content=test_image, content_type="image/jpeg"
            )

            image_data, filename = article._download_pixabay_image(hit)

            self.assertEqual(image_data, test_image)
            self.assertEqual(filename, "pixabay_12345.jpg")

    def test_download_pixabay_image_failure(self):
        """Test handling of Pixabay image download failure."""
        article = self._create_scraped_article()

        hit = {
            "id": 12345,
            "largeImageURL": "https://pixabay.com/get/12345_1280.jpg",
        }

        with patch("odoo.addons.newsfeed.models.news_article.requests.get") as mock_get:
            mock_get.return_value = _make_mock_response(404)

            image_data, filename = article._download_pixabay_image(hit)

            self.assertIsNone(image_data)
            self.assertIsNone(filename)

    def test_get_header_image_uses_article_image_first(self):
        """Test that _get_header_image_for_blog uses article image when available."""
        # Create article with header image
        article = self._create_scraped_article(with_header_image=True)

        log_entries = []

        def add_entry(level, message, **kwargs):
            log_entries.append({"level": level, "message": message})

        with patch("odoo.addons.newsfeed.models.news_article.requests.get") as mock_get:
            image_data, filename, source = article._get_header_image_for_blog(add_entry)

            # Should not call Pixabay when article has image
            mock_get.assert_not_called()

            self.assertIsNotNone(image_data)
            self.assertEqual(filename, "test_header.jpg")
            self.assertEqual(source, "article")

            # Check log entry
            self.assertTrue(any("from article" in e["message"] for e in log_entries))

    def test_get_header_image_falls_back_to_pixabay(self):
        """Test that _get_header_image_for_blog falls back to Pixabay."""
        self.env["ir.config_parameter"].sudo().set_param(
            "newsfeed.pixabay_api_key", "test-api-key"
        )

        # Create article WITHOUT header image
        article = self._create_scraped_article(with_header_image=False)

        test_image = _create_test_image(1920, 1080)

        pixabay_response = {
            "hits": [
                {
                    "id": 99999,
                    "largeImageURL": "https://pixabay.com/get/99999_1280.jpg",
                    "imageWidth": 1920,
                    "imageHeight": 1080,
                },
            ],
        }

        log_entries = []

        def add_entry(level, message, **kwargs):
            log_entries.append({"level": level, "message": message})

        with patch("odoo.addons.newsfeed.models.news_article.requests.get") as mock_get:
            def mock_get_side_effect(url, **kwargs):
                if "pixabay.com/api" in url:
                    return _make_mock_response(200, json_data=pixabay_response)
                else:
                    # Image download
                    return _make_mock_response(200, content=test_image, content_type="image/jpeg")

            mock_get.side_effect = mock_get_side_effect

            image_data, filename, source = article._get_header_image_for_blog(add_entry)

            self.assertIsNotNone(image_data)
            self.assertEqual(filename, "pixabay_99999.jpg")
            self.assertEqual(source, "pixabay")

            # Check log entries
            self.assertTrue(any("Pixabay fallback" in e["message"] for e in log_entries))
            self.assertTrue(any("from Pixabay" in e["message"] for e in log_entries))

    def test_get_header_image_returns_none_when_no_image_available(self):
        """Test _get_header_image_for_blog returns None when no image is available."""
        # No API key = no Pixabay fallback
        self.env["ir.config_parameter"].sudo().set_param("newsfeed.pixabay_api_key", "")

        # Article without header image
        article = self._create_scraped_article(with_header_image=False)

        log_entries = []

        def add_entry(level, message, **kwargs):
            log_entries.append({"level": level, "message": message})

        image_data, filename, source = article._get_header_image_for_blog(add_entry)

        self.assertIsNone(image_data)
        self.assertIsNone(filename)
        self.assertIsNone(source)

        # Should log warning about no image
        self.assertTrue(any("no suitable image found" in e["message"].lower() for e in log_entries))

    def test_pixabay_warning_logged_when_api_key_missing(self):
        """Test that a warning is logged when Pixabay API key is not configured."""
        self.env["ir.config_parameter"].sudo().set_param("newsfeed.pixabay_api_key", "")

        article = self._create_scraped_article(with_header_image=False)

        log_entries = []

        def add_entry(level, message, **kwargs):
            log_entries.append({"level": level, "message": message})

        image_data, filename, source = article._get_header_image_for_blog(add_entry)

        # Should return no image
        self.assertIsNone(source)

        # Log should mention the fallback attempt and failure
        self.assertTrue(any("Pixabay fallback" in e["message"] for e in log_entries))


@tagged("post_install", "-at_install")
class TestPixabayApiKeyConfiguration(TransactionCase):
    """Test Pixabay API key configuration via system parameters."""

    def test_get_pixabay_api_key_when_not_set(self):
        """Test _get_pixabay_api_key returns None when not configured."""
        self.env["ir.config_parameter"].sudo().set_param("newsfeed.pixabay_api_key", "")

        article = self.env["news.article"].create({
            "title": "Test",
            "source_id": self.env["news.source"].create({
                "name": "Test",
                "url": "https://example.com",
            }).id,
            "url": "https://example.com/test",
            "stage_id": self.env.ref("newsassistant.news_article_stage_new").id,
        })

        api_key = article._get_pixabay_api_key()
        self.assertIsNone(api_key)

    def test_get_pixabay_api_key_when_set(self):
        """Test _get_pixabay_api_key returns the configured key."""
        self.env["ir.config_parameter"].sudo().set_param(
            "newsfeed.pixabay_api_key", "my-secret-api-key"
        )

        article = self.env["news.article"].create({
            "title": "Test",
            "source_id": self.env["news.source"].create({
                "name": "Test",
                "url": "https://example.com",
            }).id,
            "url": "https://example.com/test",
            "stage_id": self.env.ref("newsassistant.news_article_stage_new").id,
        })

        api_key = article._get_pixabay_api_key()
        self.assertEqual(api_key, "my-secret-api-key")

    def test_get_pixabay_api_key_strips_whitespace(self):
        """Test _get_pixabay_api_key strips whitespace from the key."""
        self.env["ir.config_parameter"].sudo().set_param(
            "newsfeed.pixabay_api_key", "  my-api-key  "
        )

        article = self.env["news.article"].create({
            "title": "Test",
            "source_id": self.env["news.source"].create({
                "name": "Test",
                "url": "https://example.com",
            }).id,
            "url": "https://example.com/test",
            "stage_id": self.env.ref("newsassistant.news_article_stage_new").id,
        })

        api_key = article._get_pixabay_api_key()
        self.assertEqual(api_key, "my-api-key")
