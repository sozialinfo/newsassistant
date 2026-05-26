"""Tests for article state tracking and transitions."""
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestArticleState(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, queue_job__no_delay=True))
        cls.source = cls.env["news.source"].create({
            "name": "Test Source",
            "source_type": "website",
            "url": "https://example.com/news",
        })
        cls.stage_new = cls.env.ref("newsassistant.news_article_stage_new")
        cls.snapshot = cls.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": cls.source.id,
            "raw_content": "<p>Content</p>",
        })

    def _create_article(self, **kwargs):
        vals = {
            "title": "Test Article",
            "snapshot_id": self.snapshot.id,
            "stage_id": self.stage_new.id,
        }
        vals.update(kwargs)
        return self.env["news.article"].create(vals)

    def test_article_default_state_is_pending(self):
        """New articles should have state 'pending'."""
        article = self._create_article()
        self.assertEqual(article.state, "pending")
        self.assertEqual(article.retry_count, 0)
        self.assertFalse(article.status_message)
        self.assertFalse(article.last_error_date)

    def test_article_source_id_computed_from_snapshot(self):
        """Article source_id should be computed from snapshot."""
        article = self._create_article()
        self.assertEqual(article.source_id, self.source)

    def test_action_skip_sets_skipped_and_archives(self):
        """action_skip should set state to 'skipped' and archive."""
        article = self._create_article(state="error", status_message="Some error", retry_count=2)

        article.action_skip()

        self.assertEqual(article.state, "skipped")
        self.assertFalse(article.active)
        self.assertEqual(article.status_message, "Some error")
        self.assertEqual(article.retry_count, 2)

    def test_action_skip_on_already_skipped_returns_warning(self):
        """action_skip on a skipped article should return a warning notification."""
        article = self._create_article(state="skipped", active=False)
        result = article.action_skip()
        self.assertEqual(result["params"]["type"], "warning")

    def test_action_reset_clears_error_fields(self):
        """action_reset should reset to 'pending', clear error fields, and unarchive."""
        article = self._create_article(
            state="skipped",
            status_message="Some error",
            retry_count=5,
            active=False,
        )

        article.action_reset()

        self.assertEqual(article.state, "pending")
        self.assertTrue(article.active)
        self.assertFalse(article.status_message)
        self.assertFalse(article.last_error_date)
        self.assertEqual(article.retry_count, 0)

    def test_action_re_extract_requires_snapshot(self):
        """action_re_extract on article without snapshot returns warning."""
        article = self._create_article()
        # Forcibly unlink snapshot to simulate edge case
        article.write({"snapshot_id": False})
        result = article.action_re_extract()
        self.assertEqual(result["params"]["type"], "warning")

    def test_job_count_zero_for_new_article(self):
        """New article should have zero job count (no jobs in test context)."""
        article = self._create_article()
        self.assertEqual(article.job_count, 0)

    def test_action_view_jobs_returns_window_action(self):
        """action_view_jobs should return a window action for queue.job."""
        article = self._create_article()
        action = article.action_view_jobs()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "queue.job")
