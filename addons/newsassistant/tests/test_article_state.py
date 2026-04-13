"""Tests for article state tracking and transitions."""

import json
from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged


AI_ARTICLE_RESPONSE = json.dumps({
    "title": "Full Article Title",
    "date": "2025-03-15",
    "summary": "This article covers important topics.",
    "content": "<p>Article content.</p>",
})


def _make_mock_response(status_code=200, json_data=None):
    from unittest.mock import MagicMock
    response = MagicMock()
    response.status_code = status_code
    if json_data:
        response.json.return_value = json_data
    return response


@tagged("post_install", "-at_install")
class TestArticleState(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.source = cls.env["news.source"].create({
            "name": "Test Source",
            "url": "https://example.com/news",
        })
        cls.stage_new = cls.env.ref("newsassistant.news_article_stage_new")

    def test_article_default_state_is_pending(self):
        """New articles should have state 'pending'."""
        article = self.env["news.article"].create({
            "title": "Test Article",
            "source_id": self.source.id,
            "url": "https://example.com/test",
            "stage_id": self.stage_new.id,
        })
        self.assertEqual(article.state, "pending")
        self.assertEqual(article.retry_count, 0)
        self.assertFalse(article.error_message)
        self.assertFalse(article.last_error_date)

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_successful_extraction_sets_scraped(self, mock_fetch, mock_post):
        """Successful extraction should set state to 'scraped'."""
        article = self.env["news.article"].create({
            "title": "Test Article",
            "source_id": self.source.id,
            "url": "https://example.com/test",
            "stage_id": self.stage_new.id,
        })
        mock_fetch.return_value = "# Article content"
        mock_post.return_value = _make_mock_response(200, json_data={
            "choices": [{"message": {"content": AI_ARTICLE_RESPONSE}}],
        })

        article._fetch_and_extract()

        self.assertEqual(article.state, "scraped")
        self.assertFalse(article.error_message)
        self.assertFalse(article.last_error_date)

    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_failed_extraction_sets_error(self, mock_fetch):
        """Failed extraction should set state to 'error'."""
        article = self.env["news.article"].create({
            "title": "Test Article",
            "source_id": self.source.id,
            "url": "https://example.com/test",
            "stage_id": self.stage_new.id,
        })
        mock_fetch.side_effect = ValueError("Jina API error 404")

        article._fetch_and_extract()

        self.assertEqual(article.state, "error")
        self.assertEqual(article.retry_count, 1)
        self.assertIn("404", article.error_message)
        self.assertTrue(article.last_error_date)

    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_retry_count_increments(self, mock_fetch):
        """Each failure should increment retry_count."""
        article = self.env["news.article"].create({
            "title": "Test Article",
            "source_id": self.source.id,
            "url": "https://example.com/test",
            "stage_id": self.stage_new.id,
        })
        mock_fetch.side_effect = ValueError("Error")

        article._fetch_and_extract()
        self.assertEqual(article.retry_count, 1)

        article._fetch_and_extract()
        self.assertEqual(article.retry_count, 2)

        article._fetch_and_extract()
        self.assertEqual(article.retry_count, 3)

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_error_article_recovers_on_success(self, mock_fetch, mock_post):
        """Error article should recover to 'scraped' on success."""
        article = self.env["news.article"].create({
            "title": "Test Article",
            "source_id": self.source.id,
            "url": "https://example.com/test",
            "stage_id": self.stage_new.id,
            "state": "error",
            "error_message": "Previous error",
            "retry_count": 3,
        })

        mock_fetch.return_value = "# Article content"
        mock_post.return_value = _make_mock_response(200, json_data={
            "choices": [{"message": {"content": AI_ARTICLE_RESPONSE}}],
        })

        article._fetch_and_extract()

        self.assertEqual(article.state, "scraped")
        self.assertFalse(article.error_message)
        self.assertFalse(article.last_error_date)
        # retry_count is preserved
        self.assertEqual(article.retry_count, 3)

    def test_action_skip(self):
        """action_skip should set state to 'skipped'."""
        article = self.env["news.article"].create({
            "title": "Test Article",
            "source_id": self.source.id,
            "url": "https://example.com/test",
            "stage_id": self.stage_new.id,
            "state": "error",
            "error_message": "Some error",
            "retry_count": 2,
        })

        article.action_skip()

        self.assertEqual(article.state, "skipped")
        # Error fields preserved
        self.assertEqual(article.error_message, "Some error")
        self.assertEqual(article.retry_count, 2)

    def test_action_reset(self):
        """action_reset should reset to 'pending' and clear error fields."""
        article = self.env["news.article"].create({
            "title": "Test Article",
            "source_id": self.source.id,
            "url": "https://example.com/test",
            "stage_id": self.stage_new.id,
            "state": "skipped",
            "error_message": "Some error",
            "retry_count": 5,
        })

        article.action_reset()

        self.assertEqual(article.state, "pending")
        self.assertFalse(article.error_message)
        self.assertFalse(article.last_error_date)
        self.assertEqual(article.retry_count, 0)


@tagged("post_install", "-at_install")
class TestScrapeHistory(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.source = cls.env["news.source"].create({
            "name": "Test Source",
            "url": "https://example.com/news",
        })
        cls.stage_new = cls.env.ref("newsassistant.news_article_stage_new")

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant.models.news_source.fetch_page")
    def test_source_log_created_on_success(self, mock_fetch, mock_post):
        """Source scrape should create log entry on success."""
        from odoo.addons.queue_job.tests.common import trap_jobs

        mock_fetch.return_value = "# Empty page"
        mock_post.return_value = _make_mock_response(200, json_data={
            "choices": [{"message": {"content": "[]"}}],
        })

        with trap_jobs():
            self.source._scrape_listing()

        logs = self.env["news.source.log"].search([("source_id", "=", self.source.id)])
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs.status, "success")
        self.assertTrue(logs.duration >= 0)

    @patch("odoo.addons.newsassistant.models.news_source.fetch_page")
    def test_source_log_created_on_error(self, mock_fetch):
        """Source scrape should create log entry on error."""
        mock_fetch.side_effect = ValueError("Fetch error")

        self.source._scrape_listing()

        logs = self.env["news.source.log"].search([("source_id", "=", self.source.id)])
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs.status, "error")
        self.assertIn("Fetch error", logs.error_message)

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_article_log_created_on_success(self, mock_fetch, mock_post):
        """Article extraction should create log entry on success."""
        article = self.env["news.article"].create({
            "title": "Test Article",
            "source_id": self.source.id,
            "url": "https://example.com/test",
            "stage_id": self.stage_new.id,
        })

        mock_fetch.return_value = "# Article content"
        mock_post.return_value = _make_mock_response(200, json_data={
            "choices": [{"message": {"content": AI_ARTICLE_RESPONSE}}],
        })

        article._fetch_and_extract()

        logs = self.env["news.article.log"].search([("article_id", "=", article.id)])
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs.status, "success")
        self.assertTrue(logs.duration >= 0)

    @patch("odoo.addons.newsassistant.models.news_article.fetch_page")
    def test_article_log_created_on_error(self, mock_fetch):
        """Article extraction should create log entry on error."""
        article = self.env["news.article"].create({
            "title": "Test Article",
            "source_id": self.source.id,
            "url": "https://example.com/test",
            "stage_id": self.stage_new.id,
        })

        mock_fetch.side_effect = ValueError("Fetch error")

        article._fetch_and_extract()

        logs = self.env["news.article.log"].search([("article_id", "=", article.id)])
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs.status, "error")
        self.assertIn("Fetch error", logs.error_message)
