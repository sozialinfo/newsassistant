from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    newsfeed_content_strategy = fields.Text(
        string="Content Strategy",
        help="Prompt that defines relevance criteria for article triage. "
             "Should describe what makes an article 'relevant', 'uncertain', or 'discard'.",
    )
    newsfeed_teaser_prompt = fields.Text(
        string="Teaser Prompt",
        help="Prompt that defines how to generate teasers for relevant articles. "
             "Should describe the style, tone, and length of teasers.",
    )
    newsfeed_blog_id = fields.Many2one(
        "blog.blog",
        string="Target Blog",
        help="Blog where curated articles will be published.",
    )
    newsfeed_pixabay_api_key = fields.Char(
        string="Pixabay API Key",
        help="API key for Pixabay image service. Used as fallback when "
             "articles don't have suitable header images.",
    )
    newsassistant_blog_shortlist_stage_id = fields.Many2one(
        "news.article.stage",
        string="Shortlist Stage",
        help="Stage assigned to articles that need human review before publishing.",
    )
    newsassistant_blog_published_stage_id = fields.Many2one(
        "news.article.stage",
        string="Published Stage",
        help="Stage assigned to articles that have been auto-published to the blog.",
    )
    newsassistant_blog_discard_stage_id = fields.Many2one(
        "news.article.stage",
        string="Discard Stage",
        help="Stage assigned to articles that the pipeline has discarded as not relevant.",
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        ICP = self.env["ir.config_parameter"].sudo()

        res["newsfeed_content_strategy"] = ICP.get_param(
            "newsassistant_blog.content_strategy", default=""
        )
        res["newsfeed_teaser_prompt"] = ICP.get_param(
            "newsassistant_blog.teaser_prompt", default=""
        )

        blog_id_str = ICP.get_param("newsassistant_blog.blog_id", default="")
        if blog_id_str:
            try:
                blog_id = int(blog_id_str)
                if self.env["blog.blog"].browse(blog_id).exists():
                    res["newsfeed_blog_id"] = blog_id
            except (ValueError, TypeError):
                pass

        res["newsfeed_pixabay_api_key"] = ICP.get_param(
            "newsassistant_blog.pixabay_api_key", default=""
        )

        for field_name, param_key in [
            ("newsassistant_blog_shortlist_stage_id", "newsassistant_blog.shortlist_stage_id"),
            ("newsassistant_blog_published_stage_id", "newsassistant_blog.published_stage_id"),
            ("newsassistant_blog_discard_stage_id", "newsassistant_blog.discard_stage_id"),
        ]:
            stage_id_str = ICP.get_param(param_key, default="")
            if stage_id_str:
                try:
                    stage_id = int(stage_id_str)
                    if self.env["news.article.stage"].browse(stage_id).exists():
                        res[field_name] = stage_id
                except (ValueError, TypeError):
                    pass

        return res

    def set_values(self):
        super().set_values()
        ICP = self.env["ir.config_parameter"].sudo()

        ICP.set_param(
            "newsassistant_blog.content_strategy",
            self.newsfeed_content_strategy or "",
        )
        ICP.set_param(
            "newsassistant_blog.teaser_prompt",
            self.newsfeed_teaser_prompt or "",
        )
        ICP.set_param(
            "newsassistant_blog.blog_id",
            str(self.newsfeed_blog_id.id) if self.newsfeed_blog_id else "",
        )
        ICP.set_param(
            "newsassistant_blog.pixabay_api_key",
            self.newsfeed_pixabay_api_key or "",
        )

        for field_name, param_key in [
            ("newsassistant_blog_shortlist_stage_id", "newsassistant_blog.shortlist_stage_id"),
            ("newsassistant_blog_published_stage_id", "newsassistant_blog.published_stage_id"),
            ("newsassistant_blog_discard_stage_id", "newsassistant_blog.discard_stage_id"),
        ]:
            stage = getattr(self, field_name)
            ICP.set_param(param_key, str(stage.id) if stage else "")
