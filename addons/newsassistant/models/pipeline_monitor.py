from datetime import timedelta

from odoo import api, fields, models


class PipelineMonitor(models.TransientModel):
    """Pipeline Monitor dashboard for viewing scraping pipeline health."""

    _name = "news.pipeline.monitor"
    _description = "Pipeline Monitor"

    sources_with_errors = fields.Integer(compute="_compute_counts")
    articles_pending = fields.Integer(compute="_compute_counts")
    articles_with_errors = fields.Integer(compute="_compute_counts")
    recent_failures = fields.Integer(compute="_compute_counts")

    @api.depends_context("uid")
    def _compute_counts(self):
        Source = self.env["news.source"]
        Article = self.env["news.article"]
        SourceLog = self.env["news.source.log"]
        ArticleLog = self.env["news.article.log"]

        # Count sources with errors
        sources_error = Source.search_count([("state", "=", "error")])

        # Count articles by state
        articles_pending = Article.search_count([("state", "=", "pending")])
        articles_error = Article.search_count([("state", "=", "error")])

        # Count recent failures (last 24 hours)
        since = fields.Datetime.now() - timedelta(hours=24)
        source_failures = SourceLog.search_count([
            ("status", "=", "error"),
            ("timestamp", ">=", since),
        ])
        article_failures = ArticleLog.search_count([
            ("status", "=", "error"),
            ("timestamp", ">=", since),
        ])

        for record in self:
            record.sources_with_errors = sources_error
            record.articles_pending = articles_pending
            record.articles_with_errors = articles_error
            record.recent_failures = source_failures + article_failures

    def action_view_sources_with_errors(self):
        """Open sources filtered to error state."""
        return {
            "type": "ir.actions.act_window",
            "name": "Sources with Errors",
            "res_model": "news.source",
            "view_mode": "list,form",
            "domain": [("state", "=", "error")],
            "context": {"search_default_state_error": 1},
        }

    def action_view_articles_pending(self):
        """Open articles filtered to pending state."""
        return {
            "type": "ir.actions.act_window",
            "name": "Articles Pending",
            "res_model": "news.article",
            "view_mode": "list,form",
            "domain": [("state", "=", "pending")],
            "context": {"search_default_filter_state_pending": 1},
        }

    def action_view_articles_with_errors(self):
        """Open articles filtered to error state."""
        return {
            "type": "ir.actions.act_window",
            "name": "Articles with Errors",
            "res_model": "news.article",
            "view_mode": "list,form",
            "domain": [("state", "=", "error")],
            "context": {"search_default_filter_state_error": 1},
        }

    def action_view_recent_failures(self):
        """Open recent source log failures."""
        since = fields.Datetime.now() - timedelta(hours=24)
        return {
            "type": "ir.actions.act_window",
            "name": "Recent Failures",
            "res_model": "news.source.log",
            "view_mode": "list",
            "domain": [
                ("status", "=", "error"),
                ("timestamp", ">=", since),
            ],
        }
