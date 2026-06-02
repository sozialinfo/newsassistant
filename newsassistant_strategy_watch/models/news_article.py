import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.newsassistant.models.utils import html_to_markdown

_logger = logging.getLogger(__name__)

AI_TIMEOUT = 120
TRANSIENT_HTTP_CODES = {408, 429, 500, 502, 503, 504}


class NewsArticle(models.Model):
    _inherit = "news.article"

    # -------------------------------------------------------------------------
    # Fields
    # -------------------------------------------------------------------------

    strategy_watch = fields.Boolean(
        string="Strategy Watch",
        default=False,
        help="Flagged when AI detects strategic impact in this article.",
    )
    strategy_watch_state = fields.Selection(
        [
            ("pending", "Pending"),
            ("processed", "Processed"),
        ],
        default="pending",
        readonly=True,
        index=True,
        string="Watch Evaluation",
        help="Whether this article has been evaluated for strategic watch.",
    )
    strategy_watch_reasoning = fields.Text(
        string="Watch Reasoning",
        readonly=True,
        help="LLM reasoning for the strategy watch decision.",
    )

    # -------------------------------------------------------------------------
    # Strategy Watch Evaluation (overrides base no-op)
    # -------------------------------------------------------------------------

    def _call_ai(self, system_prompt, user_content, temperature=0.1):
        """Delegate AI call to the shared StrategyAiMixin via strategy.strategy."""
        return self.env["strategy.strategy"]._call_ai(
            system_prompt, user_content, temperature=temperature
        )

    def _parse_ai_json(self, raw_text):
        """Delegate JSON parsing to the shared StrategyAiMixin via strategy.strategy."""
        return self.env["strategy.strategy"]._parse_ai_json(raw_text)

    def _evaluate_strategy_watch(self):
        """Evaluate this article against all active strategies with watch prompts.

        For each active strategy with a non-empty watch_prompt, calls the AI
        and sets strategy_watch = True if any strategy flags the article.
        Sets strategy_watch_state to processed when done.
        """
        self.ensure_one()
        if self.strategy_watch_state == "processed":
            return

        _logger.info("Evaluating strategy watch for article: %s", self.title)

        today = fields.Date.today()
        strategies = self.env["strategy.strategy"].search([("state", "=", "active")])
        active_strategies = strategies.filtered(
            lambda s: s._is_active_for_period(today, today)
            and s.watch_prompt and s.watch_prompt.strip()
        )

        if not active_strategies:
            _logger.info("No active strategies with watch prompts — marking article as processed")
            self.write({"strategy_watch_state": "processed"})
            return

        is_watched = False
        reasoning_parts = []

        for strategy in active_strategies:
            try:
                relevant, reasoning = self._evaluate_watch_against_strategy(strategy)
                if relevant:
                    is_watched = True
                if reasoning:
                    reasoning_parts.append(f"{strategy.name}: {reasoning}")
            except RetryableJobError:
                raise
            except Exception as e:
                _logger.warning(
                    "Strategy watch eval failed for article %s against strategy %s: %s",
                    self.title,
                    strategy.name,
                    e,
                )

        vals = {
            "strategy_watch_state": "processed",
            "strategy_watch": is_watched,
        }
        if reasoning_parts:
            vals["strategy_watch_reasoning"] = "\n\n".join(reasoning_parts)

        self.write(vals)
        _logger.info(
            "Strategy watch eval complete for '%s': watched=%s",
            self.title,
            is_watched,
        )

    def _evaluate_watch_against_strategy(self, strategy):
        """Evaluate this article against a single strategy's watch prompt.

        Args:
            strategy: strategy.strategy record with a non-empty watch_prompt.

        Returns:
            tuple: (is_watch_relevant bool, reasoning str)
        """
        self.ensure_one()

        prompt_text = html_to_markdown(strategy.watch_prompt)
        system_prompt = (
            "/no_think\n"
            f"{prompt_text}\n\n"
            "Based on the above strategy watch criteria, evaluate the following news article.\n"
            "Return a JSON object with exactly these fields:\n"
            '- "is_watch_relevant": true or false\n'
            '- "reasoning": one or two sentences explaining why this article should '
            "or should not be flagged for strategy watch\n"
            "Return ONLY valid JSON, no markdown, no explanation outside the JSON."
        )

        article_content = f"Title: {self.title}\n\n"
        if self.summary:
            article_content += f"Summary: {self.summary}\n\n"
        if self.content:
            clean_content = html_to_markdown(self.content)
            article_content += f"Content: {clean_content[:4000]}"

        ai_result = self._call_ai(system_prompt, article_content, temperature=0.1)

        try:
            result = self._parse_ai_json(ai_result["content"])
        except (json.JSONDecodeError, ValueError) as e:
            _logger.warning(
                "Failed to parse watch AI response for article %s / strategy %s: %s",
                self.title,
                strategy.name,
                e,
            )
            return False, ""

        reasoning = result.get("reasoning", "") or ""
        is_watch_relevant = result.get("is_watch_relevant", False)
        return is_watch_relevant, reasoning

    # -------------------------------------------------------------------------
    # Manual Trigger
    # -------------------------------------------------------------------------

    def action_reevaluate_strategy_watch(self):
        """Button action: reset watch eval state and re-queue evaluation."""
        self.ensure_one()

        self.write({
            "strategy_watch_state": "pending",
            "strategy_watch_reasoning": False,
            "strategy_watch": False,
        })

        self.with_delay(
            channel="root.newsassistant",
            description=f"Strategy watch eval (manual): {self.title[:50]}",
        )._evaluate_strategies()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Watch Evaluation Queued"),
                "message": _("Strategy watch evaluation has been queued for this article."),
                "type": "info",
                "sticky": False,
            },
        }