import json
import logging
import os
import re
import time

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.newsassistant.models.utils import html_has_content, html_to_markdown

from odoo.addons.queue_job.exception import RetryableJobError

_logger = logging.getLogger(__name__)

AI_TIMEOUT = 120
TRANSIENT_HTTP_CODES = {408, 429, 500, 502, 503, 504}
MAX_ARTICLES_IN_BRIEF = 50


class StrategyDigest(models.Model):
    _name = "strategy.digest"
    _inherit = ["strategy.ai.mixin"]
    _description = "Strategy Digest"
    _order = "date_from desc, name"

    # -------------------------------------------------------------------------
    # Fields
    # -------------------------------------------------------------------------

    name = fields.Char(
        string="Name",
        required=True,
    )
    date_from = fields.Date(
        string="From",
        required=True,
    )
    date_to = fields.Date(
        string="To",
        required=True,
    )
    strategy_ids = fields.Many2many(
        "strategy.strategy",
        "strategy_digest_strategy_rel",
        "digest_id",
        "strategy_id",
        string="Strategies",
        help="Strategies active during this period. Populated automatically when generating the brief.",
    )
    article_ids = fields.Many2many(
        "news.article",
        "strategy_digest_article_rel",
        "digest_id",
        "article_id",
        string="Articles",
        help="Articles with strategy labels in this period. Populated automatically when generating the brief.",
    )
    brief = fields.Html(
        string="Strategy Brief",
        sanitize=True,
        help="AI-generated executive brief for this period. Can be freely edited after generation.",
    )
    has_brief = fields.Boolean(
        string="Has Brief",
        compute="_compute_has_brief",
        store=False,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("done", "Done"),
        ],
        default="draft",
        string="State",
        copy=False,
    )

    # -------------------------------------------------------------------------
    # Constraints
    # -------------------------------------------------------------------------

    @api.depends("brief")
    def _compute_has_brief(self):
        for record in self:
            record.has_brief = html_has_content(record.brief)

    # -------------------------------------------------------------------------

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for record in self:
            if record.date_from and record.date_to and record.date_from > record.date_to:
                raise ValidationError(
                    _("'From' date must be before or equal to 'To' date.")
                )

    # -------------------------------------------------------------------------
    # Period Resolution
    # -------------------------------------------------------------------------

    def _get_active_strategies_for_period(self):
        """Return all active strategies active during this digest's period.

        Only strategies with state='active' and dates overlapping the period are returned.
        Strategies with no dates are considered eternal (always active).
        """
        self.ensure_one()
        all_strategies = self.env["strategy.strategy"].search([("state", "=", "active")])
        return all_strategies.filtered(
            lambda s: s._is_active_for_period(self.date_from, self.date_to)
        )

    def _get_articles_for_period(self):
        """Return articles with strategy labels and date within this digest's period."""
        self.ensure_one()
        return self.env["news.article"].search([
            ("date", ">=", self.date_from),
            ("date", "<=", self.date_to),
            ("strategy_label_ids", "!=", False),
            ("state", "=", "scraped"),
        ], order="date desc")

    # -------------------------------------------------------------------------
    # Brief Generation
    # -------------------------------------------------------------------------

    def _build_brief_prompt(self, strategies, articles, lang):
        """Build the AI prompt for brief generation.

        Args:
            strategies: strategy.strategy recordset
            articles: news.article recordset
            lang: language code string (e.g. 'de_DE', 'fr_FR', 'en_US')

        Returns:
            tuple: (system_prompt, user_content)
        """
        # Determine human-readable language name for the prompt
        lang_name_map = {
            "de": "German",
            "fr": "French",
            "it": "Italian",
            "es": "Spanish",
            "en": "English",
        }
        lang_prefix = (lang or "en")[:2].lower()
        language = lang_name_map.get(lang_prefix, "English")

        system_prompt = (
            f"/no_think\n"
            f"You are a strategic analyst writing an executive brief in {language}.\n\n"
            "Create a concise strategy brief based on the provided articles and strategies.\n"
            "The brief MUST:\n"
            "1. Be written in HTML format (use <h2>, <h3>, <p>, <ul>, <li>, <strong> tags)\n"
            "2. Start with an <h2>Executive Summary</h2> section (2–3 paragraphs)\n"
            "3. Continue with an <h2>Detailed Analysis</h2> section organised by strategy\n"
            "4. Reference articles using footnote-style superscript numbers: <sup>[1]</sup>\n"
            "5. End with an <h2>Sources</h2> section listing all referenced articles\n"
            "6. Be concise — target no more than 2 A4 pages when printed\n"
            f"7. Write ALL prose in {language} — article titles and source names may remain in their original language\n"
            "8. Cross-reference articles that are relevant to multiple strategies\n\n"
            "Return ONLY the HTML content — no markdown fences, no explanation outside the HTML."
        )

        # Strategies section
        strategies_text = ""
        for strategy in strategies:
            label_names = ", ".join(strategy.label_ids.mapped("name")) or "(no labels)"
            strategies_text += f"\n### Strategy: {strategy.name}\n"
            if strategy.date_from or strategy.date_to:
                date_range = f"{strategy.date_from or '∞'} – {strategy.date_to or '∞'}"
                strategies_text += f"Date range: {date_range}\n"
            strategies_text += f"Labels: {label_names}\n"
            if strategy.digest_prompt:
                prompt_md = html_to_markdown(strategy.digest_prompt)
                strategies_text += f"Focus: {prompt_md[:500]}\n"

        # Articles section — numbered for footnote referencing
        articles_text = ""
        article_list = list(articles[:MAX_ARTICLES_IN_BRIEF])
        for idx, article in enumerate(article_list, 1):
            label_names = ", ".join(article.strategy_label_ids.mapped("name")) or ""
            articles_text += (
                f"\n[{idx}] {article.title}\n"
                f"    Source: {article.source_id.name if article.source_id else 'Unknown'}\n"
                f"    Date: {article.date}\n"
                f"    Labels: {label_names}\n"
                f"    URL: {article.url or ''}\n"
            )
            if article.summary:
                articles_text += f"    Summary: {article.summary[:200]}\n"

        truncation_note = ""
        if len(articles) > MAX_ARTICLES_IN_BRIEF:
            truncation_note = (
                f"\n(Note: {len(articles) - MAX_ARTICLES_IN_BRIEF} additional articles "
                "were found but omitted for brevity.)\n"
            )

        period_str = f"{self.date_from} to {self.date_to}"
        user_content = (
            f"Period: {period_str}\n\n"
            f"## Active Strategies\n{strategies_text}\n\n"
            f"## Articles ({len(article_list)} of {len(articles)})\n"
            f"{articles_text}{truncation_note}"
        )

        return system_prompt, user_content

    def action_print_brief(self):
        """Print the strategy brief as PDF."""
        self.ensure_one()
        return self.env.ref(
            "newsassistant_strategy_digest.action_report_strategy_digest"
        ).report_action(self)

    def action_generate_brief(self):
        """Generate the AI strategy brief for this digest's period."""
        self.ensure_one()

        strategies = self._get_active_strategies_for_period()
        articles = self._get_articles_for_period()

        if not articles:
            raise UserError(
                _("No strategy-labelled articles found for the period %s – %s.\n\n"
                  "Make sure articles have been evaluated for strategy labels "
                  "(see the cron job or use 'Re-evaluate Strategy Labels' on individual articles).")
                % (self.date_from, self.date_to)
            )

        # Determine user's language
        lang = self.env.user.lang or "en_US"

        system_prompt, user_content = self._build_brief_prompt(strategies, articles, lang)

        try:
            result = self._call_ai(system_prompt, user_content, temperature=0.4)
        except (RetryableJobError, UserError):
            raise
        except Exception as e:
            raise UserError(_("AI call failed: %s") % str(e)) from e

        # Strip any <think> blocks from AI output
        brief_html = result["content"].strip()
        brief_html = re.sub(r"<think>.*?</think>", "", brief_html, flags=re.DOTALL).strip()
        # Strip markdown fences if present
        if brief_html.startswith("```"):
            first_newline = brief_html.find("\n")
            if first_newline != -1:
                brief_html = brief_html[first_newline + 1:]
        if brief_html.endswith("```"):
            brief_html = brief_html[:-3].strip()

        self.write({
            "brief": brief_html,
            "strategy_ids": [(6, 0, strategies.ids)],
            "article_ids": [(6, 0, articles[:MAX_ARTICLES_IN_BRIEF].ids)],
        })

        _logger.info(
            "Strategy digest brief generated for '%s': %d strategies, %d articles",
            self.name,
            len(strategies),
            len(articles),
        )

        return False
