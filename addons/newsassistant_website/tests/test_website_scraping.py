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


def _make_jina_response(content, images=None):
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "data": {"content": content, "images": images or {}}
    }
    return response


@tagged("post_install", "-at_install")
class TestWebsiteListingScrape(TransactionCase):
    """Tests for NewsSourceWebsite._scrape_listing()."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, queue_job__no_delay=True))
        cls.source = cls.env["news.source"].create({
            "name": "Test Source",
            "source_type": "website",
            "url": "https://example.com/news",
        })

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant_website.models.jina_utils.requests.get")
    @patch.dict("os.environ", {"JINA_API_KEY": "test-key"})
    def test_scrape_listing_enqueues_snapshot_jobs(self, mock_jina, mock_post):
        """Listing scrape enqueues _fetch_and_create_snapshot jobs for each new URL."""
        mock_jina.return_value = _make_jina_response(LISTING_MARKDOWN)
        mock_post.return_value = _make_mock_response(200, json_data=_make_ai_response(AI_LISTING_RESPONSE))

        with trap_jobs() as trap:
            self.source._scrape_listing()
            # Should have enqueued 2 fetch-and-create-snapshot jobs
            jobs = [j for j in trap.enqueued_jobs if j.method_name == "_fetch_and_create_snapshot"]
            self.assertEqual(len(jobs), 2)

    @patch("odoo.addons.newsassistant_website.models.jina_utils.requests.get")
    @patch.dict("os.environ", {"JINA_API_KEY": "test-key"})
    def test_scrape_listing_jina_error_sets_error(self, mock_jina):
        """Jina error on listing page sets source to error state."""
        mock_jina.return_value = MagicMock(
            status_code=404,
            text="Not found",
        )
        self.source._scrape_listing()
        self.assertEqual(self.source.state, "error")

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant_website.models.jina_utils.requests.get")
    @patch.dict("os.environ", {"JINA_API_KEY": "test-key"})
    def test_scrape_listing_updates_source_state(self, mock_jina, mock_post):
        """Successful listing scrape updates source state and last_scrape_date."""
        mock_jina.return_value = _make_jina_response(LISTING_MARKDOWN)
        mock_post.return_value = _make_mock_response(200, json_data=_make_ai_response("[]"))

        self.source._scrape_listing()

        self.assertEqual(self.source.state, "ok")
        self.assertTrue(self.source.last_scrape_date)

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant_website.models.jina_utils.requests.get")
    @patch.dict("os.environ", {"JINA_API_KEY": "test-key"})
    def test_scrape_listing_creates_log(self, mock_jina, mock_post):
        """Listing scrape creates a news.log record."""
        mock_jina.return_value = _make_jina_response("# Empty page")
        mock_post.return_value = _make_mock_response(200, json_data=_make_ai_response("[]"))

        with trap_jobs():
            self.source._scrape_listing()

        logs = self.env["news.log"].search([
            ("source_id", "=", self.source.id),
            ("category", "=", "listing"),
        ])
        self.assertTrue(len(logs) >= 1)

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    @patch("odoo.addons.newsassistant_website.models.jina_utils.requests.get")
    @patch.dict("os.environ", {"JINA_API_KEY": "test-key"})
    def test_scrape_listing_deduplicates_known_urls(self, mock_jina, mock_post):
        """Known article URLs are not re-queued."""
        mock_jina.return_value = _make_jina_response(LISTING_MARKDOWN)
        mock_post.return_value = _make_mock_response(200, json_data=_make_ai_response(AI_LISTING_RESPONSE))

        # Pre-create a snapshot+article for article/1
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
            self.source._scrape_listing()
            fetch_jobs = [j for j in trap.enqueued_jobs if j.method_name == "_fetch_and_create_snapshot"]
            # Only article/2 should be queued (article/1 already exists)
            self.assertEqual(len(fetch_jobs), 1)

    def test_cron_skips_email_sources(self):
        """_cron_scrape_all should not queue email sources."""
        email_source = self.env["news.source"].create({
            "name": "Email Source",
            "source_type": "email",
            "sender_domain": "newsletter.example.com",
            "active": True,
        })
        # Use plain env (no queue_job__no_delay) so trap_jobs works correctly
        plain_env = self.env(context={})
        with trap_jobs() as trap:
            plain_env["news.source"]._cron_scrape_all()
            job_record_ids = [j.recordset.id for j in trap.enqueued_jobs if j.method_name == "_scrape_listing"]
            self.assertNotIn(email_source.id, job_record_ids)
