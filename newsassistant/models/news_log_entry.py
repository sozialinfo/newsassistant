import json
from datetime import timedelta

from odoo import api, fields, models


class NewsLogEntry(models.Model):
    """Detail entry for a log record.

    Stores individual steps within an operation, including full LLM
    request/response data in the metadata JSON field.
    """

    _name = "news.log.entry"
    _description = "News Log Entry"
    _order = "timestamp asc"

    log_id = fields.Many2one(
        "news.log",
        required=True,
        ondelete="cascade",
        index=True,
    )
    timestamp = fields.Datetime(
        required=True,
        default=fields.Datetime.now,
    )
    level = fields.Selection(
        [
            ("debug", "Debug"),
            ("info", "Info"),
            ("warning", "Warning"),
            ("error", "Error"),
        ],
        required=True,
    )
    message = fields.Char(required=True)
    duration = fields.Float(string="Duration (s)")

    # JSON field for structured data (LLM prompts, responses, token counts, etc.)
    metadata = fields.Text(string="Metadata (JSON)")

    # Computed field for display
    metadata_pretty = fields.Text(
        compute="_compute_metadata_pretty",
        string="Metadata",
    )

    def _compute_metadata_pretty(self):
        """Format metadata JSON for display."""
        for entry in self:
            if entry.metadata:
                try:
                    data = json.loads(entry.metadata)
                    entry.metadata_pretty = json.dumps(data, indent=2, ensure_ascii=False)
                except (json.JSONDecodeError, TypeError):
                    entry.metadata_pretty = entry.metadata
            else:
                entry.metadata_pretty = ""

    def action_view_metadata(self):
        """Open a popup form to view the full metadata."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"Log Entry: {self.message[:50]}",
            "res_model": "news.log.entry",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    @api.autovacuum
    def _gc_successful_log_entries(self):
        """Vacuum old entries for successful logs.

        Deletes detail entries where the parent log has level='success'
        and the entry is older than 1 day. This keeps storage manageable
        while preserving error/warning details for debugging.
        """
        cutoff = fields.Datetime.now() - timedelta(days=1)
        # Find entries that are old AND belong to successful logs
        old_success_entries = self.search([
            ("timestamp", "<", cutoff),
            ("log_id.level", "=", "success"),
        ])
        if old_success_entries:
            count = len(old_success_entries)
            old_success_entries.unlink()
            return f"Deleted {count} old log entries from successful operations"
        return "No old log entries to clean up"
