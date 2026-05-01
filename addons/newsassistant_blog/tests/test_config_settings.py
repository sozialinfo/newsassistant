from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestBlogConfigSettings(TransactionCase):
    """Tests for newsassistant_blog res.config.settings stage fields."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stage_shortlist = cls.env.ref("newsassistant.news_article_stage_shortlist")
        cls.stage_published = cls.env.ref("newsassistant.news_article_stage_published")
        cls.stage_discarded = cls.env.ref("newsassistant.news_article_stage_discarded")
        cls.blog = cls.env["blog.blog"].create({"name": "Settings Test Blog"})

    def _get_settings(self):
        return self.env["res.config.settings"].create({})

    def _clear_stage_params(self):
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("newsassistant_blog.shortlist_stage_id", "")
        ICP.set_param("newsassistant_blog.published_stage_id", "")
        ICP.set_param("newsassistant_blog.discard_stage_id", "")

    def test_set_values_writes_stage_params(self):
        """set_values stores all three stage IDs in ir.config_parameter."""
        settings = self._get_settings()
        settings.newsassistant_blog_shortlist_stage_id = self.stage_shortlist
        settings.newsassistant_blog_published_stage_id = self.stage_published
        settings.newsassistant_blog_discard_stage_id = self.stage_discarded
        settings.set_values()

        ICP = self.env["ir.config_parameter"].sudo()
        self.assertEqual(
            ICP.get_param("newsassistant_blog.shortlist_stage_id"),
            str(self.stage_shortlist.id),
        )
        self.assertEqual(
            ICP.get_param("newsassistant_blog.published_stage_id"),
            str(self.stage_published.id),
        )
        self.assertEqual(
            ICP.get_param("newsassistant_blog.discard_stage_id"),
            str(self.stage_discarded.id),
        )

    def test_get_values_reads_configured_stages(self):
        """get_values returns the configured stage IDs."""
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("newsassistant_blog.shortlist_stage_id", str(self.stage_shortlist.id))
        ICP.set_param("newsassistant_blog.published_stage_id", str(self.stage_published.id))
        ICP.set_param("newsassistant_blog.discard_stage_id", str(self.stage_discarded.id))

        settings = self._get_settings()
        values = settings.get_values()

        self.assertEqual(values["newsassistant_blog_shortlist_stage_id"], self.stage_shortlist.id)
        self.assertEqual(values["newsassistant_blog_published_stage_id"], self.stage_published.id)
        self.assertEqual(values["newsassistant_blog_discard_stage_id"], self.stage_discarded.id)

    def test_get_values_returns_falsy_when_unset(self):
        """get_values returns falsy for stage fields when params are empty."""
        self._clear_stage_params()
        settings = self._get_settings()
        values = settings.get_values()
        self.assertFalse(values.get("newsassistant_blog_shortlist_stage_id"))
        self.assertFalse(values.get("newsassistant_blog_published_stage_id"))
        self.assertFalse(values.get("newsassistant_blog_discard_stage_id"))

    def test_set_values_clears_params_when_stage_empty(self):
        """set_values writes empty string when stage field is empty."""
        # First set a value
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("newsassistant_blog.shortlist_stage_id", str(self.stage_shortlist.id))

        # Then clear it via settings
        settings = self._get_settings()
        settings.newsassistant_blog_shortlist_stage_id = False
        settings.set_values()

        # get_param returns False if param doesn't exist, or "" if it was cleared
        param_value = ICP.get_param("newsassistant_blog.shortlist_stage_id")
        self.assertFalse(param_value)
