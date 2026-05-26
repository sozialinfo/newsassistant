"""Tests for image selection and validation utilities."""
from io import BytesIO
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.newsassistant_website.models.image_utils import (
    select_header_image,
    should_skip_image_url,
    validate_and_download_image,
)


def _create_test_image_bytes(width, height, fmt="JPEG"):
    """Create test image bytes for given dimensions."""
    from PIL import Image
    img = Image.new("RGB", (width, height), color="blue")
    buf = BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def _make_mock_response(status_code=200, content=None, content_type="image/jpeg"):
    response = MagicMock()
    response.status_code = status_code
    response.content = content or b""
    response.headers = {"Content-Type": content_type}
    return response


@tagged("post_install", "-at_install")
class TestShouldSkipImageUrl(TransactionCase):
    """Tests for should_skip_image_url()."""

    def test_skips_logo_url(self):
        self.assertTrue(should_skip_image_url("https://example.com/company-logo.png"))

    def test_skips_icon_url(self):
        self.assertTrue(should_skip_image_url("https://example.com/icon-share.svg"))

    def test_skips_svg_extension(self):
        self.assertTrue(should_skip_image_url("https://example.com/graphic.svg"))

    def test_skips_footer_url(self):
        self.assertTrue(should_skip_image_url("https://example.com/footer-badge.png"))

    def test_skips_avatar_url(self):
        self.assertTrue(should_skip_image_url("https://example.com/user-avatar.jpg"))

    def test_allows_regular_image(self):
        self.assertFalse(should_skip_image_url("https://example.com/news/header.jpg"))

    def test_allows_article_photo(self):
        self.assertFalse(should_skip_image_url("https://example.com/photos/2025/article-photo.jpg"))


@tagged("post_install", "-at_install")
class TestValidateAndDownloadImage(TransactionCase):
    """Tests for validate_and_download_image()."""

    @patch("odoo.addons.newsassistant_website.models.image_utils.requests.get")
    def test_accepts_valid_landscape_jpeg(self, mock_get):
        """Valid landscape JPEG at minimum size (800x400) is accepted."""
        img_bytes = _create_test_image_bytes(800, 400)
        mock_get.return_value = _make_mock_response(content=img_bytes)
        data, filename = validate_and_download_image("https://example.com/img.jpg")
        self.assertIsNotNone(data)
        self.assertIsNotNone(filename)

    @patch("odoo.addons.newsassistant_website.models.image_utils.requests.get")
    def test_accepts_900x600_image(self, mock_get):
        """Image at 900x600 (previously rejected at 1000px threshold) is now accepted."""
        img_bytes = _create_test_image_bytes(900, 600)
        mock_get.return_value = _make_mock_response(content=img_bytes)
        data, filename = validate_and_download_image("https://example.com/img.jpg")
        self.assertIsNotNone(data)
        self.assertIsNotNone(filename)

    @patch("odoo.addons.newsassistant_website.models.image_utils.requests.get")
    def test_rejects_small_image(self, mock_get):
        """Image smaller than 800px wide is rejected."""
        img_bytes = _create_test_image_bytes(700, 400)
        mock_get.return_value = _make_mock_response(content=img_bytes)
        data, filename = validate_and_download_image("https://example.com/img.jpg")
        self.assertIsNone(data)
        self.assertIsNone(filename)

    @patch("odoo.addons.newsassistant_website.models.image_utils.requests.get")
    def test_rejects_portrait_image(self, mock_get):
        """Portrait image (height > width) is rejected."""
        img_bytes = _create_test_image_bytes(800, 1200)
        mock_get.return_value = _make_mock_response(content=img_bytes)
        data, filename = validate_and_download_image("https://example.com/img.jpg")
        self.assertIsNone(data)

    @patch("odoo.addons.newsassistant_website.models.image_utils.requests.get")
    def test_rejects_gif_format(self, mock_get):
        """GIF format is rejected."""
        img_bytes = _create_test_image_bytes(1200, 600, fmt="GIF")
        mock_get.return_value = _make_mock_response(content=img_bytes, content_type="image/gif")
        data, filename = validate_and_download_image("https://example.com/img.gif")
        self.assertIsNone(data)

    @patch("odoo.addons.newsassistant_website.models.image_utils.requests.get")
    def test_rejects_404_response(self, mock_get):
        """HTTP 404 returns None."""
        mock_get.return_value = _make_mock_response(status_code=404)
        data, filename = validate_and_download_image("https://example.com/img.jpg")
        self.assertIsNone(data)

    @patch("odoo.addons.newsassistant_website.models.image_utils.requests.get")
    def test_handles_timeout_gracefully(self, mock_get):
        """Timeout returns None without raising."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Timed out")
        data, filename = validate_and_download_image("https://example.com/img.jpg")
        self.assertIsNone(data)
        self.assertIsNone(filename)


@tagged("post_install", "-at_install")
class TestSelectHeaderImage(TransactionCase):
    """Tests for select_header_image()."""

    def test_returns_none_for_empty_dict(self):
        """Empty images dict returns None, None."""
        data, filename = select_header_image({})
        self.assertIsNone(data)
        self.assertIsNone(filename)

    @patch("odoo.addons.newsassistant_website.models.image_utils.requests.get")
    def test_selects_first_valid_image(self, mock_get):
        """First valid image is returned."""
        img_bytes = _create_test_image_bytes(1200, 600)
        mock_get.return_value = _make_mock_response(content=img_bytes)
        images = {"Main": "https://example.com/main.jpg"}
        data, filename = select_header_image(images)
        self.assertIsNotNone(data)
        self.assertEqual(filename, "main.jpg")

    @patch("odoo.addons.newsassistant_website.models.image_utils.requests.get")
    def test_skips_logo_and_selects_next(self, mock_get):
        """Logo URL is skipped; next valid image is returned."""
        img_bytes = _create_test_image_bytes(1200, 600)
        mock_get.return_value = _make_mock_response(content=img_bytes)
        images = {
            "Logo": "https://example.com/logo.png",
            "Main": "https://example.com/main.jpg",
        }
        data, filename = select_header_image(images)
        self.assertIsNotNone(data)
        self.assertEqual(filename, "main.jpg")

    def test_returns_none_when_all_logos(self):
        """When all images are logos/icons, returns None."""
        images = {
            "Logo": "https://example.com/logo.png",
            "Icon": "https://example.com/icon.svg",
        }
        data, filename = select_header_image(images)
        self.assertIsNone(data)
        self.assertIsNone(filename)
