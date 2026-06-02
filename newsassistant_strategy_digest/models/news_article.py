import json
import logging
import os
import re
import time

import requests

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

    strategy_label_ids = fields.Many2many(
        "strategy.label",
        "news_article_strategy_label_rel",
        "article_id",
        "label_id",
        string="Strategy Labels",
        help="Labels assigned to this article based on strategy evaluation.",
    )
    strategy_eval_state = fields.Selection(
        [
            ("pending", "Pending"),
            ("processed", "Processed"),
        ],
        default="pending",
        readonly=True,
        index=True,
        string="Evaluation Status",
        help="Whether this article has been evaluated against active strategies.",
    )
    strategy_reasoning = fields.Text(
        string="Reasoning",
        readonly=True,
        help="LLM reasoning for strategy label assignments, concatenated per strategy.",
    )

    def _call_ai(self, system_prompt, user_content, temperature=0.1):
        """Delegate AI call to the shared StrategyAiMixin via strategy.strategy."""
        return self.env["strategy.strategy"]._call_ai(
            system_prompt, user_content, temperature=temperature
        )

    def _parse_ai_json(self, raw_text):
        """Delegate JSON parsing to the shared StrategyAiMixin via strategy.strategy."""
        return self.env["strategy.strategy"]._parse_ai_json(raw_text)

    # -------------------------------------------------------------------------
    # Strategy Label Evaluation (overrides base no-op)
    # -------------------------------------------------------------------------

    def _evaluate_strategy_labels(self):
        """Evaluate this article against all active strategies with digest prompts.

        For each active strategy with a non-empty digest_prompt, calls the AI and
        assigns matching labels. Sets strategy_eval_state to processed when done.
        """
        self.ensure_one()
        if self.strategy_eval_state == "processed":
            return

        _logger.info("Evaluating strategy labels for article: %s", self.title)

        today = fields.Date.today()
        strategies = self.env["strategy.strategy"].search([("state", "=", "active")])
        active_strategies = strategies.filtered(
            lambda s: s._is_active_for_period(today, today)
            and s.digest_prompt and s.digest_prompt.strip()
        )

        if not active_strategies:
            _logger.info("No active strategies with digest prompts — marking article as processed")
            self.write({"strategy_eval_state": "processed"})
            return

        labels_to_add = self.env["strategy.label"]
        reasoning_parts = []

        for strategy in active_strategies:
            try:
                new_labels, reasoning = self._evaluate_against_strategy(strategy)
                labels_to_add |= new_labels
                if reasoning:
                    reasoning_parts.append(f"{strategy.name}: {reasoning}")
            except RetryableJobError:
                raise
            except Exception as e:
                _logger.warning(
                    "Strategy eval failed for article %s against strategy %s: %s",
                    self.title,
                    strategy.name,
                    e,
                )

        vals = {"strategy_eval_state": "processed"}
        if labels_to_add:
            vals["strategy_label_ids"] = [(4, label.id) for label in labels_to_add]
        if reasoning_parts:
            vals["strategy_reasoning"] = "\n\n".join(reasoning_parts)

        self.write(vals)
        _logger.info(
            "Strategy eval complete for '%s': assigned labels %s",
            self.title,
            [l.name for l in labels_to_add],
        )

    def _evaluate_against_strategy(self, strategy):
        """Evaluate this article against a single strategy.

        Args:
            strategy: strategy.strategy record with a non-empty digest_prompt.

        Returns:
            tuple: (strategy.label recordset, reasoning str)
        """
        self.ensure_one()

        label_names = [label.name for label in strategy.label_ids]

        prompt_text = html_to_markdown(strategy.digest_prompt)
        system_prompt = (
            "/no_think\n"
            f"{prompt_text}\n\n"
            "Based on the above strategy, evaluate the following news article.\n"
            "Return a JSON object with exactly these fields:\n"
            '- "is_relevant": true or false\n'
            '- "labels": list of label names to assign (must be from: '
            + json.dumps(label_names) + ")\n"
            '- "reasoning": one or two sentences explaining why these labels apply '
            "(or why the article is not relevant)\n"
            "Return ONLY valid JSON, no markdown, no explanation outside the JSON.\n"
            "Only include labels that clearly apply. Return an empty list if none apply."
        )

        article_content = f"Title: {self.title}\n\n"
        if self.summary:
            article_content += f"Summary: {self.summary}\n\n"
        if self.content:
            clean_content = html_to_markdown(self.content)
            article_content += f"Content: {clean_content[:4000]}"

        ai_result = self._call_ai(system_prompt, article_content, temperature=0.1)

        empty = self.env["strategy.label"]
        try:
            result = self._parse_ai_json(ai_result["content"])
        except (json.JSONDecodeError, ValueError) as e:
            _logger.warning(
                "Failed to parse AI response for article %s / strategy %s: %s",
                self.title,
                strategy.name,
                e,
            )
            return empty, ""

        reasoning = result.get("reasoning", "") or ""
        is_relevant = result.get("is_relevant", False)
        if not is_relevant:
            return empty, reasoning

        returned_label_names = result.get("labels", [])
        if not isinstance(returned_label_names, list):
            returned_label_names = []

        matched_labels = self.env["strategy.label"]
        for label_name in returned_label_names:
            label = strategy.label_ids.filtered(
                lambda l: l.name.strip().lower() == str(label_name).strip().lower()
            )
            if label:
                matched_labels |= label
            else:
                _logger.warning(
                    "AI returned unknown label '%s' for strategy '%s' — skipping",
                    label_name,
                    strategy.name,
                )

        return matched_labels, reasoning

    # -------------------------------------------------------------------------
    # Manual Trigger
    # -------------------------------------------------------------------------

    def action_reevaluate_strategy_labels(self):
        """Button action: reset strategy eval state and re-queue evaluation."""
        self.ensure_one()

        self.write({
            "strategy_eval_state": "pending",
            "strategy_reasoning": False,
            "strategy_label_ids": [(5, False, False)],
        })

        self.with_delay(
            channel="root.newsassistant",
            description=f"Strategy eval (manual): {self.title[:50]}",
        )._evaluate_strategies()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Evaluation Queued"),
                "message": _("Strategy label evaluation has been queued for this article."),
                "type": "info",
                "sticky": False,
            },
        }

    def action_reevaluate_strategy_labels_bulk(self):
        """Server action: re-evaluate strategy labels for selected articles."""
        articles = self.filtered(lambda a: a.state == "scraped")
        skipped = len(self) - len(articles)

        if not articles:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("No Articles to Evaluate"),
                    "message": _("None of the selected articles are in 'Scraped' state."),
                    "type": "warning",
                    "sticky": False,
                },
            }

        articles.write({"strategy_eval_state": "pending"})

        for article in articles:
            article.with_delay(
                channel="root.newsassistant",
                description=f"Strategy eval (manual): {article.title[:50]}",
            )._evaluate_strategies()

        message = _("Queued %d article(s) for strategy label evaluation.") % len(articles)
        if skipped:
            message += _(" Skipped %d article(s) not in 'Scraped' state.") % skipped

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Evaluation Queued"),
                "message": message,
                "type": "info",
                "sticky": False,
            },
        }