import json
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.queue_job.tests.common import trap_jobs


# Markdown content as returned by Jina Reader API
LISTING_MARKDOWN = """
# News Site

[Article One](https://example.com/article/1)
Summary one.

[Article Two](https://example.com/article/2)
Summary two.
"""

ARTICLE_MARKDOWN = """
# Full Article Title

Published: 2025-03-15

This is the first paragraph of the article.

This is the second paragraph with more details.
"""

AI_LISTING_RESPONSE = json.dumps([
    {"title": "Article One", "url": "https://example.com/article/1"},
    {"title": "Article Two", "url": "https://example.com/article/2"},
])

AI_ARTICLE_RESPONSE = json.dumps({
    "title": "Full Article Title",
    "date": "2025-03-15",
    "summary": "This article covers important topics. It has two paragraphs.",
    "content": "<p>This is the first paragraph of the article.</p><p>This is the second paragraph with more details.</p>",
})


def _make_mock_response(status_code=200, text="", json_data=None, content_type="text/html"):
    response = MagicMock()
    response.status_code = status_code
    response.text = text
    response.content = text.encode("utf-8") if isinstance(text, str) else text
    response.headers = {"content-type": content_type}
    if json_data:
        response.json.return_value = json_data
    return response


@tagged("post_install", "-at_install")
class TestScrapingPipelineStage1(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.source = cls.env["news.source"].create({
            "name": "Test Source",
            "url": "https://example.com/news",
        })

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant.models.news_source.fetch_page")
    def test_stage1_discovers_articles(self, mock_fetch, mock_post):
        """Test that Stage 1 discovers article URLs from listing page."""
        mock_fetch.return_value = LISTING_MARKDOWN
        ai_response_data = {
            "choices": [{"message": {"content": AI_LISTING_RESPONSE}}],
        }
        mock_post.return_value = _make_mock_response(200, json_data=ai_response_data)

        # Use trap_jobs so article jobs are trapped, not executed
        with trap_jobs() as trap:
            self.source._scrape_listing()
            trap.assert_jobs_count(2)
            for job in trap.enqueued_jobs:
                self.assertEqual(job.method_name, "_fetch_and_extract")

        # Verify articles were created
        articles = self.env["news.article"].search([("source_id", "=", self.source.id)])
        self.assertEqual(len(articles), 2)
        urls = articles.mapped("url")
        self.assertIn("https://example.com/article/1", urls)
        self.assertIn("https://example.com/article/2", urls)

        # Verify source state updated
        self.assertEqual(self.source.state, "ok")
        self.assertTrue(self.source.last_scrape_date)

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant.models.news_source.fetch_page")
    def test_stage1_deduplication(self, mock_fetch, mock_post):
        """Test that known URLs are skipped in Stage 1."""
        stage = self.env.ref("newsassistant.news_article_stage_new")
        # Pre-create one article
        self.env["news.article"].create({
            "title": "Existing Article",
            "source_id": self.source.id,
            "url": "https://example.com/article/1",
            "stage_id": stage.id,
        })

        mock_fetch.return_value = LISTING_MARKDOWN
        ai_response_data = {
            "choices": [{"message": {"content": AI_LISTING_RESPONSE}}],
        }
        mock_post.return_value = _make_mock_response(200, json_data=ai_response_data)

        with trap_jobs() as trap:
            self.source._scrape_listing()
            # Only 1 new article should get a job (article/2), article/1 is deduped
            trap.assert_jobs_count(1)

        articles = self.env["news.article"].search([("source_id", "=", self.source.id)])
        self.assertEqual(len(articles), 2)  # 1 existing + 1 new

    @patch("odoo.addons.newsassistant.models.news_source.fetch_page")
    def test_stage1_jina_error_sets_error(self, mock_fetch):
        """Test that Jina API error sets source to error state."""
        mock_fetch.side_effect = ValueError("Jina API error 404: Not found")

        self.source._scrape_listing()

        self.assertEqual(self.source.state, "error")
        self.assertIn("Jina", self.source.error_message)

    @patch("odoo.addons.newsassistant.models.news_source.fetch_page")
    def test_stage1_jina_503_raises_retryable(self, mock_fetch):
        """Test that Jina 503 raises RetryableJobError."""
        mock_fetch.side_effect = RetryableJobError("Jina API returned 503", seconds=300)

        with self.assertRaises(RetryableJobError):
            self.source._scrape_listing()

    @patch("odoo.addons.newsassistant.models.news_source.fetch_page")
    def test_stage1_timeout_raises_retryable(self, mock_fetch):
        """Test that timeout raises RetryableJobError."""
        mock_fetch.side_effect = RetryableJobError("Timeout fetching via Jina", seconds=300)

        with self.assertRaises(RetryableJobError):
            self.source._scrape_listing()

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant.models.news_source.fetch_page")
    def test_stage1_malformed_ai_response(self, mock_fetch, mock_post):
        """Test that malformed AI JSON sets source to error state."""
        mock_fetch.return_value = LISTING_MARKDOWN
        ai_response_data = {
            "choices": [{"message": {"content": "This is not JSON"}}],
        }
        mock_post.return_value = _make_mock_response(200, json_data=ai_response_data)

        self.source._scrape_listing()

        self.assertEqual(self.source.state, "error")
        self.assertIn("JSON", self.source.error_message)

    @patch("odoo.addons.newsassistant.models.news_source.fetch_page")
    def test_stage1_missing_jina_key_sets_error(self, mock_fetch):
        """Test that missing JINA_API_KEY sets source to error state."""
        mock_fetch.side_effect = ValueError("JINA_API_KEY environment variable not set")

        self.source._scrape_listing()

        self.assertEqual(self.source.state, "error")
        self.assertIn("JINA_API_KEY", self.source.error_message)


@tagged("post_install", "-at_install")
class TestScrapingPipelineStage2(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, queue_job__no_delay=True))
        cls.source = cls.env["news.source"].create({
            "name": "Test Source",
            "url": "https://example.com/news",
        })
        cls.stage_new = cls.env.ref("newsassistant.news_article_stage_new")
        cls.article = cls.env["news.article"].create({
            "title": "Placeholder Title",
            "source_id": cls.source.id,
            "url": "https://example.com/article/1",
            "stage_id": cls.stage_new.id,
        })

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_stage2_extracts_content(self, mock_fetch, mock_post):
        """Test that Stage 2 extracts article content correctly."""
        mock_fetch.return_value = ARTICLE_MARKDOWN
        ai_response_data = {
            "choices": [{"message": {"content": AI_ARTICLE_RESPONSE}}],
        }
        mock_post.return_value = _make_mock_response(200, json_data=ai_response_data)

        self.article._fetch_and_extract()

        self.assertEqual(self.article.title, "Full Article Title")
        self.assertEqual(str(self.article.date), "2025-03-15")
        self.assertIn("important topics", self.article.summary)
        self.assertIn("first paragraph", self.article.content)
        self.assertTrue(self.article.scrape_date)

    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_stage2_jina_error_logs_error(self, mock_fetch):
        """Test that Jina API error on article page sets error state."""
        mock_fetch.side_effect = ValueError("Jina API error 404: Not found")

        self.article._fetch_and_extract()

        self.assertEqual(self.article.state, "error")
        self.assertIn("404", self.article.error_message)
        self.assertTrue(self.article.scrape_date)

    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_stage2_jina_503_raises_retryable(self, mock_fetch):
        """Test that Jina 503 raises RetryableJobError."""
        mock_fetch.side_effect = RetryableJobError("Jina API returned 503", seconds=300)

        with self.assertRaises(RetryableJobError):
            self.article._fetch_and_extract()

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_stage2_malformed_ai_response(self, mock_fetch, mock_post):
        """Test that malformed AI response sets error state."""
        mock_fetch.return_value = ARTICLE_MARKDOWN
        ai_response_data = {
            "choices": [{"message": {"content": "not valid json"}}],
        }
        mock_post.return_value = _make_mock_response(200, json_data=ai_response_data)

        self.article._fetch_and_extract()

        self.assertEqual(self.article.state, "error")
        self.assertIn("Invalid AI response", self.article.error_message)
        self.assertTrue(self.article.scrape_date)

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_stage2_ai_returns_markdown_fences(self, mock_fetch, mock_post):
        """Test that markdown code fences in AI response are stripped."""
        mock_fetch.return_value = ARTICLE_MARKDOWN
        fenced_response = f"```json\n{AI_ARTICLE_RESPONSE}\n```"
        ai_response_data = {
            "choices": [{"message": {"content": fenced_response}}],
        }
        mock_post.return_value = _make_mock_response(200, json_data=ai_response_data)

        self.article._fetch_and_extract()

        self.assertEqual(self.article.title, "Full Article Title")
        self.assertIn("first paragraph", self.article.content)

    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_stage2_missing_jina_key_logs_error(self, mock_fetch):
        """Test that missing JINA_API_KEY sets error state."""
        mock_fetch.side_effect = ValueError("JINA_API_KEY environment variable not set")

        self.article._fetch_and_extract()

        self.assertEqual(self.article.state, "error")
        self.assertIn("JINA_API_KEY", self.article.error_message)
        self.assertTrue(self.article.scrape_date)
