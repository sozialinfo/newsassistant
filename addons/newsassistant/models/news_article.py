import json
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class NewsArticle(models.Model):
    _name = "news.article"
    _description = "News Article"
    _rec_name = "title"
    _order = "scrape_date desc, date desc, id desc"

    title = fields.Char(required=True)
    snapshot_id = fields.Many2one(
        "news.snapshot",
        string="Snapshot",
        required=True,
        ondelete="cascade",
        index=True,
    )
    source_id = fields.Many2one(
        "news.source",
        string="Source",
        compute="_compute_source_id",
        store=True,
        index=True,
    )
    url = fields.Char(index=True)
    date = fields.Date()
    summary = fields.Text()
    content = fields.Html(sanitize=True, sanitize_overridable=True)
    stage_id = fields.Many2one(
        "news.article.stage",
        string="Stage",
        default=lambda self: self._default_stage_id(),
        group_expand="_read_group_stage_ids",
    )
    scrape_date = fields.Datetime(readonly=True)
    active = fields.Boolean(default=True)

    # Header image extracted from article
    header_image = fields.Binary(
        string="Header Image",
        help="Header image extracted from the article, suitable for blog covers",
    )
    header_image_filename = fields.Char(
        string="Header Image Filename",
    )

    # Extraction state tracking
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("scraped", "Scraped"),
            ("error", "Error"),
            ("skipped", "Skipped"),
        ],
        default="pending",
        readonly=True,
        index=True,
    )
    status_message = fields.Text(readonly=True)
    retry_count = fields.Integer(default=0, readonly=True)
    last_error_date = fields.Datetime(readonly=True)
    log_ids = fields.One2many("news.log", "article_id", string="Logs")

    _sql_constraints = [
        ("url_unique", "UNIQUE(url)", "An article with this URL already exists."),
    ]

    @api.depends("snapshot_id", "snapshot_id.source_id")
    def _compute_source_id(self):
        for article in self:
            article.source_id = article.snapshot_id.source_id

    @api.model
    def _default_stage_id(self):
        """Return the configured default stage, falling back to 'New' by name."""
        param = self.env["ir.config_parameter"].sudo().get_param(
            "newsassistant.new_article_stage_id"
        )
        if param:
            stage = self.env["news.article.stage"].browse(int(param))
            if stage.exists():
                return stage
        return self.env["news.article.stage"].search([("name", "=", "New")], limit=1)

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        """Always show all stages in kanban, even empty ones."""
        return self.env["news.article.stage"].search([])

    def action_re_extract(self):
        """Button action: manually re-extract article from its snapshot."""
        self.ensure_one()
        if not self.snapshot_id:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Cannot Re-extract"),
                    "message": _("No snapshot linked to this article."),
                    "type": "warning",
                    "sticky": False,
                },
            }
        self.snapshot_id.with_delay(
            channel="root.newsassistant",
            description=f"Manual re-extract: {self.title[:50]}",
        )._extract_articles()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Re-extract Started"),
                "message": _("Re-extracting article from snapshot in background..."),
                "type": "info",
                "sticky": False,
            },
        }

    def action_skip(self):
        """Mark article as skipped and archive it."""
        self.ensure_one()
        if self.state == "skipped":
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Already Skipped"),
                    "message": _("This article is already skipped."),
                    "type": "warning",
                    "sticky": False,
                },
            }
        self.write({"state": "skipped", "active": False})
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Article Skipped"),
                "message": _("Article marked as skipped and archived."),
                "type": "info",
                "sticky": False,
            },
        }

    def action_reset(self):
        """Reset skipped article to pending state and unarchive."""
        self.ensure_one()
        self.write({
            "state": "pending",
            "status_message": False,
            "last_error_date": False,
            "retry_count": 0,
            "active": True,
        })
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Article Reset"),
                "message": _("Article reset to pending and unarchived."),
                "type": "info",
                "sticky": False,
            },
        }


