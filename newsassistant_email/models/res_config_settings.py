"""Settings extension for newsassistant_email: email alias configuration."""
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    newsassistant_email_alias_name = fields.Char(
        string="Email Alias",
        help="The alias name for inbound newsletters (e.g. 'newsassistant' → newsassistant@yourdomain.com)",
        config_parameter="newsassistant_email.alias_name",
    )

    def set_values(self):
        super().set_values()
        alias_name = self.newsassistant_email_alias_name
        model = self.env["ir.model"]._get("news.snapshot")
        alias = self.env["mail.alias"].search(
            [("alias_model_id", "=", model.id)], limit=1
        )
        if alias and alias_name:
            alias.write({"alias_name": alias_name})

    @api.model
    def get_values(self):
        res = super().get_values()
        # Sync from the actual alias record if it exists
        model = self.env["ir.model"]._get("news.snapshot")
        if model:
            alias = self.env["mail.alias"].search(
                [("alias_model_id", "=", model.id)], limit=1
            )
            if alias and alias.alias_name:
                res["newsassistant_email_alias_name"] = alias.alias_name
        return res
