import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class NewsArticle(models.Model):
    _inherit = "news.article"

    # -------------------------------------------------------------------------
    # Cron / Pipeline — unified evaluation
    # -------------------------------------------------------------------------

    def _cron_strategy_eval_impl(self):
        """Cron entry point: queue evaluation jobs for unprocessed articles.

        Dispatches to all installed sister modules' evaluation methods
        via _evaluate_strategies().
        """
        articles = self.search([
            ("state", "=", "scraped"),
        ])

        _logger.info(
            "Strategy eval cron: found %d articles to check",
            len(articles),
        )

        for article in articles:
            article.with_delay(
                channel="root.newsassistant",
                description=f"Strategy eval: {article.title[:50]}",
            )._evaluate_strategies()

        return len(articles)

    def _evaluate_strategies(self):
        """Queue job: evaluate this article against all active strategies.

        Dispatches to sister modules. Each sister module's evaluation
        method checks its own state to skip already-processed articles.
        No-op implementations below are overridden by sister modules.
        """
        self.ensure_one()
        _logger.info("Evaluating strategies for article: %s", self.title)

        self._evaluate_strategy_labels()
        self._evaluate_strategy_watch()

    def _evaluate_strategy_labels(self):
        """No-op in base — overridden by newsassistant_strategy_digest."""
        pass

    def _evaluate_strategy_watch(self):
        """No-op in base — overridden by newsassistant_strategy_watch."""
        pass