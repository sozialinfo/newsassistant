from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    newsassistant_crawl4ai_url = fields.Char(
        string="crawl4ai Server URL",
        default="http://crawl4ai:11235",
        help="URL of the self-hosted crawl4ai server. Default: http://crawl4ai:11235",
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        ICP = self.env["ir.config_parameter"].sudo()
        res["newsassistant_crawl4ai_url"] = ICP.get_param(
            "newsassistant_website.crawl4ai_url",
            default="http://crawl4ai:11235",
        )
        return res

    def set_values(self):
        super().set_values()
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param(
            "newsassistant_website.crawl4ai_url",
            self.newsassistant_crawl4ai_url or "http://crawl4ai:11235",
        )
