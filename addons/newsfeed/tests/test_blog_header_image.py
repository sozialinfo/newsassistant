"""Tests for blog post header image display and attachment."""
import base64
import json
from io import BytesIO
from unittest.mock import MagicMock, patch

from PIL import Image

from odoo.tests.common import TransactionCase, tagged


def _create_test_image(width, height, format="JPEG"):
    """Create a test image with specified dimensions."""
    img = Image.new("RGB", (width, height), color="red")
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


@tagged("post_install", "-at_install")
class TestBlogPostHeaderImage(TransactionCase):
    """Test blog post header image attachment and display."""

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
        """Helper to create a scraped article ready for blog post creation."""
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
            vals["header_image_filename"] = "article_header.jpg"
        return self.env["news.article"].create(vals)

    def test_blog_post_created_with_article_header_image(self):
        """Test that blog post is created with article's header image attached."""
        article = self._create_scraped_article(with_header_image=True)

        log_entries = []

        def add_entry(level, message, **kwargs):
            log_entries.append({"level": level, "message": message, **kwargs})

        # Create blog post
        blog_post = article._create_blog_post(
            teaser="This is a test teaser.",
            log_entries=log_entries,
            add_entry=add_entry,
        )

        self.assertIsNotNone(blog_post)
        self.assertEqual(blog_post.name, article.title)
        self.assertEqual(blog_post.blog_id, self.blog)
        self.assertTrue(blog_post.is_published)

        # Verify cover_properties is set
        self.assertTrue(blog_post.cover_properties)
        cover_props = json.loads(blog_post.cover_properties)
        self.assertIn("background-image", cover_props)
        self.assertIn("url(/web/image/", cover_props["background-image"])

        # Verify attachment was created
        attachment = self.env["ir.attachment"].search([
            ("res_model", "=", "blog.post"),
            ("res_id", "=", blog_post.id),
        ])
        self.assertEqual(len(attachment), 1)
        self.assertEqual(attachment.name, "article_header.jpg")
        self.assertEqual(attachment.mimetype, "image/jpeg")

    def test_blog_post_cover_properties_format(self):
        """Test that cover_properties JSON has correct format."""
        article = self._create_scraped_article(with_header_image=True)

        log_entries = []

        def add_entry(level, message, **kwargs):
            log_entries.append({"level": level, "message": message, **kwargs})

        blog_post = article._create_blog_post(
            teaser="Test teaser",
            log_entries=log_entries,
            add_entry=add_entry,
        )

        cover_props = json.loads(blog_post.cover_properties)

        # Verify all required properties
        self.assertIn("background-image", cover_props)
        self.assertIn("background_color_class", cover_props)
        self.assertIn("opacity", cover_props)
        self.assertIn("resize_class", cover_props)

        # Check specific values
        self.assertEqual(cover_props["background_color_class"], "o_cc3")
        self.assertEqual(cover_props["opacity"], "0.4")
        self.assertEqual(cover_props["resize_class"], "o_half_screen_height")

    def test_blog_post_created_with_pixabay_fallback(self):
        """Test that blog post uses Pixabay image when article has no header."""
        # Set Pixabay API key
        self.env["ir.config_parameter"].sudo().set_param(
            "newsfeed.pixabay_api_key", "test-api-key"
        )

        article = self._create_scraped_article(with_header_image=False)

        test_image = _create_test_image(1920, 1080)

        pixabay_response = {
            "hits": [
                {
                    "id": 77777,
                    "largeImageURL": "https://pixabay.com/get/77777_1280.jpg",
                    "imageWidth": 1920,
                    "imageHeight": 1080,
                },
            ],
        }

        log_entries = []

        def add_entry(level, message, **kwargs):
            log_entries.append({"level": level, "message": message, **kwargs})

        with patch("odoo.addons.newsfeed.models.news_article.requests.get") as mock_get:
            def mock_get_side_effect(url, **kwargs):
                if "pixabay.com/api" in url:
                    return _make_mock_response(200, json_data=pixabay_response)
                else:
                    return _make_mock_response(200, content=test_image, content_type="image/jpeg")

            mock_get.side_effect = mock_get_side_effect

            blog_post = article._create_blog_post(
                teaser="Test teaser",
                log_entries=log_entries,
                add_entry=add_entry,
            )

        self.assertIsNotNone(blog_post)

        # Verify attachment was created from Pixabay
        attachment = self.env["ir.attachment"].search([
            ("res_model", "=", "blog.post"),
            ("res_id", "=", blog_post.id),
        ])
        self.assertEqual(len(attachment), 1)
        self.assertEqual(attachment.name, "pixabay_77777.jpg")

        # Verify cover_properties is set
        self.assertTrue(blog_post.cover_properties)
        cover_props = json.loads(blog_post.cover_properties)
        self.assertIn("background-image", cover_props)

    def test_blog_post_created_without_image(self):
        """Test that blog post is created successfully even without any image."""
        # No Pixabay API key
        self.env["ir.config_parameter"].sudo().set_param("newsfeed.pixabay_api_key", "")

        article = self._create_scraped_article(with_header_image=False)

        log_entries = []

        def add_entry(level, message, **kwargs):
            log_entries.append({"level": level, "message": message, **kwargs})

        blog_post = article._create_blog_post(
            teaser="Test teaser",
            log_entries=log_entries,
            add_entry=add_entry,
        )

        # Blog post should still be created
        self.assertIsNotNone(blog_post)
        self.assertEqual(blog_post.name, article.title)
        self.assertTrue(blog_post.is_published)

        # No attachment should exist
        attachment = self.env["ir.attachment"].search([
            ("res_model", "=", "blog.post"),
            ("res_id", "=", blog_post.id),
        ])
        self.assertEqual(len(attachment), 0)

    def test_create_header_image_attachment_correct_fields(self):
        """Test that _create_header_image_attachment creates correct attachment."""
        article = self._create_scraped_article()

        # First create a blog post
        blog_post = self.env["blog.post"].create({
            "name": "Test Post",
            "blog_id": self.blog.id,
            "content": "<p>Test</p>",
        })

        test_image = _create_test_image(1200, 600)

        attachment = article._create_header_image_attachment(
            image_data=test_image,
            filename="custom_image.jpg",
            blog_post=blog_post,
        )

        self.assertEqual(attachment.name, "custom_image.jpg")
        self.assertEqual(attachment.res_model, "blog.post")
        self.assertEqual(attachment.res_id, blog_post.id)
        self.assertEqual(attachment.mimetype, "image/jpeg")

        # Verify image data is correct
        stored_data = base64.b64decode(attachment.datas)
        self.assertEqual(stored_data, test_image)

    def test_create_header_image_attachment_png_mimetype(self):
        """Test that PNG images get correct mimetype."""
        article = self._create_scraped_article()

        blog_post = self.env["blog.post"].create({
            "name": "Test Post",
            "blog_id": self.blog.id,
            "content": "<p>Test</p>",
        })

        png_image = _create_test_image(1200, 600, format="PNG")

        attachment = article._create_header_image_attachment(
            image_data=png_image,
            filename="image.png",
            blog_post=blog_post,
        )

        self.assertEqual(attachment.mimetype, "image/png")

    def test_set_blog_cover_properties(self):
        """Test that _set_blog_cover_properties sets correct JSON."""
        article = self._create_scraped_article()

        blog_post = self.env["blog.post"].create({
            "name": "Test Post",
            "blog_id": self.blog.id,
            "content": "<p>Test</p>",
        })

        attachment = self.env["ir.attachment"].create({
            "name": "test.jpg",
            "datas": base64.b64encode(b"fake image data").decode("utf-8"),
            "res_model": "blog.post",
            "res_id": blog_post.id,
        })

        article._set_blog_cover_properties(blog_post, attachment)

        # Verify cover_properties is set
        self.assertTrue(blog_post.cover_properties)
        cover_props = json.loads(blog_post.cover_properties)

        expected_url = f"url(/web/image/{attachment.id})"
        self.assertEqual(cover_props["background-image"], expected_url)

    def test_blog_post_deduplication_skips_header_image(self):
        """Test that duplicate blog post detection skips header image logic."""
        article = self._create_scraped_article(with_header_image=True)

        log_entries = []

        def add_entry(level, message, **kwargs):
            log_entries.append({"level": level, "message": message, **kwargs})

        # Create first blog post
        first_post = article._create_blog_post(
            teaser="First teaser",
            log_entries=log_entries,
            add_entry=add_entry,
        )

        # Try to create second blog post for same article
        second_post = article._create_blog_post(
            teaser="Second teaser",
            log_entries=log_entries,
            add_entry=add_entry,
        )

        # Should return the existing post
        self.assertEqual(first_post.id, second_post.id)

        # Should only have one attachment
        attachments = self.env["ir.attachment"].search([
            ("res_model", "=", "blog.post"),
            ("res_id", "=", first_post.id),
        ])
        self.assertEqual(len(attachments), 1)

    def test_log_entries_indicate_image_source(self):
        """Test that log entries correctly indicate image source."""
        article = self._create_scraped_article(with_header_image=True)

        log_entries = []

        def add_entry(level, message, **kwargs):
            log_entries.append({"level": level, "message": message, **kwargs})

        article._create_blog_post(
            teaser="Test teaser",
            log_entries=log_entries,
            add_entry=add_entry,
        )

        # Find log entry about header image
        image_logs = [e for e in log_entries if "Header image" in e.get("message", "")]
        self.assertTrue(len(image_logs) > 0)

        # Should mention "from article"
        self.assertTrue(any("from article" in e["message"] for e in image_logs))


