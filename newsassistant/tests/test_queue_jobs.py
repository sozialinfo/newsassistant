"""Tests for queue job integration with news.snapshot."""
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.queue_job.tests.common import trap_jobs


@tagged("post_install", "-at_install")
class TestQueueJobs(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["news.source"].search([]).write({"active": False})
        cls.source = cls.env["news.source"].create({
            "name": "Active Source",
            "source_type": "website",
            "url": "https://example.com/news",
            "active": True,
        })

    def test_snapshot_create_enqueues_extract_job(self):
        """Creating a non-listing snapshot should enqueue _extract_articles."""
        plain_env = self.env(context={})
        with trap_jobs() as trap:
            plain_env["news.snapshot"].create({
                "source_id": self.source.id,
                "raw_content": "<p>Content</p>",
            })
            trap.assert_jobs_count(1)
            job = trap.enqueued_jobs[0]
            self.assertEqual(job.method_name, "_extract_articles")

    def test_listing_snapshot_enqueues_discover_job(self):
        """Creating a listing snapshot should enqueue _discover_articles."""
        plain_env = self.env(context={})
        with trap_jobs() as trap:
            plain_env["news.snapshot"].create({
                "source_id": self.source.id,
                "raw_content": "<p>Listing</p>",
                "is_listing": True,
            })
            trap.assert_jobs_count(1)
            job = trap.enqueued_jobs[0]
            self.assertEqual(job.method_name, "_discover_articles")

    def test_snapshot_create_multiple_each_enqueues_job(self):
        """Creating multiple snapshots enqueues one job per snapshot."""
        plain_env = self.env(context={})
        with trap_jobs() as trap:
            plain_env["news.snapshot"].create([
                {"source_id": self.source.id, "raw_content": "<p>A</p>"},
                {"source_id": self.source.id, "raw_content": "<p>B</p>"},
            ])
            trap.assert_jobs_count(2)
