from odoo import fields, models


class NewsSourceLog(models.Model):
    _name = "news.source.log"
    _description = "News Source Scrape Log"
    _order = "timestamp desc"

    source_id = fields.Many2one(
        "news.source",
        required=True,
        ondelete="cascade",
        index=True,
    )
    timestamp = fields.Datetime(required=True, default=fields.Datetime.now)
    status = fields.Selection(
        [("success", "Success"), ("error", "Error")],
        required=True,
    )
    duration = fields.Float(string="Duration (s)", digits=(10, 2))
    articles_found = fields.Integer(default=0)
    error_message = fields.Text()
    job_id = fields.Many2one(
        "queue.job",
        string="Job",
        ondelete="set null",
        index=True,
    )

    def action_view_job(self):
        """Open the linked queue.job record."""
        self.ensure_one()
        if not self.job_id:
            return
        return {
            "type": "ir.actions.act_window",
            "res_model": "queue.job",
            "res_id": self.job_id.id,
            "view_mode": "form",
            "target": "current",
        }
