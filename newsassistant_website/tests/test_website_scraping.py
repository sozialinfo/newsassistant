"""Tests for website scraping pipeline."""
import json
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.queue_job.tests.common import trap_jobs


LISTING_MARKDOWN = """
# News Site

[Article One](https://example.com/article/1)
Summary one.

[Article Two](https://example.com/article/2)
Summary two.
"""

AI_LISTING_RESPONSE = json.dumps([
    {"title": "Article One", "url": "https://example.com/article/1"},
    {"title": "Article Two", "url": "https://example.com/article/2"},
])


def _make_mock_response(status_code=200, json_data=None, text=""):
    response = MagicMock()
    response.status_code = status_code
    response.text = text
    if json_data:
        response.json.return_value = json_data
    return response


def _make_ai_response(content):
    return {
        "choices": [{"message": {"content": content}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    }


@tagged("post_install", "-at_install")
class TestWebsiteListingScrape(TransactionCase):
    """Tests for NewsSourceWebsite._scrape_listing()."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.source = cls.env["news.source"].create({
            "name": "Test Source",
            "source_type": "website",
            "url": "https://example.com/news",
        })

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant_website.models.news_source_website.fetch_page")
    def test_scrape_listing_enqueues_snapshot_jobs(self, mock_fetch, mock_ai):
        """Listing scrape enqueues _fetch_and_create_snapshot jobs for each new URL."""
        mock_fetch.return_value = (LISTING_MARKDOWN, {})
        mock_ai.return_value = _make_mock_response(200, json_data=_make_ai_response(AI_LISTING_RESPONSE))

        with trap_jobs() as trap:
            source = self.source.with_env(self.env(context=dict(self.env.context, queue_job__no_delay=False)))
            source._scrape_listing()
            jobs = [j for j in trap.enqueued_jobs if j.method_name == "_fetch_and_create_snapshot"]
            self.assertEqual(len(jobs), 2)

    @patch("odoo.addons.newsassistant_website.models.news_source_website.fetch_page")
    def test_scrape_listing_crawl4ai_error_raises_retryable(self, mock_fetch):
        """crawl4ai error raises RetryableJobError."""
        mock_fetch.side_effect = RetryableJobError("crawl4ai error", seconds=300)
        with self.assertRaises(RetryableJobError):
            self.source._scrape_listing()

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant_website.models.news_source_website.fetch_page")
    def test_scrape_listing_updates_source_state(self, mock_fetch, mock_ai):
        """Successful listing scrape updates source state and last_scrape_date."""
        mock_fetch.return_value = (LISTING_MARKDOWN, {})
        mock_ai.return_value = _make_mock_response(200, json_data=_make_ai_response("[]"))

        self.source._scrape_listing()

        self.assertEqual(self.source.state, "ok")
        self.assertTrue(self.source.last_scrape_date)

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant_website.models.news_source_website.fetch_page")
    def test_scrape_listing_creates_log(self, mock_fetch, mock_ai):
        """Listing scrape creates a news.log record."""
        mock_fetch.return_value = ("# empty", {})
        mock_ai.return_value = _make_mock_response(200, json_data=_make_ai_response("[]"))

        with trap_jobs():
            self.source._scrape_listing()

        logs = self.env["news.log"].search([
            ("source_id", "=", self.source.id),
            ("category", "=", "listing"),
        ])
        self.assertTrue(len(logs) >= 1)

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant_website.models.news_source_website.fetch_page")
    def test_scrape_listing_deduplicates_known_urls(self, mock_fetch, mock_ai):
        """Known article URLs are not re-queued."""
        mock_fetch.return_value = (LISTING_MARKDOWN, {})
        mock_ai.return_value = _make_mock_response(200, json_data=_make_ai_response(AI_LISTING_RESPONSE))

        snapshot = self.env["news.snapshot"].create({
            "source_id": self.source.id,
            "raw_content": "<p>pre-existing</p>",
        })
        self.env["news.article"].create({
            "title": "Existing",
            "snapshot_id": snapshot.id,
            "url": "https://example.com/article/1",
        })

        with trap_jobs() as trap:
            source = self.source.with_env(self.env(context=dict(self.env.context, queue_job__no_delay=False)))
            source._scrape_listing()
            fetch_jobs = [j for j in trap.enqueued_jobs if j.method_name == "_fetch_and_create_snapshot"]
            self.assertEqual(len(fetch_jobs), 1)

    def test_cron_skips_email_sources(self):
        """_cron_scrape_all should not queue email sources."""
        email_source = self.env["news.source"].create({
            "name": "Email Source",
            "source_type": "email",
            "sender_domain": "newsletter.example.com",
            "active": True,
        })
        plain_env = self.env(context={})
        with trap_jobs() as trap:
            plain_env["news.source"]._cron_scrape_all()
            job_record_ids = [j.recordset.id for j in trap.enqueued_jobs if j.method_name == "_scrape_listing"]
            self.assertNotIn(email_source.id, job_record_ids)