@tagged("post_install", "-at_install")
class TestKanbanHeaderImageDisplay(TransactionCase):
    """Test that Kanban view correctly displays header images."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.source = cls.env["news.source"].create({
            "name": "Test Source",
            "url": "https://example.com/news",
        })
        cls.stage_new = cls.env.ref("newsassistant.news_article_stage_new")

    def test_article_with_header_image_has_binary_field(self):
        """Test that article with header image has the binary field populated."""
        test_image = _create_test_image(1200, 600)

        article = self.env["news.article"].create({
            "title": "Article with Image",
            "source_id": self.source.id,
            "url": "https://example.com/article/1",
            "stage_id": self.stage_new.id,
            "header_image": base64.b64encode(test_image).decode("utf-8"),
            "header_image_filename": "header.jpg",
        })

        # Verify the raw value exists (used by Kanban template)
        self.assertTrue(article.header_image)
        self.assertEqual(article.header_image_filename, "header.jpg")

        # The binary field should be readable
        decoded = base64.b64decode(article.header_image)
        self.assertEqual(decoded, test_image)

    def test_article_without_header_image_has_empty_field(self):
        """Test that article without header image has empty binary field."""
        article = self.env["news.article"].create({
            "title": "Article without Image",
            "source_id": self.source.id,
            "url": "https://example.com/article/2",
            "stage_id": self.stage_new.id,
        })

        # Verify the field is empty/False
        self.assertFalse(article.header_image)
        self.assertFalse(article.header_image_filename)

    def test_kanban_view_exists_with_header_image_field(self):
        """Test that Kanban view definition includes header_image field."""
        # Get the Kanban view
        View = self.env["ir.ui.view"]
        kanban_view = View.search([
            ("model", "=", "news.article"),
            ("type", "=", "kanban"),
        ], limit=1)

        self.assertTrue(kanban_view, "Kanban view should exist for news.article")

        # Check the arch contains header_image
        arch = kanban_view.arch
        self.assertIn("header_image", arch, "Kanban view should reference header_image field")

    def test_header_image_field_is_binary_type(self):
        """Test that header_image field is of Binary type."""
        Article = self.env["news.article"]
        field = Article._fields.get("header_image")

        self.assertIsNotNone(field, "header_image field should exist")
        self.assertEqual(field.type, "binary", "header_image should be Binary field")

    def test_header_image_can_be_read_via_orm(self):
        """Test that header_image can be read via standard ORM methods."""
        test_image = _create_test_image(1200, 600)

        article = self.env["news.article"].create({
            "title": "Test Article",
            "source_id": self.source.id,
            "url": "https://example.com/article/3",
            "stage_id": self.stage_new.id,
            "header_image": base64.b64encode(test_image).decode("utf-8"),
            "header_image_filename": "test.jpg",
        })

        # Read via ORM (as Kanban would)
        article_data = article.read(["header_image", "header_image_filename"])[0]

        self.assertTrue(article_data["header_image"])
        self.assertEqual(article_data["header_image_filename"], "test.jpg")
