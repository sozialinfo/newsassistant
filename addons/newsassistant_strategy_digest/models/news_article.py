import json
import logging
import os
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
        string="Strategy Eval State",
        help="Whether this article has been evaluated against active strategies.",
    )

    # -------------------------------------------------------------------------
    # AI Infrastructure (duplicated to avoid cross-module dependency)
    # -------------------------------------------------------------------------

    def _call_ai(self, system_prompt, user_content, temperature=0.1):
        """Call the Infomaniak AI chat completion API."""
        api_key = os.environ.get("INFOMANIAK_AI_API_KEY")
        if not api_key:
            raise UserError(
                _("Infomaniak AI API key not configured. "
                  "Set the INFOMANIAK_AI_API_KEY environment variable.")
            )

        product_id = self.env["ir.config_parameter"].sudo().get_param(
            "newsassistant.infomaniak_product_id", default="103794"
        )
        url = f"https://api.infomaniak.com/2/ai/{product_id}/openai/v1/chat/completions"

        model = "qwen3"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        start_time = time.time()
        try:
            response = requests.post(
                url, json=payload, headers=headers, timeout=AI_TIMEOUT
            )
        except requests.exceptions.Timeout:
            raise RetryableJobError(
                "Infomaniak AI API timeout", seconds=300, ignore_retry=False
            )
        except requests.exceptions.ConnectionError as e:
            raise RetryableJobError(
                f"Infomaniak AI API connection error: {e}",
                seconds=300,
                ignore_retry=False,
            )
        duration_ms = int((time.time() - start_time) * 1000)

        if response.status_code in TRANSIENT_HTTP_CODES:
            raise RetryableJobError(
                f"Infomaniak AI API returned {response.status_code}",
                seconds=300,
                ignore_retry=False,
            )

        if response.status_code != 200:
            raise ValueError(
                f"Infomaniak AI API error {response.status_code}: {response.text[:500]}"
            )

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise ValueError(f"Unexpected AI response structure: {e}")

        usage = data.get("usage", {})
        return {
            "content": content,
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            "duration_ms": duration_ms,
        }

    def _parse_ai_json(self, raw_text):
        """Parse JSON from AI response, handling markdown fences and thinking blocks."""
        import re

        text = raw_text.strip()
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

        if text.startswith("```"):
            first_newline = text.find("\n")
            if first_newline != -1:
                text = text[first_newline + 1:]
        if text.endswith("```"):
            text = text[:-3].strip()

        return json.loads(text)

    # -------------------------------------------------------------------------
    # Cron / Pipeline
    # -------------------------------------------------------------------------

    def _cron_strategy_eval_impl(self):
        """Cron entry point: queue evaluation jobs for unprocessed articles."""
        articles = self.search([
            ("state", "=", "scraped"),
            ("strategy_eval_state", "=", "pending"),
        ])

        _logger.info(
            "Strategy eval cron: found %d unprocessed articles",
            len(articles),
        )

        for article in articles:
            article.with_delay(
                channel="root.newsassistant",
                description=f"Strategy eval: {article.title[:50]}",
            )._evaluate_strategy_labels()

        return len(articles)

    def _evaluate_strategy_labels(self):
        """Queue job: evaluate this article against all active strategies.

        For each active strategy with a non-empty prompt, calls the AI and
        assigns matching labels. Marks strategy_eval_state as processed when done.
        """
        self.ensure_one()
        _logger.info("Evaluating strategy labels for article: %s", self.title)

        today = fields.Date.today()
        strategies = self.env["strategy.strategy"].search([("state", "=", "active")])
        active_strategies = strategies.filtered(
            lambda s: s._is_active_for_period(today, today) and s.prompt and s.prompt.strip()
        )

        if not active_strategies:
            _logger.info("No active strategies with prompts — marking article as processed")
            self.write({"strategy_eval_state": "processed"})
            return

        labels_to_add = self.env["strategy.label"]

        for strategy in active_strategies:
            try:
                new_labels = self._evaluate_against_strategy(strategy)
                labels_to_add |= new_labels
            except RetryableJobError:
                raise
            except Exception as e:
                _logger.warning(
                    "Strategy eval failed for article %s against strategy %s: %s",
                    self.title,
                    strategy.name,
                    e,
                )

        if labels_to_add:
            self.write({
                "strategy_label_ids": [(4, label.id) for label in labels_to_add],
            })

        self.write({"strategy_eval_state": "processed"})
        _logger.info(
            "Strategy eval complete for '%s': assigned labels %s",
            self.title,
            [l.name for l in labels_to_add],
        )

    def _evaluate_against_strategy(self, strategy):
        """Evaluate this article against a single strategy.

        Args:
            strategy: strategy.strategy record with a non-empty prompt.

        Returns:
            strategy.label recordset: Labels to assign (subset of strategy.label_ids).
        """
        self.ensure_one()

        label_names = [label.name for label in strategy.label_ids]

        prompt_text = html_to_markdown(strategy.prompt)
        system_prompt = (
            "/no_think\n"
            f"{prompt_text}\n\n"
            "Based on the above strategy, evaluate the following news article.\n"
            "Return a JSON object with exactly these fields:\n"
            '- "is_relevant": true or false\n'
            '- "labels": list of label names to assign (must be from: '
            + json.dumps(label_names) + ")\n"
            "Return ONLY valid JSON, no markdown, no explanation outside the JSON.\n"
            "Only include labels that clearly apply. Return an empty list if none apply."
        )

        # Prepare article content
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
                "Failed to parse AI response for article %s / strategy %s: %s",
                self.title,
                strategy.name,
                e,
            )
            return self.env["strategy.label"]

        is_relevant = result.get("is_relevant", False)
        if not is_relevant:
            return self.env["strategy.label"]

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

        return matched_labels

    # -------------------------------------------------------------------------
    # Manual Trigger
    # -------------------------------------------------------------------------

    def action_reevaluate_strategy_labels(self):
        """Button action: reset strategy eval state and re-queue evaluation."""
        self.ensure_one()

        self.write({"strategy_eval_state": "pending"})

        self.with_delay(
            channel="root.newsassistant",
            description=f"Strategy eval (manual): {self.title[:50]}",
        )._evaluate_strategy_labels()

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
            )._evaluate_strategy_labels()

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
