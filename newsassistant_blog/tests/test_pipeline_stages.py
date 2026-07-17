from unittest.mock import patch
import time

from odoo import fields as odoo_fields
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPipelineStages(TransactionCase):
    """Tests for settings-driven pipeline stage routing."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, queue_job__no_delay=True))
        cls.stage_new = cls.env.ref("newsassistant.news_article_stage_new")
        cls.stage_shortlist = cls.env.ref("newsassistant.news_article_stage_shortlist")
        cls.stage_published = cls.env.ref("newsassistant.news_article_stage_published")
        cls.stage_discarded = cls.env.ref("newsassistant.news_article_stage_discarded")
        cls.source = cls.env["news.source"].create({
            "name": "Pipeline Stage Test Source",
            "source_type": "website",
            "url": "https://pipeline-test.example.com/news",
        })
        cls.snapshot = cls.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": cls.source.id,
            "raw_content": "<p>Content</p>",
        })
        cls.blog = cls.env["blog.blog"].create({"name": "Pipeline Test Blog"})

    def _set_params(self, shortlist=None, published=None, discard=None, blog=None):
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param(
            "newsassistant_blog.shortlist_stage_id",
            str(shortlist.id) if shortlist else "",
        )
        ICP.set_param(
            "newsassistant_blog.published_stage_id",
            str(published.id) if published else "",
        )
        ICP.set_param(
            "newsassistant_blog.discard_stage_id",
            str(discard.id) if discard else "",
        )
        if blog is not None:
            ICP.set_param("newsassistant_blog.blog_id", str(blog.id) if blog else "")

    def _create_article(self, url_suffix=""):
        return self.env["news.article"].create({
            "title": f"Test Article {url_suffix}",
            "snapshot_id": self.snapshot.id,
            "url": f"https://pipeline-test.example.com/article-{url_suffix}",
            "state": "scraped",
            "summary": "Test summary.",
            "content": "<p>Test content.</p>",
        })

    def _add_entry(self, entries, level, message, **kwargs):
        entries.append({"level": level, "message": message, **kwargs})

    # --- _get_pipeline_stage ---

    def test_get_pipeline_stage_from_param(self):
        """_get_pipeline_stage reads stage from ir.config_parameter."""
        self._set_params(shortlist=self.stage_shortlist)
        article = self._create_article("gps-1")
        stage = article._get_pipeline_stage(
            "newsassistant_blog.shortlist_stage_id", "Shortlist"
        )
        self.assertEqual(stage, self.stage_shortlist)

    def test_get_pipeline_stage_fallback_by_name(self):
        """_get_pipeline_stage falls back to name search when param is empty."""
        self.env["ir.config_parameter"].sudo().set_param(
            "newsassistant_blog.shortlist_stage_id", ""
        )
        article = self._create_article("gps-2")
        stage = article._get_pipeline_stage(
            "newsassistant_blog.shortlist_stage_id", "Shortlist"
        )
        self.assertEqual(stage, self.stage_shortlist)

    def test_get_pipeline_stage_invalid_id_falls_back(self):
        """_get_pipeline_stage falls back by name when param holds an invalid ID."""
        self.env["ir.config_parameter"].sudo().set_param(
            "newsassistant_blog.shortlist_stage_id", "999999"
        )
        article = self._create_article("gps-3")
        stage = article._get_pipeline_stage(
            "newsassistant_blog.shortlist_stage_id", "Shortlist"
        )
        self.assertEqual(stage, self.stage_shortlist)

    # --- _handle_discard ---

    def test_handle_discard_moves_to_configured_stage(self):
        """_handle_discard() moves article to configured discard stage."""
        self._set_params(discard=self.stage_discarded)
        article = self._create_article("hd-1")
        entries = []
        article._handle_discard("Not relevant", entries, lambda l, m, **k: entries.append(m))
        self.assertEqual(article.stage_id, self.stage_discarded)

    def test_handle_discard_falls_back_by_name(self):
        """_handle_discard() falls back to 'Discarded' by name when param is unset."""
        self.env["ir.config_parameter"].sudo().set_param(
            "newsassistant_blog.discard_stage_id", ""
        )
        article = self._create_article("hd-2")
        entries = []
        article._handle_discard("Not relevant", entries, lambda l, m, **k: entries.append(m))
        self.assertEqual(article.stage_id, self.stage_discarded)

    # --- _handle_shortlist ---

    def test_handle_shortlist_moves_to_configured_stage(self):
        """_handle_shortlist() moves article to published stage via blog post creation."""
        self._set_params(
            shortlist=self.stage_shortlist,
            published=self.stage_published,
            blog=self.blog,
        )
        article = self._create_article("hs-1")
        entries = []

        def add(level, message, duration=None, metadata=None):
            entries.append({
                "timestamp": odoo_fields.Datetime.now(),
                "level": level,
                "message": message,
                "duration": duration,
                "metadata": metadata,
            })

        mock_ai_result = {
            "content": '{"teaser": "A compelling teaser.", "read_more": "Read more at example.com"}',
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            "duration_ms": 50,
        }
        with patch.object(type(article), '_call_ai', return_value=mock_ai_result):
            article._handle_shortlist("Very relevant", entries, add, job_id=None, start_time=time.time())

        self.assertEqual(article.stage_id, self.stage_published)
        self.assertEqual(article.blog_reasoning, "Very relevant")

    # --- _create_blog_post stage update ---

    def test_create_blog_post_moves_to_published_stage(self):
        """_create_blog_post() moves article to configured published stage."""
        self._set_params(
            shortlist=self.stage_shortlist,
            published=self.stage_published,
            discard=self.stage_discarded,
            blog=self.blog,
        )
        article = self._create_article("cbp-1")
        entries = []

        def add(l, m, **k):
            entries.append(m)

        post = article._create_blog_post("Test teaser.", entries, add)
        self.assertIsNotNone(post)
        self.assertEqual(article.stage_id, self.stage_published)

    def test_create_blog_post_falls_back_published_by_name(self):
        """_create_blog_post() falls back to 'Published' by name when param is unset."""
        self._set_params(blog=self.blog)
        self.env["ir.config_parameter"].sudo().set_param(
            "newsassistant_blog.published_stage_id", ""
        )
        article = self._create_article("cbp-2")
        entries = []

        def add(l, m, **k):
            entries.append(m)

        post = article._create_blog_post("Test teaser.", entries, add)
        self.assertIsNotNone(post)
        self.assertEqual(article.stage_id, self.stage_published)
