import base64
import io
import json
import logging
import os
import re
import time

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.queue_job.exception import RetryableJobError

_logger = logging.getLogger(__name__)

try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text
except ImportError:  # pragma: no cover
    pdfminer_extract_text = None  # pragma: no cover

AI_TIMEOUT = 120
TRANSIENT_HTTP_CODES = {408, 429, 500, 502, 503, 504}
MAX_PDF_TEXT_CHARS = 8000


class StrategyAiMixin(models.AbstractModel):
    """Shared AI infrastructure for all strategy modules.

    Provides _call_ai() and _parse_ai_json() to any model that inherits
    this mixin. Avoids duplication across strategy_strategy, strategy_digest,
    and news_article (newsassistant_strategy_digest / newsassistant_strategy_watch).
    """

    _name = "strategy.ai.mixin"
    _description = "Strategy AI Mixin"

    def _call_ai(self, system_prompt, user_content, temperature=0.1):
        """Call the Infomaniak AI chat completion API.

        Returns:
            dict with keys: content, usage, duration_ms
        """
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
        text = raw_text.strip()
        text = re.sub(r"\s*thinking.*? response", "", text, flags=re.DOTALL).strip()

        if text.startswith("```"):
            first_newline = text.find("\n")
            if first_newline != -1:
                text = text[first_newline + 1:]
        if text.endswith("```"):
            text = text[:-3].strip()

        return json.loads(text)


class StrategyStrategy(models.Model):
    _name = "strategy.strategy"
    _inherit = ["strategy.ai.mixin", "mail.thread"]
    _description = "Strategy"
    _order = "name"

    # -------------------------------------------------------------------------
    # Fields
    # -------------------------------------------------------------------------

    name = fields.Char(
        string="Name",
        required=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("archived", "Archived"),
        ],
        string="State",
        default="draft",
        required=True,
        copy=False,
        tracking=True,
        index=True,
    )
    date_from = fields.Date(
        string="Valid From",
        index=True,
        help="Start date of the strategy (leave empty for no start limit).",
    )
    date_to = fields.Date(
        string="Valid To",
        index=True,
        help="End date of the strategy (leave empty for no end limit).",
    )
    description = fields.Text(
        string="Description",
        help="Text description of the strategy. Used alongside PDF documents for prompt distillation.",
    )
    document_ids = fields.Many2many(
        "ir.attachment",
        "strategy_strategy_attachment_rel",
        "strategy_id",
        "attachment_id",
        string="Upload Strategy Document",
        domain=[("mimetype", "like", "pdf")],
        help="PDF documents defining this strategy. Used to distill the AI prompts.",
    )

    # -------------------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------------------

    def action_activate(self):
        """Activate the strategy."""
        self.ensure_one()
        self.write({"state": "active"})

    # -------------------------------------------------------------------------
    # Write override — activation guard
    # -------------------------------------------------------------------------

    def write(self, vals):
        """Prevent activation when no content is available.

        When transitioning to 'active':
        - If content is available (description or documents): proceed.
        - If no content: raise UserError.
        """
        if vals.get("state") == "active":
            for record in self:
                if record.state == "active":
                    continue
                has_content = bool(
                    (record.description and record.description.strip())
                    or record.document_ids
                )
                if not has_content:
                    raise UserError(
                        _(
                            "Cannot activate this strategy: there is "
                            "no content to work with.\n\n"
                            "Please add PDF documents or a description first."
                        )
                    )
        return super().write(vals)

    # -------------------------------------------------------------------------
    # Business Logic Helpers
    # -------------------------------------------------------------------------

    def _is_active_for_period(self, period_from, period_to):
        """Check whether this strategy overlaps with the given period.

        A strategy with no dates is considered eternal (always active).
        A strategy with only date_from is active from that date onwards.
        A strategy with only date_to is active up to that date.
        A strategy with both dates must overlap with the period.

        Args:
            period_from (date): Start of the period (inclusive).
            period_to (date): End of the period (inclusive).

        Returns:
            bool: True if the strategy is active during the period.
        """
        self.ensure_one()
        if not self.date_from and not self.date_to:
            return True
        if self.date_from and not self.date_to:
            return self.date_from <= period_to
        if not self.date_from and self.date_to:
            return self.date_to >= period_from
        return self.date_from <= period_to and self.date_to >= period_from

    def _extract_pdf_text(self, attachment):
        """Extract text from a PDF attachment using pdfminer.

        Args:
            attachment: ir.attachment record with PDF content.

        Returns:
            str: Extracted text (may be empty for scanned PDFs).
        """
        if pdfminer_extract_text is None:  # pragma: no cover
            _logger.warning("pdfminer not available — cannot extract PDF text")  # pragma: no cover
            return ""  # pragma: no cover

        if not attachment.datas:
            return ""

        try:
            pdf_bytes = base64.b64decode(attachment.datas)
            pdf_stream = io.BytesIO(pdf_bytes)
            text = pdfminer_extract_text(pdf_stream)
            return (text or "").strip()
        except Exception as e:
            _logger.warning(
                "Failed to extract text from PDF '%s': %s",
                attachment.name,
                e,
            )
            return ""

    # -------------------------------------------------------------------------
    # Content gathering (shared by sister module distillations)
    # -------------------------------------------------------------------------

    def _distill_gather_content(self):
        """Gather text content from PDF documents and description.

        Returns:
            list[str]: Content parts to feed to the AI.

        Raises:
            UserError: If no content is available.
        """
        self.ensure_one()
        content_parts = []

        for attachment in self.document_ids:
            text = self._extract_pdf_text(attachment)
            if text:
                content_parts.append(
                    f"=== Document: {attachment.name} ===\n{text[:MAX_PDF_TEXT_CHARS]}"
                )
            else:
                _logger.warning(
                    "Strategy '%s': no text extracted from '%s' (possibly scanned PDF)",
                    self.name,
                    attachment.name,
                )

        if self.description and self.description.strip():
            content_parts.append(
                f"=== Strategy Description ===\n{self.description.strip()}"
            )

        if not content_parts:
            raise UserError(
                _("No content available to distill. Please upload PDF documents or add a description.")
            )

        return content_parts

    # -------------------------------------------------------------------------
    # Prompt distillation (base — dispatches to sister modules)
    # -------------------------------------------------------------------------

    def action_distill_prompt(self):
        """Distill the strategy into prompts for all installed sister modules.

        Opens a confirmation wizard before proceeding.
        """
        self.ensure_one()
        wizard = self.env["strategy.distill.confirm"].create({
            "strategy_id": self.id,
            "method_name": "",
            "is_plural": True,
        })
        return {
            "type": "ir.actions.act_window",
            "res_model": "strategy.distill.confirm",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    def _do_distill_prompt(self):
        """Run distillation for all installed sister modules.

        Each sister module's _distill_sister_prompt() is discovered
        dynamically and called if available.
        """
        self.ensure_one()
        distilled = []

        # Try to distill for each known sister module
        for method_name in ["_distill_digest_prompt", "_distill_watch_prompt"]:
            if hasattr(self, method_name):
                try:
                    getattr(self, method_name)()
                    distilled.append(method_name)
                except Exception as e:
                    _logger.warning(
                        "Strategy '%s': distillation via %s failed: %s",
                        self.name, method_name, e,
                    )

        if not distilled:
            raise UserError(
                _("No distillation modules are installed. "
                  "Please install at least one sister module (digest or watch).")
            )

        _logger.info(
            "Strategy '%s': completed distillation via %s",
            self.name,
            ", ".join(distilled),
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Prompt Distilled"),
                "message": _(
                    "Distilled prompts for %(count)d module(s).",
                    count=len(distilled),
                ),
                "type": "success",
                "sticky": True,
            },
        }


