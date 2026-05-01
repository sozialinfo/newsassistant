"""Tests for newsassistant res.config.settings extension."""
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCoreConfigSettings(TransactionCase):
    """Tests for newsassistant res.config.settings extension."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, queue_job__no_delay=True))
        cls.stage_new = cls.env.ref("newsassistant.news_article_stage_new")
        cls.stage_shortlist = cls.env.ref("newsassistant.news_article_stage_shortlist")
        cls.source = cls.env["news.source"].create({
            "name": "Config Test Source",
            "source_type": "website",
            "url": "https://config-test.example.com/news",
        })
        cls.snapshot = cls.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": cls.source.id,
            "raw_content": "<p>Content</p>",
        })

    def _get_settings(self):
        return self.env["res.config.settings"].create({})

    def test_get_values_returns_default_stage_when_unset(self):
        """get_values returns False for new article stage when param not set."""
        self.env["ir.config_parameter"].sudo().set_param(
            "newsassistant.new_article_stage_id", ""
        )
        settings = self._get_settings()
        values = settings.get_values()
        self.assertFalse(values.get("newsassistant_new_article_stage_id"))

    def test_set_values_writes_config_parameter(self):
        """set_values stores the stage ID in ir.config_parameter."""
        settings = self._get_settings()
        settings.newsassistant_new_article_stage_id = self.stage_shortlist
        settings.set_values()

        param = self.env["ir.config_parameter"].sudo().get_param(
            "newsassistant.new_article_stage_id"
        )
        self.assertEqual(param, str(self.stage_shortlist.id))

    def test_get_values_reads_configured_stage(self):
        """get_values returns the configured stage."""
        self.env["ir.config_parameter"].sudo().set_param(
            "newsassistant.new_article_stage_id", str(self.stage_shortlist.id)
        )
        settings = self._get_settings()
        self.assertEqual(
            settings.newsassistant_new_article_stage_id.id,
            self.stage_shortlist.id,
        )

    def test_default_stage_id_uses_config_parameter(self):
        """_default_stage_id() returns the stage from ir.config_parameter."""
        self.env["ir.config_parameter"].sudo().set_param(
            "newsassistant.new_article_stage_id", str(self.stage_shortlist.id)
        )
        default_stage = self.env["news.article"]._default_stage_id()
        self.assertEqual(default_stage, self.stage_shortlist)

    def test_default_stage_id_falls_back_to_new_when_unset(self):
        """_default_stage_id() falls back to 'New' stage when param is unset."""
        self.env["ir.config_parameter"].sudo().set_param(
            "newsassistant.new_article_stage_id", ""
        )
        default_stage = self.env["news.article"]._default_stage_id()
        self.assertEqual(default_stage, self.stage_new)

    def test_default_stage_id_falls_back_when_invalid_id(self):
        """_default_stage_id() falls back to 'New' when param holds invalid ID."""
        self.env["ir.config_parameter"].sudo().set_param(
            "newsassistant.new_article_stage_id", "999999"
        )
        default_stage = self.env["news.article"]._default_stage_id()
        self.assertEqual(default_stage, self.stage_new)

    def test_new_article_uses_configured_default_stage(self):
        """Articles created without explicit stage use the configured default."""
        self.env["ir.config_parameter"].sudo().set_param(
            "newsassistant.new_article_stage_id", str(self.stage_shortlist.id)
        )
        article = self.env["news.article"].create({
            "title": "Config Default Stage Test",
            "snapshot_id": self.snapshot.id,
            "url": "https://config-test.example.com/article-config-1",
        })
        self.assertEqual(article.stage_id, self.stage_shortlist)
        self.env["ir.config_parameter"].sudo().set_param(
            "newsassistant.new_article_stage_id", ""
        )
