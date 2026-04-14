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

    @api.model
    def get_values(self):
        res = super().get_values()
        ICP = self.env["ir.config_parameter"].sudo()
        
        res["newsfeed_content_strategy"] = ICP.get_param(
            "newsfeed.content_strategy", default=""
        )
        res["newsfeed_teaser_prompt"] = ICP.get_param(
            "newsfeed.teaser_prompt", default=""
        )
        
        blog_id_str = ICP.get_param("newsfeed.blog_id", default="")
        if blog_id_str:
            try:
                blog_id = int(blog_id_str)
                if self.env["blog.blog"].browse(blog_id).exists():
                    res["newsfeed_blog_id"] = blog_id
            except (ValueError, TypeError):
                pass
        
        res["newsfeed_pixabay_api_key"] = ICP.get_param(
            "newsfeed.pixabay_api_key", default=""
        )
        return res

    def set_values(self):
        super().set_values()
        ICP = self.env["ir.config_parameter"].sudo()
        
        ICP.set_param(
            "newsfeed.content_strategy",
            self.newsfeed_content_strategy or "",
        )
        ICP.set_param(
            "newsfeed.teaser_prompt",
            self.newsfeed_teaser_prompt or "",
        )
        ICP.set_param(
            "newsfeed.blog_id",
            str(self.newsfeed_blog_id.id) if self.newsfeed_blog_id else "",
        )
        ICP.set_param(
            "newsfeed.pixabay_api_key",
            self.newsfeed_pixabay_api_key or "",
        )