class StrategyDistillConfirm(models.TransientModel):
    """Wizard: confirm overwrite of existing prompts before distilling."""

    _name = "strategy.distill.confirm"
    _description = "Confirm Prompt Overwrite"
    strategy_id = fields.Many2one(
        "strategy.strategy",
        string="Strategy",
        required=True,
        ondelete="cascade",
    )
    method_name = fields.Char(
        string="Method",
        help="Name of the distillation method to call on confirmation. "
             "If empty, calls _do_distill_prompt() for all modules.",
    )
    is_plural = fields.Boolean(
        string="Plural",
        default=False,
        help="Whether the warning text should be plural (all vs. single prompt).",
    )
    confirm_title = fields.Char(
        string="Title",
        compute="_compute_confirm_text",
    )
    confirm_body = fields.Text(
        string="Body",
        compute="_compute_confirm_text",
    )

    @api.depends("is_plural")
    def _compute_confirm_text(self):
        """Compute confirm_title and confirm_body based on is_plural flag."""
        for wizard in self:
            if wizard.is_plural:
                wizard.confirm_title = "Overwrite All Prompts?"
                wizard.confirm_body = (
                    "Distilling new prompts will overwrite "
                    "the existing ones. Any manual edits to the current "
                    "prompts will be lost."
                )
            else:
                wizard.confirm_title = "Overwrite Prompt?"
                wizard.confirm_body = (
                    "Distilling a new prompt will overwrite "
                    "the existing one. Any manual edits to the current "
                    "prompt will be lost."
                )

    def action_confirm_distill(self):
        """Confirm overwrite and run the distillation for the strategy."""
        self.ensure_one()
        if self.method_name and hasattr(self.strategy_id, self.method_name):
            getattr(self.strategy_id, self.method_name)()
        else:
            self.strategy_id._do_distill_prompt()
        return {
            "type": "ir.actions.act_window",
            "res_model": "strategy.strategy",
            "res_id": self.strategy_id.id,
            "view_mode": "form",
            "target": "main",
        }