from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestNewsSource(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, queue_job__no_delay=True))
        cls.source = cls.env["news.source"].create({
            "name": "Test Source",
            "url": "https://example.com/news",
        })

    def test_create_source_defaults(self):
        """Test that a new source has correct default values."""
        self.assertTrue(self.source.active)
        self.assertEqual(self.source.state, "ok")
        self.assertFalse(self.source.error_message)
        self.assertFalse(self.source.last_scrape_date)
        self.assertEqual(self.source.article_count, 0)

    def test_computed_article_count(self):
        """Test that article_count reflects related articles."""
        stage = self.env.ref("newsassistant.news_article_stage_new")
        for i in range(3):
            self.env["news.article"].create({
                "title": f"Article {i}",
                "source_id": self.source.id,
                "url": f"https://example.com/article/{i}",
                "stage_id": stage.id,
            })
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
        # Simulate successful scrape recovery
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

    def test_source_url_required(self):
        """Test that url is required."""
        with self.assertRaises(Exception):
            self.env["news.source"].create({
                "name": "No URL Source",
            })
