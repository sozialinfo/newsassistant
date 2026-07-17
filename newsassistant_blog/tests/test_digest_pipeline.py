"""Tests for the digest pipeline: relevance evaluation and blog post creation."""
import json
from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError
from odoo.addons.queue_job.tests.common import trap_jobs


@tagged("post_install", "-at_install")
class TestDigestPipeline(TransactionCase):
    """Tests for article digest AI pipeline with mocked AI calls."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, queue_job__no_delay=True))
        cls.stage_new = cls.env.ref("newsassistant.news_article_stage_new")
        cls.stage_shortlist = cls.env.ref("newsassistant.news_article_stage_shortlist")
        cls.stage_published = cls.env.ref("newsassistant.news_article_stage_published")
        cls.stage_discarded = cls.env.ref("newsassistant.news_article_stage_discarded")
        cls.source = cls.env["news.source"].create({
            "name": "Digest Pipeline Source",
            "source_type": "website",
            "url": "https://digest-test.example.com",
        })
        cls.snapshot = cls.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": cls.source.id,
            "raw_content": "<p>Test content</p>",
        })
        cls.blog = cls.env["blog.blog"].create({"name": "Digest Test Blog"})
        ICP = cls.env["ir.config_parameter"].sudo()
        ICP.set_param("newsassistant_blog.blog_id", str(cls.blog.id))
        ICP.set_param("newsassistant_blog.content_strategy", "Focus on technology news.")
        ICP.set_param("newsassistant_blog.teaser_prompt", "Write a 2-sentence teaser.")
        ICP.set_param("newsassistant_blog.shortlist_stage_id", str(cls.stage_shortlist.id))
        ICP.set_param("newsassistant_blog.published_stage_id", str(cls.stage_published.id))
        ICP.set_param("newsassistant_blog.discard_stage_id", str(cls.stage_discarded.id))

    def _create_article(self, suffix=""):
        return self.env["news.article"].create({
            "title": f"Digest Test Article {suffix}",
            "snapshot_id": self.snapshot.id,
            "url": f"https://digest-test.example.com/article-{suffix}",
            "state": "scraped",
            "summary": "Test summary.",
            "content": "<p>Test article content.</p>",
        })

    def _mock_ai(self, response_dict):
        """Return a mock AI result for a given response dict."""
        return {
            "content": json.dumps(response_dict),
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            "request": {"model": "qwen3", "temperature": 0.1, "system_prompt": "", "user_content": ""},
            "response": {"content": json.dumps(response_dict), "status_code": 200},
            "duration_ms": 100,
        }

    def test_evaluate_relevance_relevant(self):
        """_evaluate_relevance should return 'relevant' when AI says so."""
        article = self._create_article("rel-1")
        log_entries = []

        def add(level, message, **kwargs):
            log_entries.append({"level": level, "message": message, **kwargs})

        with patch.object(type(article), "_call_ai",
                          return_value=self._mock_ai({"decision": "relevant", "reasoning": "Good article"})):
            decision, reasoning = article._evaluate_relevance("strategy", log_entries, add)

        self.assertEqual(decision, "relevant")
        self.assertEqual(reasoning, "Good article")

    def test_evaluate_relevance_discard(self):
        """_evaluate_relevance should return 'discard' when AI says so."""
        article = self._create_article("dis-1")
        log_entries = []
        add = lambda l, m, **k: log_entries.append(m)

        with patch.object(type(article), "_call_ai",
                          return_value=self._mock_ai({"decision": "discard", "reasoning": "Not relevant"})):
            decision, reasoning = article._evaluate_relevance("strategy", log_entries, add)

        self.assertEqual(decision, "discard")

    def test_evaluate_relevance_uncertain(self):
        """_evaluate_relevance should return 'uncertain' when AI says so."""
        article = self._create_article("unc-1")
        log_entries = []
        add = lambda l, m, **k: log_entries.append(m)

        with patch.object(type(article), "_call_ai",
                          return_value=self._mock_ai({"decision": "uncertain", "reasoning": "Maybe"})):
            decision, reasoning = article._evaluate_relevance("strategy", log_entries, add)

        self.assertEqual(decision, "uncertain")

    def test_handle_discard_sets_stage(self):
        """_handle_discard should move article to discard stage."""
        article = self._create_article("dis-2")
        log_entries = []
        add = lambda l, m, **k: log_entries.append(m)
        article._handle_discard("Not relevant", log_entries, add)
        self.assertEqual(article.stage_id, self.stage_discarded)

    def test_handle_uncertain_leaves_in_new(self):
        """_handle_uncertain should leave article in its current stage."""
        article = self._create_article("unc-2")
        original_stage = article.stage_id
        log_entries = []
        add = lambda l, m, **k: log_entries.append(m)
        article._handle_uncertain("Maybe useful", log_entries, add)
        self.assertEqual(article.stage_id, original_stage)

    def test_generate_teaser_success(self):
        """_generate_teaser should store teaser on success and return dict."""
        article = self._create_article("teas-1")
        log_entries = []
        add = lambda l, m, **k: log_entries.append(m)

        mock_result = self._mock_ai({
            "teaser": "A compelling two-sentence teaser for this article.",
            "read_more": "Ganzen Artikel lesen bei digest-test.example.com",
        })

        with patch.object(type(article), "_call_ai", return_value=mock_result):
            result = article._generate_teaser(log_entries, add)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["teaser"], "A compelling two-sentence teaser for this article.")
        self.assertEqual(result["read_more"], "Ganzen Artikel lesen bei digest-test.example.com")
        self.assertEqual(article.teaser, result["teaser"])

    def test_create_blog_post_success(self):
        """_create_blog_post should create a blog post with language-aware link text."""
        article = self._create_article("blog-1")
        log_entries = []
        add = lambda l, m, **k: log_entries.append(m)

        teaser_result = {
            "teaser": "A great teaser!",
            "read_more": "Ganzen Artikel lesen bei digest-test.example.com",
        }
        post = article._create_blog_post(teaser_result, log_entries, add)
        self.assertIsNotNone(post)
        self.assertEqual(post.blog_id, self.blog)
        self.assertEqual(post.news_article_id, article)
        self.assertIn("Ganzen Artikel lesen", post.content)

    def test_create_blog_post_deduplication(self):
        """Creating blog post twice should return existing post."""
        article = self._create_article("blog-2")
        log_entries = []
        add = lambda l, m, **k: log_entries.append(m)

        post1 = article._create_blog_post("Teaser 1", log_entries, add)
        post2 = article._create_blog_post("Teaser 2", log_entries, add)
        self.assertEqual(post1, post2)

    def test_cron_digest_all_impl_queues_jobs(self):
        """_cron_digest_all_impl should queue jobs for pending articles."""
        article = self._create_article("cron-1")
        article.write({"state": "scraped", "digest_state": "pending"})

        # Use trap_jobs without queue_job__no_delay to intercept without executing
        plain_env = self.env(context={k: v for k, v in self.env.context.items()
                                       if k != "queue_job__no_delay"})
        with trap_jobs() as trap:
            count = plain_env["news.article"]._cron_digest_all_impl()

        self.assertGreaterEqual(count, 1)
        extract_jobs = [j for j in trap.enqueued_jobs if j.method_name == "_digest_article"]
        self.assertGreater(len(extract_jobs), 0)

    def test_digest_state_pending_by_default(self):
        """New articles should have digest_state 'pending'."""
        article = self._create_article("state-1")
        self.assertEqual(article.digest_state, "pending")

    def test_blog_post_count_compute(self):
        """blog_post_count should reflect linked blog posts."""
        article = self._create_article("count-1")
        self.assertEqual(article.blog_post_count, 0)

        log_entries = []
        add = lambda l, m, **k: log_entries.append(m)
        article._create_blog_post("Test teaser", log_entries, add)

        # Invalidate cache to trigger recompute
        article.invalidate_recordset(["blog_post_count"])
        self.assertEqual(article.blog_post_count, 1)

    def test_action_digest_now_not_scraped(self):
        """action_digest_now on non-scraped article should return warning."""
        article = self._create_article("warn-1")
        article.write({"state": "pending"})
        result = article.action_digest_now()
        self.assertEqual(result["params"]["type"], "warning")

    def test_action_digest_selected_no_scraped(self):
        """action_digest_selected with no scraped articles returns warning."""
        article = self._create_article("warn-2")
        article.write({"state": "pending"})
        result = article.action_digest_selected()
        self.assertEqual(result["params"]["type"], "warning")

    def test_action_view_blog_post_no_post(self):
        """action_view_blog_post with no post should return warning."""
        article = self._create_article("no-post-1")
        result = article.action_view_blog_post()
        self.assertEqual(result["params"]["type"], "warning")

    def test_action_view_blog_post_with_post(self):
        """action_view_blog_post with a post should return URL action."""
        article = self._create_article("has-post-1")
        log_entries = []
        add = lambda l, m, **k: log_entries.append(m)
        article._create_blog_post("A teaser", log_entries, add)
        result = article.action_view_blog_post()
        self.assertEqual(result["type"], "ir.actions.act_url")

    def test_get_content_strategy_raises_when_not_configured(self):
        """_get_content_strategy should raise UserError when not set."""
        self.env["ir.config_parameter"].sudo().set_param(
            "newsassistant_blog.content_strategy", ""
        )
        article = self._create_article("strategy-err")
        with self.assertRaises(UserError):
            article._get_content_strategy()
        # Restore
        self.env["ir.config_parameter"].sudo().set_param(
            "newsassistant_blog.content_strategy", "Focus on technology news."
        )
