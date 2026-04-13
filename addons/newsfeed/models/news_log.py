from odoo import fields, models


class NewsLog(models.Model):
    _inherit = "news.log"

    # Extend the category selection to include 'digest'
    category = fields.Selection(
        selection_add=[
            ("digest", "Digest Processing"),
        ],
        ondelete={"digest": "cascade"},
    )
