import json
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.queue_job.tests.common import trap_jobs


@tagged("post_install", "-at_install")
class TestQueueJobs(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Deactivate any demo sources to isolate tests
        cls.env["news.source"].search([]).write({"active": False})
        cls.source1 = cls.env["news.source"].create({
            "name": "Active Source 1",
            "url": "https://example1.com/news",
            "active": True,
        })
        cls.source2 = cls.env["news.source"].create({
            "name": "Active Source 2",
            "url": "https://example2.com/news",
            "active": True,
        })
        cls.source_inactive = cls.env["news.source"].create({
            "name": "Inactive Source",
            "url": "https://example3.com/news",
            "active": False,
        })

    def test_cron_creates_jobs_for_active_sources(self):
        """Test that _cron_scrape_all creates one job per active source."""
        with trap_jobs() as trap:
            self.env["news.source"]._cron_scrape_all()
            # 2 active sources -> 2 jobs
            trap.assert_jobs_count(2)
            # Verify the jobs are for _scrape_listing
            for job in trap.enqueued_jobs:
                self.assertEqual(job.method_name, "_scrape_listing")

    def test_cron_skips_inactive_sources(self):
        """Test that inactive sources do not get scrape jobs."""
        with trap_jobs() as trap:
            self.env["news.source"]._cron_scrape_all()
            # Should only be 2 jobs (for active sources), not 3
            trap.assert_jobs_count(2)
            # Verify job recordsets don't include the inactive source
            job_record_ids = [job.recordset.id for job in trap.enqueued_jobs]
            self.assertNotIn(self.source_inactive.id, job_record_ids)

    def test_scrape_listing_creates_article_jobs(self):
        """Test that _scrape_listing creates fetch_and_extract jobs for new articles."""
        listing_response = MagicMock()
        listing_response.status_code = 200
        listing_response.text = "<html><body><p>News</p></body></html>"

        ai_data = json.dumps([
            {"title": "Art 1", "url": "https://example1.com/art/1"},
            {"title": "Art 2", "url": "https://example1.com/art/2"},
        ])
        ai_response = MagicMock()
        ai_response.status_code = 200
        ai_response.json.return_value = {
            "choices": [{"message": {"content": ai_data}}],
        }

        with patch(
            "odoo.addons.newsassistant.models.news_source.requests.get",
            return_value=listing_response,
        ), patch(
            "odoo.addons.newsassistant.models.news_source.requests.post",
            return_value=ai_response,
        ):
            with trap_jobs() as trap:
                self.source1._scrape_listing()
                # 2 new articles -> 2 _fetch_and_extract jobs
                trap.assert_jobs_count(2)
                for job in trap.enqueued_jobs:
                    self.assertEqual(job.method_name, "_fetch_and_extract")

    def test_transient_http_error_raises_retryable(self):
        """Test that HTTP 503 on listing page raises RetryableJobError."""
        response_503 = MagicMock()
        response_503.status_code = 503

        with patch(
            "odoo.addons.newsassistant.models.news_source.requests.get",
            return_value=response_503,
        ):
            with self.assertRaises(RetryableJobError):
                self.source1._scrape_listing()

    def test_ai_api_rate_limit_raises_retryable(self):
        """Test that AI API 429 raises RetryableJobError."""
        listing_response = MagicMock()
        listing_response.status_code = 200
        listing_response.text = "<html><body>Content</body></html>"

        ai_response = MagicMock()
        ai_response.status_code = 429

        with patch(
            "odoo.addons.newsassistant.models.news_source.requests.get",
            return_value=listing_response,
        ), patch(
            "odoo.addons.newsassistant.models.news_source.requests.post",
            return_value=ai_response,
        ):
            with self.assertRaises(RetryableJobError):
                self.source1._scrape_listing()
