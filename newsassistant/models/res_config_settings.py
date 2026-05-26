from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    newsassistant_new_article_stage_id = fields.Many2one(
        "news.article.stage",
        string="Default Stage for New Articles",
        config_parameter="newsassistant.new_article_stage_id",
        help="Stage assigned to newly created articles. Defaults to 'New' if not set.",
    )
    newsassistant_infomaniak_product_id = fields.Char(
        string="Infomaniak AI Product ID",
        config_parameter="newsassistant.infomaniak_product_id",
        help="Infomaniak AI product ID used for AI API calls. Default: 103794.",
    )
