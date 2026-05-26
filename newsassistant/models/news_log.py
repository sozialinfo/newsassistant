from odoo import fields, models


class NewsLog(models.Model):
    """Unified log for scraping operations.

    Stores one summary record per operation (listing scrape or article extraction).
    Detail entries are stored in news.log.entry with full LLM interaction data.
    """

    _name = "news.log"
    _description = "News Log"
    _rec_name = "message"
    _order = "timestamp desc"

    timestamp = fields.Datetime(
        required=True,
        default=fields.Datetime.now,
        index=True,
    )
    level = fields.Selection(
        [
            ("success", "Success"),
            ("warning", "Warning"),
            ("error", "Error"),
        ],
        required=True,
        index=True,
    )
    category = fields.Selection(
        [
            ("listing", "Listing Scrape"),
            ("extraction", "Article Extraction"),
            ("email", "Email Inbound"),
        ],
        required=True,
        index=True,
    )
    message = fields.Char(required=True)
    duration = fields.Float(string="Duration (s)")

    # Links to related objects (all optional)
    source_id = fields.Many2one(
        "news.source",
        string="Source",
        ondelete="set null",
        index=True,
    )
    snapshot_id = fields.Many2one(
        "news.snapshot",
        string="Snapshot",
        ondelete="set null",
        index=True,
    )
    article_id = fields.Many2one(
        "news.article",
        string="Article",
        ondelete="set null",
        index=True,
    )
    job_id = fields.Many2one(
        "queue.job",
        string="Job",
        ondelete="set null",
        index=True,
    )

    # Detail entries
    entry_ids = fields.One2many(
        "news.log.entry",
        "log_id",
        string="Entries",
    )

    # Articles created by this job (for listing scrapes)
    created_article_ids = fields.Many2many(
        "news.article",
        string="Created Articles",
    )
    created_article_count = fields.Integer(
        compute="_compute_created_article_count",
        string="Articles Created",
    )

    def _compute_created_article_count(self):
        """Count created articles per log using a single batched query."""
        if not self.ids:
            for log in self:
                log.created_article_count = 0
            return
        self.env.cr.execute(
            """
            SELECT news_log_id, COUNT(news_article_id)
            FROM news_article_news_log_rel
            WHERE news_log_id IN %s
            GROUP BY news_log_id
            """,
            [tuple(self.ids)],
        )
        counts = {row[0]: row[1] for row in self.env.cr.fetchall()}
        for log in self:
            log.created_article_count = counts.get(log.id, 0)

    def action_view_created_articles(self):
        """Open the articles created by this job."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Created Articles",
            "res_model": "news.article",
            "view_mode": "list,form",
            "domain": [("id", "in", self.created_article_ids.ids)],
            "context": {"create": False},
        }

    # Computed fields for display
    source_name = fields.Char(
        related="source_id.name",
        string="Source Name",
        store=False,
    )
    article_title = fields.Char(
        related="article_id.title",
        string="Article Title",
        store=False,
    )
