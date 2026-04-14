"""Tests for header image extraction during article scraping."""
import base64
import json
from io import BytesIO
from unittest.mock import MagicMock, patch

from PIL import Image

from odoo.tests.common import TransactionCase, tagged


def _create_test_image(width, height, format="JPEG"):
    """Create a test image with specified dimensions."""
    img = Image.new("RGB", (width, height), color="blue")
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


def _make_ai_response(content):
    """Create a mock AI API response with usage data."""
    return {
        "choices": [{"message": {"content": content}}],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        },
    }


ARTICLE_MARKDOWN = """
# Test Article Title

Published: 2025-03-15

This is the article content with important information.
"""

AI_ARTICLE_RESPONSE = json.dumps({
    "is_article": True,
    "title": "Test Article Title",
    "date": "2025-03-15",
    "summary": "This article covers important topics.",
    "content": "<p>This is the article content with important information.</p>",
})


@tagged("post_install", "-at_install")
class TestHeaderImageExtraction(TransactionCase):
    """Test header image extraction during article scraping."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, queue_job__no_delay=True))
        cls.source = cls.env["news.source"].create({
            "name": "Test Source",
            "url": "https://example.com/news",
        })
        cls.stage_new = cls.env.ref("newsassistant.news_article_stage_new")

    def _create_article(self, url="https://example.com/article/1"):
        """Helper to create a test article."""
        return self.env["news.article"].create({
            "title": "Placeholder Title",
            "source_id": self.source.id,
            "url": url,
            "stage_id": self.stage_new.id,
        })

    @patch("odoo.addons.newsassistant.models.news_source.requests.get")
    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_extracts_header_image_from_suitable_candidate(self, mock_fetch, mock_post, mock_get):
        """Test that a suitable header image is extracted and stored on the article."""
        # Create a valid landscape image (1200x600)
        test_image = _create_test_image(1200, 600)

        # Mock the Jina fetch to return article with images
        mock_fetch.return_value = (ARTICLE_MARKDOWN, {
            "Main Image": "https://example.com/images/header.jpg",
        })

        # Mock AI response
        ai_response_data = _make_ai_response(AI_ARTICLE_RESPONSE)
        mock_post.return_value = _make_mock_response(200, json_data=ai_response_data)

        # Mock image download
        mock_get.return_value = _make_mock_response(
            200,
            content=test_image,
            content_type="image/jpeg",
        )

        article = self._create_article()
        article._fetch_and_extract()

        # Verify article state
        self.assertEqual(article.state, "scraped")
        self.assertEqual(article.title, "Test Article Title")

        # Verify header image was stored
        self.assertTrue(article.header_image, "Header image should be stored")
        self.assertEqual(article.header_image_filename, "header.jpg")

        # Verify the stored image data is valid
        stored_image = base64.b64decode(article.header_image)
        self.assertEqual(stored_image, test_image)

    @patch("odoo.addons.newsassistant.models.news_source.requests.get")
    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_skips_images_too_small(self, mock_fetch, mock_post, mock_get):
        """Test that images smaller than 1000x400 are rejected."""
        # Create a small image (500x300)
        small_image = _create_test_image(500, 300)

        mock_fetch.return_value = (ARTICLE_MARKDOWN, {
            "Small Image": "https://example.com/images/small.jpg",
        })

        ai_response_data = _make_ai_response(AI_ARTICLE_RESPONSE)
        mock_post.return_value = _make_mock_response(200, json_data=ai_response_data)

        mock_get.return_value = _make_mock_response(
            200,
            content=small_image,
            content_type="image/jpeg",
        )

        article = self._create_article()
        article._fetch_and_extract()

        # Article should still be scraped successfully
        self.assertEqual(article.state, "scraped")
        # But no header image should be stored
        self.assertFalse(article.header_image, "Small image should be rejected")
        self.assertFalse(article.header_image_filename)

    @patch("odoo.addons.newsassistant.models.news_source.requests.get")
    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_skips_portrait_images(self, mock_fetch, mock_post, mock_get):
        """Test that portrait images (height > width) are rejected."""
        # Create a portrait image (800x1200)
        portrait_image = _create_test_image(800, 1200)

        mock_fetch.return_value = (ARTICLE_MARKDOWN, {
            "Portrait Image": "https://example.com/images/portrait.jpg",
        })

        ai_response_data = _make_ai_response(AI_ARTICLE_RESPONSE)
        mock_post.return_value = _make_mock_response(200, json_data=ai_response_data)

        mock_get.return_value = _make_mock_response(
            200,
            content=portrait_image,
            content_type="image/jpeg",
        )

        article = self._create_article()
        article._fetch_and_extract()

        self.assertEqual(article.state, "scraped")
        self.assertFalse(article.header_image, "Portrait image should be rejected")

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_skips_logo_urls(self, mock_fetch, mock_post):
        """Test that URLs containing 'logo', 'icon', etc. are skipped without download."""
        mock_fetch.return_value = (ARTICLE_MARKDOWN, {
            "Logo": "https://example.com/images/company-logo.png",
            "Icon": "https://example.com/assets/icon-share.svg",
            "Footer Image": "https://example.com/footer-badge.png",
        })

        ai_response_data = _make_ai_response(AI_ARTICLE_RESPONSE)
        mock_post.return_value = _make_mock_response(200, json_data=ai_response_data)

        article = self._create_article()

        # Patch requests.get to track if it's called
        with patch("odoo.addons.newsassistant.models.news_source.requests.get") as mock_get:
            article._fetch_and_extract()
            # No image downloads should be attempted for logo/icon URLs
            mock_get.assert_not_called()

        self.assertEqual(article.state, "scraped")
        self.assertFalse(article.header_image, "Logo/icon images should be skipped")

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_skips_svg_extensions(self, mock_fetch, mock_post):
        """Test that .svg URLs are skipped without download."""
        mock_fetch.return_value = (ARTICLE_MARKDOWN, {
            "Vector Image": "https://example.com/images/graphic.svg",
        })

        ai_response_data = _make_ai_response(AI_ARTICLE_RESPONSE)
        mock_post.return_value = _make_mock_response(200, json_data=ai_response_data)

        article = self._create_article()

        with patch("odoo.addons.newsassistant.models.news_source.requests.get") as mock_get:
            article._fetch_and_extract()
            mock_get.assert_not_called()

        self.assertEqual(article.state, "scraped")
        self.assertFalse(article.header_image)

    @patch("odoo.addons.newsassistant.models.news_source.requests.get")
    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_selects_first_valid_image(self, mock_fetch, mock_post, mock_get):
        """Test that the first valid image is selected when multiple exist."""
        small_image = _create_test_image(500, 300)
        valid_image = _create_test_image(1200, 600)

        mock_fetch.return_value = (ARTICLE_MARKDOWN, {
            "Logo": "https://example.com/logo.png",
            "Small": "https://example.com/small.jpg",
            "Valid": "https://example.com/valid.jpg",
            "Another Valid": "https://example.com/another.jpg",
        })

        ai_response_data = _make_ai_response(AI_ARTICLE_RESPONSE)
        mock_post.return_value = _make_mock_response(200, json_data=ai_response_data)

        def mock_get_side_effect(url, **kwargs):
            if "small" in url:
                return _make_mock_response(200, content=small_image, content_type="image/jpeg")
            elif "valid" in url or "another" in url:
                return _make_mock_response(200, content=valid_image, content_type="image/jpeg")
            return _make_mock_response(404)

        mock_get.side_effect = mock_get_side_effect

        article = self._create_article()
        article._fetch_and_extract()

        self.assertEqual(article.state, "scraped")
        self.assertTrue(article.header_image, "First valid image should be selected")
        # The valid.jpg should be selected (first valid after logo is skipped and small is rejected)
        self.assertEqual(article.header_image_filename, "valid.jpg")

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_handles_no_images_gracefully(self, mock_fetch, mock_post):
        """Test that article extraction succeeds when no images are available."""
        mock_fetch.return_value = (ARTICLE_MARKDOWN, {})

        ai_response_data = _make_ai_response(AI_ARTICLE_RESPONSE)
        mock_post.return_value = _make_mock_response(200, json_data=ai_response_data)

        article = self._create_article()
        article._fetch_and_extract()

        self.assertEqual(article.state, "scraped")
        self.assertEqual(article.title, "Test Article Title")
        self.assertFalse(article.header_image)
        self.assertFalse(article.header_image_filename)

    @patch("odoo.addons.newsassistant.models.news_source.requests.get")
    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_handles_all_images_failing_validation(self, mock_fetch, mock_post, mock_get):
        """Test graceful handling when all image candidates fail validation."""
        small_image = _create_test_image(400, 200)

        mock_fetch.return_value = (ARTICLE_MARKDOWN, {
            "Image1": "https://example.com/img1.jpg",
            "Image2": "https://example.com/img2.jpg",
        })

        ai_response_data = _make_ai_response(AI_ARTICLE_RESPONSE)
        mock_post.return_value = _make_mock_response(200, json_data=ai_response_data)

        # All images are too small
        mock_get.return_value = _make_mock_response(
            200,
            content=small_image,
            content_type="image/jpeg",
        )

        article = self._create_article()
        article._fetch_and_extract()

        # Article extraction should still succeed
        self.assertEqual(article.state, "scraped")
        self.assertEqual(article.title, "Test Article Title")
        # No header image since all failed validation
        self.assertFalse(article.header_image)

    @patch("odoo.addons.newsassistant.models.news_source.requests.get")
    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_handles_image_download_failure(self, mock_fetch, mock_post, mock_get):
        """Test graceful handling when image download fails."""
        mock_fetch.return_value = (ARTICLE_MARKDOWN, {
            "Image": "https://example.com/image.jpg",
        })

        ai_response_data = _make_ai_response(AI_ARTICLE_RESPONSE)
        mock_post.return_value = _make_mock_response(200, json_data=ai_response_data)

        # Image download returns 404
        mock_get.return_value = _make_mock_response(404)

        article = self._create_article()
        article._fetch_and_extract()

        self.assertEqual(article.state, "scraped")
        self.assertFalse(article.header_image)

    @patch("odoo.addons.newsassistant.models.news_source.requests.get")
    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_handles_image_download_timeout(self, mock_fetch, mock_post, mock_get):
        """Test graceful handling when image download times out."""
        import requests

        mock_fetch.return_value = (ARTICLE_MARKDOWN, {
            "Image": "https://example.com/image.jpg",
        })

        ai_response_data = _make_ai_response(AI_ARTICLE_RESPONSE)
        mock_post.return_value = _make_mock_response(200, json_data=ai_response_data)

        # Image download times out
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

        article = self._create_article()
        article._fetch_and_extract()

        # Article should still be scraped successfully
        self.assertEqual(article.state, "scraped")
        self.assertFalse(article.header_image)

    @patch("odoo.addons.newsassistant.models.news_source.requests.get")
    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_rejects_unsupported_image_formats(self, mock_fetch, mock_post, mock_get):
        """Test that GIF and other unsupported formats are rejected."""
        # Create a GIF image
        gif_image = _create_test_image(1200, 600, format="GIF")

        mock_fetch.return_value = (ARTICLE_MARKDOWN, {
            "Animation": "https://example.com/animation.gif",
        })

        ai_response_data = _make_ai_response(AI_ARTICLE_RESPONSE)
        mock_post.return_value = _make_mock_response(200, json_data=ai_response_data)

        mock_get.return_value = _make_mock_response(
            200,
            content=gif_image,
            content_type="image/gif",
        )

        article = self._create_article()
        article._fetch_and_extract()

        self.assertEqual(article.state, "scraped")
        self.assertFalse(article.header_image, "GIF format should be rejected")

    @patch("odoo.addons.newsassistant.models.news_source.requests.get")
    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_accepts_png_format(self, mock_fetch, mock_post, mock_get):
        """Test that PNG images are accepted."""
        png_image = _create_test_image(1200, 600, format="PNG")

        mock_fetch.return_value = (ARTICLE_MARKDOWN, {
            "PNG Image": "https://example.com/image.png",
        })

        ai_response_data = _make_ai_response(AI_ARTICLE_RESPONSE)
        mock_post.return_value = _make_mock_response(200, json_data=ai_response_data)

        mock_get.return_value = _make_mock_response(
            200,
            content=png_image,
            content_type="image/png",
        )

        article = self._create_article()
        article._fetch_and_extract()

        self.assertEqual(article.state, "scraped")
        self.assertTrue(article.header_image, "PNG format should be accepted")
        self.assertEqual(article.header_image_filename, "image.png")

    @patch("odoo.addons.newsassistant.models.news_source.requests.get")
    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_accepts_webp_format(self, mock_fetch, mock_post, mock_get):
        """Test that WebP images are accepted."""
        # Check if WebP is supported by PIL
        try:
            webp_image = _create_test_image(1200, 600, format="WEBP")
        except KeyError:
            # WebP not available in this PIL installation, skip test
            self.skipTest("WebP format not supported by PIL in this environment")
            return

        mock_fetch.return_value = (ARTICLE_MARKDOWN, {
            "WebP Image": "https://example.com/image.webp",
        })

        ai_response_data = _make_ai_response(AI_ARTICLE_RESPONSE)
        mock_post.return_value = _make_mock_response(200, json_data=ai_response_data)

        mock_get.return_value = _make_mock_response(
            200,
            content=webp_image,
            content_type="image/webp",
        )

        article = self._create_article()
        article._fetch_and_extract()

        self.assertEqual(article.state, "scraped")
        self.assertTrue(article.header_image, "WebP format should be accepted")
        self.assertEqual(article.header_image_filename, "image.webp")

    @patch("odoo.addons.newsassistant.models.news_source.requests.get")
    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_image_at_exact_minimum_dimensions(self, mock_fetch, mock_post, mock_get):
        """Test that images at exactly 1000x400 are accepted."""
        exact_image = _create_test_image(1000, 400)

        mock_fetch.return_value = (ARTICLE_MARKDOWN, {
            "Exact Size": "https://example.com/exact.jpg",
        })

        ai_response_data = _make_ai_response(AI_ARTICLE_RESPONSE)
        mock_post.return_value = _make_mock_response(200, json_data=ai_response_data)

        mock_get.return_value = _make_mock_response(
            200,
            content=exact_image,
            content_type="image/jpeg",
        )

        article = self._create_article()
        article._fetch_and_extract()

        self.assertEqual(article.state, "scraped")
        self.assertTrue(article.header_image, "Image at exact minimum dimensions should be accepted")
