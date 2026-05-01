from odoo.tests.common import TransactionCase, tagged

from odoo.addons.newsassistant_blog.hooks import post_init_hook


@tagged("post_install", "-at_install")
class TestPostInitHook(TransactionCase):
    """Tests for newsassistant_blog post_init_hook."""

    def _clear_params(self):
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("newsassistant_blog.shortlist_stage_id", "")
        ICP.set_param("newsassistant_blog.published_stage_id", "")
        ICP.set_param("newsassistant_blog.discard_stage_id", "")
        ICP.set_param("newsassistant_blog.blog_id", "")

    def test_hook_links_existing_stages(self):
        """Hook finds and links existing Shortlist, Published, Discarded stages."""
        self._clear_params()
        stage_shortlist = self.env.ref("newsassistant.news_article_stage_shortlist")
        stage_published = self.env.ref("newsassistant.news_article_stage_published")
        stage_discarded = self.env.ref("newsassistant.news_article_stage_discarded")

        post_init_hook(self.env)

        ICP = self.env["ir.config_parameter"].sudo()
        self.assertEqual(
            ICP.get_param("newsassistant_blog.shortlist_stage_id"),
            str(stage_shortlist.id),
        )
        self.assertEqual(
            ICP.get_param("newsassistant_blog.published_stage_id"),
            str(stage_published.id),
        )
        self.assertEqual(
            ICP.get_param("newsassistant_blog.discard_stage_id"),
            str(stage_discarded.id),
        )

    def test_hook_creates_missing_stages(self):
        """Hook creates stages that don't exist yet."""
        self._clear_params()
        # Delete the standard stages to simulate missing state
        self.env["news.article.stage"].search([
            ("name", "in", ["Shortlist", "Published", "Discarded"])
        ]).unlink()

        post_init_hook(self.env)

        ICP = self.env["ir.config_parameter"].sudo()

        shortlist_id = ICP.get_param("newsassistant_blog.shortlist_stage_id")
        self.assertTrue(shortlist_id)
        shortlist = self.env["news.article.stage"].browse(int(shortlist_id))
        self.assertTrue(shortlist.exists())
        self.assertEqual(shortlist.name, "Shortlist")
        self.assertFalse(shortlist.fold)

        published_id = ICP.get_param("newsassistant_blog.published_stage_id")
        self.assertTrue(published_id)
        published = self.env["news.article.stage"].browse(int(published_id))
        self.assertTrue(published.exists())
        self.assertEqual(published.name, "Published")
        self.assertTrue(published.fold)

        discarded_id = ICP.get_param("newsassistant_blog.discard_stage_id")
        self.assertTrue(discarded_id)
        discarded = self.env["news.article.stage"].browse(int(discarded_id))
        self.assertTrue(discarded.exists())
        self.assertEqual(discarded.name, "Discarded")

    def test_hook_links_existing_news_blog(self):
        """Hook links an existing 'News' blog."""
        self._clear_params()
        # Remove any pre-existing News blogs (created by earlier tests/install hook)
        self.env["blog.blog"].search([("name", "=", "News")]).unlink()
        blog = self.env["blog.blog"].create({"name": "News"})

        post_init_hook(self.env)

        ICP = self.env["ir.config_parameter"].sudo()
        self.assertEqual(ICP.get_param("newsassistant_blog.blog_id"), str(blog.id))

    def test_hook_creates_news_blog_when_missing(self):
        """Hook creates a 'News' blog when none exists."""
        self._clear_params()
        # Remove any existing News blog
        self.env["blog.blog"].search([("name", "=", "News")]).unlink()

        post_init_hook(self.env)

        ICP = self.env["ir.config_parameter"].sudo()
        blog_id = ICP.get_param("newsassistant_blog.blog_id")
        self.assertTrue(blog_id)
        blog = self.env["blog.blog"].browse(int(blog_id))
        self.assertTrue(blog.exists())
        self.assertEqual(blog.name, "News")

    def test_hook_does_not_duplicate_stages(self):
        """Hook called twice does not create duplicate stages."""
        self._clear_params()
        post_init_hook(self.env)
        post_init_hook(self.env)

        shortlist_count = self.env["news.article.stage"].search_count([
            ("name", "=", "Shortlist")
        ])
        self.assertEqual(shortlist_count, 1)

    def test_hook_does_not_duplicate_blog(self):
        """Hook called twice does not create duplicate News blogs."""
        self._clear_params()
        self.env["blog.blog"].search([("name", "=", "News")]).unlink()

        post_init_hook(self.env)
        post_init_hook(self.env)

        news_blog_count = self.env["blog.blog"].search_count([("name", "=", "News")])
        self.assertEqual(news_blog_count, 1)
