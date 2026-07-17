"""Tests for snapshot-based article extraction pipeline."""
import json
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.queue_job.tests.common import trap_jobs
from odoo.addons.newsassistant_website.models.news_source_website import NewsSnapshotWebsite


HTML_ARTICLE_CONTENT = """
<article>
  <h1>Full Article Title</h1>
  <p>Published: 2025-03-15</p>
  <p>This is the first paragraph of the article.</p>
  <p>This is the second paragraph with more details.</p>
</article>
"""

AI_ARTICLE_RESPONSE = json.dumps({
    "is_article": True,
    "title": "Full Article Title",
    "date": "2025-03-15",
    "summary": "This article covers important topics. It has two paragraphs.",
    "content": "<p>This is the first paragraph of the article.</p><p>This is the second paragraph with more details.</p>",
})

AI_NOT_ARTICLE_RESPONSE = json.dumps({
    "is_article": False,
    "reason": "This is a listing page showing multiple articles",
})


def _make_mock_response(status_code=200, json_data=None):
    response = MagicMock()
    response.status_code = status_code
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
class TestSnapshotExtraction(TransactionCase):
    """Tests for news.snapshot._extract_articles() in the base module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, queue_job__no_delay=True))
        cls.source = cls.env["news.source"].create({
            "name": "Test Source",
            "source_type": "website",
            "url": "https://example.com/news",
        })

    def _create_snapshot(self, content=None):
        """Helper: create a snapshot without triggering extraction job."""
        return self.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": self.source.id,
            "raw_content": content or HTML_ARTICLE_CONTENT,
        })

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    def test_extract_articles_creates_article(self, mock_post):
        """Snapshot extraction should create a news.article record."""
        mock_post.return_value = _make_mock_response(200, json_data=_make_ai_response(AI_ARTICLE_RESPONSE))

        snapshot = self._create_snapshot()
        # Manually call to avoid queue_job delay
        snapshot._extract_articles()

        articles = self.env["news.article"].search([("snapshot_id", "=", snapshot.id)])
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles.title, "Full Article Title")
        self.assertEqual(str(articles.date), "2025-03-15")
        self.assertEqual(articles.state, "scraped")
        self.assertIn("important topics", articles.summary)

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    def test_extract_not_article_creates_no_article(self, mock_post):
        """When AI says not an article, no news.article should be created."""
        mock_post.return_value = _make_mock_response(200, json_data=_make_ai_response(AI_NOT_ARTICLE_RESPONSE))

        snapshot = self._create_snapshot()
        snapshot._extract_articles()

        articles = self.env["news.article"].search([("snapshot_id", "=", snapshot.id)])
        self.assertEqual(len(articles), 0)

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    def test_extract_creates_log_on_success(self, mock_post):
        """Successful extraction should create a news.log record."""
        mock_post.return_value = _make_mock_response(200, json_data=_make_ai_response(AI_ARTICLE_RESPONSE))

        snapshot = self._create_snapshot()
        snapshot._extract_articles()

        logs = self.env["news.log"].search([
            ("snapshot_id", "=", snapshot.id),
            ("category", "=", "extraction"),
        ])
        self.assertTrue(len(logs) >= 1)
        self.assertEqual(logs[0].level, "success")

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    def test_extract_creates_log_on_not_article(self, mock_post):
        """Not-an-article response should create a warning log."""
        mock_post.return_value = _make_mock_response(200, json_data=_make_ai_response(AI_NOT_ARTICLE_RESPONSE))

        snapshot = self._create_snapshot()
        snapshot._extract_articles()

        logs = self.env["news.log"].search([
            ("snapshot_id", "=", snapshot.id),
            ("category", "=", "extraction"),
        ])
        self.assertTrue(len(logs) >= 1)
        self.assertEqual(logs[0].level, "warning")

    def test_extract_empty_content_creates_warning_log(self):
        """Empty snapshot content should create a warning log."""
        snapshot = self.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": self.source.id,
            "raw_content": "",
        })
        snapshot._extract_articles()

        logs = self.env["news.log"].search([
            ("snapshot_id", "=", snapshot.id),
            ("category", "=", "extraction"),
        ])
        self.assertTrue(len(logs) >= 1)
        self.assertEqual(logs[0].level, "warning")

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    def test_extract_malformed_ai_response_creates_error_log(self, mock_post):
        """Malformed AI response should create an error log."""
        mock_post.return_value = _make_mock_response(200, json_data=_make_ai_response("not valid json"))

        snapshot = self._create_snapshot()
        snapshot._extract_articles()

        logs = self.env["news.log"].search([
            ("snapshot_id", "=", snapshot.id),
            ("category", "=", "extraction"),
        ])
        self.assertTrue(len(logs) >= 1)
        self.assertEqual(logs[0].level, "error")

    def test_snapshot_create_enqueues_extract_job(self):
        """Non-listing snapshot creation should enqueue _extract_articles job."""
        plain_env = self.env(context={k: v for k, v in self.env.context.items() if k != "queue_job__no_delay"})
        with trap_jobs() as trap:
            plain_env["news.snapshot"].create({
                "source_id": self.source.id,
                "raw_content": HTML_ARTICLE_CONTENT,
            })
            trap.assert_jobs_count(1)
            job = trap.enqueued_jobs[0]
            self.assertEqual(job.method_name, "_extract_articles")

    def test_listing_snapshot_create_enqueues_discover_job(self):
        """Listing snapshot creation should enqueue _discover_articles job."""
        plain_env = self.env(context={k: v for k, v in self.env.context.items() if k != "queue_job__no_delay"})
        with trap_jobs() as trap:
            plain_env["news.snapshot"].create({
                "source_id": self.source.id,
                "raw_content": "<p>listing content</p>",
                "is_listing": True,
            })
            trap.assert_jobs_count(1)
            job = trap.enqueued_jobs[0]
            self.assertEqual(job.method_name, "_discover_articles")

    def test_listing_snapshot_has_is_listing_flag(self):
        """Listing snapshot should have is_listing=True."""
        snapshot = self.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": self.source.id,
            "raw_content": "<p>listing</p>",
            "is_listing": True,
        })
        self.assertTrue(snapshot.is_listing)
        self.assertFalse(snapshot.parent_id)

    def test_child_snapshot_links_to_parent(self):
        """Child snapshot should have parent_id pointing to parent."""
        parent = self.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": self.source.id,
            "raw_content": "<p>parent</p>",
            "is_listing": True,
        })
        child = self.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": self.source.id,
            "raw_content": "<p>child</p>",
            "parent_id": parent.id,
        })
        self.assertTrue(child.parent_id, parent.id)
        self.assertIn(child, parent.child_ids)

    @patch.object(NewsSnapshotWebsite, '_discover_articles_website',
                   side_effect=NotImplementedError("Test: no website handler"))
    def test_base_discover_articles_raises_not_implemented(self, mock_discover):
        """Base _discover_articles should raise NotImplementedError when no handler exists."""
        snapshot = self._create_snapshot(content="<p>test</p>")
        with self.assertRaises(NotImplementedError):
            snapshot._discover_articles()

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    def test_extracted_article_source_id_is_computed(self, mock_post):
        """Article source_id should be computed from snapshot.source_id."""
        mock_post.return_value = _make_mock_response(200, json_data=_make_ai_response(AI_ARTICLE_RESPONSE))

        snapshot = self._create_snapshot()
        snapshot._extract_articles()

        article = self.env["news.article"].search([("snapshot_id", "=", snapshot.id)], limit=1)
        self.assertTrue(article)
        self.assertEqual(article.source_id, self.source)

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    def test_snapshot_computed_name(self, mock_post):
        """Snapshot name should include source name."""
        snapshot = self._create_snapshot()
        self.assertIn(self.source.name, snapshot.name)

    @patch("odoo.addons.newsassistant.models.news_source.requests.post")
    def test_ai_response_with_markdown_fences(self, mock_post):
        """AI response with markdown fences should still be parsed correctly."""
        fenced = f"```json\n{AI_ARTICLE_RESPONSE}\n```"
        mock_post.return_value = _make_mock_response(200, json_data=_make_ai_response(fenced))

        snapshot = self._create_snapshot()
        snapshot._extract_articles()

        articles = self.env["news.article"].search([("snapshot_id", "=", snapshot.id)])
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles.title, "Full Article Title")
