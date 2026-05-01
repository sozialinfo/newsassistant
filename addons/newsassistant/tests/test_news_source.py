"""Tests for news.source model."""
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestNewsSource(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, queue_job__no_delay=True))
        cls.source = cls.env["news.source"].create({
            "name": "Test Source",
            "source_type": "website",
            "url": "https://example.com/news",
        })

    def test_create_source_defaults(self):
        """Test that a new source has correct default values."""
        self.assertTrue(self.source.active)
        self.assertEqual(self.source.state, "ok")
        self.assertFalse(self.source.error_message)
        self.assertFalse(self.source.last_scrape_date)
        self.assertEqual(self.source.article_count, 0)
        self.assertEqual(self.source.source_type, "website")

    def test_create_email_source(self):
        """Test creating an email-type source."""
        source = self.env["news.source"].create({
            "name": "Email Newsletter",
            "source_type": "email",
            "sender_domain": "newsletter.example.com",
        })
        self.assertEqual(source.source_type, "email")
        self.assertEqual(source.sender_domain, "newsletter.example.com")
        self.assertTrue(source.active)
        self.assertEqual(source.state, "ok")

    def test_computed_article_count_via_snapshots(self):
        """Test that article_count reflects articles via snapshots."""
        # Create snapshots linked to source
        stage = self.env.ref("newsassistant.news_article_stage_new")
        snapshot = self.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": self.source.id,
            "raw_content": "<p>Content</p>",
        })
        # Create articles linked to snapshot (bypassing queue jobs)
        for i in range(3):
            self.env["news.article"].create({
                "title": f"Article {i}",
                "snapshot_id": snapshot.id,
                "url": f"https://example.com/article/{i}",
                "stage_id": stage.id,
            })
        self.source.invalidate_recordset(["article_count"])
        self.assertEqual(self.source.article_count, 3)

    def test_error_state_tracking(self):
        """Test that source error state can be set and cleared."""
        self.source.write({
            "state": "error",
            "error_message": "HTTP 404 fetching listing page",
        })
        self.assertEqual(self.source.state, "error")
        self.assertEqual(self.source.error_message, "HTTP 404 fetching listing page")

    def test_error_state_recovery(self):
        """Test that source recovers from error state."""
        self.source.write({
            "state": "error",
            "error_message": "Some error",
        })
        self.source.write({
            "state": "ok",
            "error_message": False,
        })
        self.assertEqual(self.source.state, "ok")
        self.assertFalse(self.source.error_message)

    def test_source_name_required(self):
        """Test that name is required."""
        with self.assertRaises(Exception):
            self.env["news.source"].create({
                "url": "https://example.com",
            })

    def test_source_snapshot_ids(self):
        """Test that source has snapshot_ids one2many."""
        snapshot = self.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": self.source.id,
            "raw_content": "<p>Test content</p>",
        })
        self.assertIn(snapshot, self.source.snapshot_ids)

    def test_source_type_default_is_website(self):
        """Test that source_type defaults to website."""
        source = self.env["news.source"].create({
            "name": "Website Source",
            "url": "https://example.com",
        })
        self.assertEqual(source.source_type, "website")

    def test_snapshot_count_zero_for_new_source(self):
        """New source should have zero snapshot count."""
        source = self.env["news.source"].create({
            "name": "No Snapshots Source",
            "source_type": "website",
            "url": "https://no-snap.example.com",
        })
        self.assertEqual(source.snapshot_count, 0)

    def test_snapshot_count_reflects_snapshots(self):
        """snapshot_count should reflect the number of snapshots for this source."""
        source = self.env["news.source"].create({
            "name": "Snap Count Source",
            "source_type": "website",
            "url": "https://snap-count.example.com",
        })
        for _ in range(3):
            self.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
                "source_id": source.id,
                "raw_content": "<p>snap</p>",
            })
        source.invalidate_recordset(["snapshot_count"])
        self.assertEqual(source.snapshot_count, 3)

    def test_log_count_zero_for_new_source(self):
        """New source should have zero log count."""
        source = self.env["news.source"].create({
            "name": "No Logs Source",
            "source_type": "website",
            "url": "https://no-log.example.com",
        })
        self.assertEqual(source.log_count, 0)

    def test_log_count_reflects_logs(self):
        """log_count should reflect the number of logs for this source."""
        source = self.env["news.source"].create({
            "name": "Log Count Source",
            "source_type": "website",
            "url": "https://log-count.example.com",
        })
        for i in range(2):
            self.env["news.log"].create({
                "source_id": source.id,
                "level": "success",
                "category": "listing",
                "message": f"Log entry {i}",
            })
        source.invalidate_recordset(["log_count"])
        self.assertEqual(source.log_count, 2)

    def test_job_count_zero_for_new_source(self):
        """New source should have zero job count (no jobs in test context)."""
        source = self.env["news.source"].create({
            "name": "No Jobs Source",
            "source_type": "website",
            "url": "https://no-jobs.example.com",
        })
        self.assertEqual(source.job_count, 0)

    def test_action_view_jobs_returns_window_action(self):
        """action_view_jobs should return a window action for queue.job."""
        action = self.source.action_view_jobs()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "queue.job")
