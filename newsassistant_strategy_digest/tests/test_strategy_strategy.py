import base64
import io
import os
from datetime import date
from unittest.mock import MagicMock, patch

import requests

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.newsassistant.models.utils import html_has_content, html_to_markdown

try:
    from odoo.addons.queue_job.exception import RetryableJobError
except ImportError:  # pragma: no cover
    RetryableJobError = Exception  # pragma: no cover


@tagged("post_install", "-at_install")
class TestStrategyStrategy(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.StrategyStrategy = cls.env["strategy.strategy"]
        cls.StrategyLabel = cls.env["strategy.label"]

        cls.label_innovation = cls.StrategyLabel.create({"name": "StratTest_Innovation"})
        cls.label_risk = cls.StrategyLabel.create({"name": "StratTest_Risk"})

        cls.strategy = cls.StrategyStrategy.create({
            "name": "Test Strategy Base",
            "label_ids": [(4, cls.label_innovation.id)],
        })

    # -------------------------------------------------------------------------
    # _is_active_for_period tests
    # -------------------------------------------------------------------------

    def test_no_dates_is_eternal(self):
        """Strategy with no dates is always active."""
        strategy = self.StrategyStrategy.create({"name": "Eternal Test"})
        self.assertTrue(strategy._is_active_for_period(date(2020, 1, 1), date(2030, 12, 31)))
        self.assertTrue(strategy._is_active_for_period(date(2000, 1, 1), date(2000, 12, 31)))

    def test_date_from_only(self):
        """Strategy with only date_from is active from that date onwards."""
        strategy = self.StrategyStrategy.create({
            "name": "FromOnly Test",
            "date_from": date(2026, 1, 1),
        })
        self.assertTrue(strategy._is_active_for_period(date(2026, 6, 1), date(2026, 12, 31)))
        self.assertTrue(strategy._is_active_for_period(date(2025, 12, 31), date(2026, 1, 1)))
        self.assertFalse(strategy._is_active_for_period(date(2025, 1, 1), date(2025, 12, 31)))

    def test_date_to_only(self):
        """Strategy with only date_to is active up to that date."""
        strategy = self.StrategyStrategy.create({
            "name": "ToOnly Test",
            "date_to": date(2026, 12, 31),
        })
        self.assertTrue(strategy._is_active_for_period(date(2026, 1, 1), date(2026, 6, 1)))
        self.assertTrue(strategy._is_active_for_period(date(2026, 12, 31), date(2027, 1, 1)))
        self.assertFalse(strategy._is_active_for_period(date(2027, 1, 1), date(2027, 12, 31)))

    def test_both_dates_overlap(self):
        """Strategy with both dates must overlap with period."""
        strategy = self.StrategyStrategy.create({
            "name": "Range Test",
            "date_from": date(2026, 3, 1),
            "date_to": date(2026, 9, 30),
        })
        self.assertTrue(strategy._is_active_for_period(date(2026, 1, 1), date(2026, 3, 15)))
        self.assertTrue(strategy._is_active_for_period(date(2026, 6, 1), date(2026, 7, 31)))
        self.assertTrue(strategy._is_active_for_period(date(2026, 9, 1), date(2026, 12, 31)))
        self.assertFalse(strategy._is_active_for_period(date(2026, 1, 1), date(2026, 2, 28)))
        self.assertFalse(strategy._is_active_for_period(date(2026, 10, 1), date(2026, 12, 31)))

    # -------------------------------------------------------------------------
    # _extract_pdf_text tests
    # -------------------------------------------------------------------------

    def test_extract_pdf_text_no_data(self):
        """Attachment with no data returns empty string."""
        from unittest.mock import MagicMock
        attachment = MagicMock()
        attachment.datas = None
        attachment.name = "empty.pdf"
        result = self.strategy._extract_pdf_text(attachment)
        self.assertEqual(result, "")

    def test_extract_pdf_text_with_mocked_pdfminer(self):
        """Test PDF text extraction with mocked pdfminer."""
        from unittest.mock import MagicMock

        attachment = MagicMock()
        attachment.name = "test.pdf"
        attachment.datas = base64.b64encode(b"%PDF-1.4 fake content").decode()

        target = (
            "odoo.addons.newsassistant_strategy_digest.models."
            "strategy_strategy.pdfminer_extract_text"
        )
        with patch(target, return_value="Extracted strategy text.") as mock_extract:
            result = self.strategy._extract_pdf_text(attachment)
            self.assertEqual(result, "Extracted strategy text.")
            self.assertTrue(mock_extract.called)

    def test_extract_pdf_text_exception_returns_empty(self):
        """Exception during extraction returns empty string."""
        from unittest.mock import MagicMock

        attachment = MagicMock()
        attachment.name = "corrupt.pdf"
        attachment.datas = base64.b64encode(b"not a pdf").decode()

        target = (
            "odoo.addons.newsassistant_strategy_digest.models."
            "strategy_strategy.pdfminer_extract_text"
        )
        with patch(target, side_effect=Exception("PDF parse error")):
            result = self.strategy._extract_pdf_text(attachment)
        self.assertEqual(result, "")

    # -------------------------------------------------------------------------
    # action_distill_prompt tests
    # -------------------------------------------------------------------------

    def test_distill_prompt_no_content_raises_user_error(self):
        """Distill with no PDFs and no description raises UserError."""
        strategy = self.StrategyStrategy.create({"name": "Empty Distill Test"})
        with self.assertRaises(UserError):
            strategy.action_distill_prompt()

    def _mock_distill_response(self, labels=None, prompt=None):
        """Helper: build a mock AI result for action_distill_prompt."""
        import json
        labels = labels or [
            {"name": "Berufsbildung", "description": "Articles about vocational training."},
            {"name": "Vernetzung", "description": "Articles about networking."},
        ]
        prompt = prompt or "Evaluate articles for relevance to social sector strategy."
        return {
            "content": json.dumps({"labels": labels, "prompt": prompt}),
            "usage": {"total_tokens": 200},
            "duration_ms": 500,
        }

    def test_distill_prompt_from_description(self):
        """Distill from description creates labels and saves prompt."""
        strategy = self.StrategyStrategy.create({
            "name": "Description Distill Test",
            "description": "Focus on vocational training and networking in the social sector.",
        })

        mock_result = self._mock_distill_response(
            labels=[
                {"name": "Berufsbildung", "description": "Articles about vocational training."},
                {"name": "Vernetzung", "description": "Articles about networking."},
            ],
            prompt="Evaluate articles about social sector vocational training.",
        )

        with patch.object(strategy.__class__, "_call_ai", return_value=mock_result):
            result = strategy.action_distill_prompt()

        self.assertIn("Evaluate articles about social sector vocational training.", strategy.prompt)
        self.assertEqual(len(strategy.label_ids), 2)
        label_names = strategy.label_ids.mapped("name")
        self.assertIn("Berufsbildung", label_names)
        self.assertIn("Vernetzung", label_names)
        self.assertEqual(result["params"]["type"], "success")

    def test_distill_prompt_reuses_existing_label(self):
        """Distill reuses an existing label instead of creating a duplicate."""
        existing_label = self.env["strategy.label"].create({"name": "ExistingLabel"})
        strategy = self.StrategyStrategy.create({
            "name": "Reuse Label Test",
            "description": "Test description.",
        })

        mock_result = self._mock_distill_response(
            labels=[{"name": "ExistingLabel", "description": "Reused label."}],
            prompt="Test prompt.",
        )

        with patch.object(strategy.__class__, "_call_ai", return_value=mock_result):
            strategy.action_distill_prompt()

        self.assertEqual(len(strategy.label_ids), 1)
        self.assertEqual(strategy.label_ids[0].id, existing_label.id)
        # No duplicate created
        count = self.env["strategy.label"].search_count([("name", "=", "ExistingLabel")])
        self.assertEqual(count, 1)

    def test_distill_prompt_with_pdf(self):
        """Distill from PDF attachment extracts text, creates labels, saves prompt."""
        strategy = self.StrategyStrategy.create({
            "name": "PDF Distill Test",
        })

        attachment = self.env["ir.attachment"].create({
            "name": "strategy_doc.pdf",
            "datas": base64.b64encode(b"%PDF-1.4 fake").decode(),
            "mimetype": "application/pdf",
        })
        strategy.write({"document_ids": [(4, attachment.id)]})

        mock_result = self._mock_distill_response(
            labels=[{"name": "PDFLabel", "description": "Articles from PDF."}],
            prompt="Generated prompt from PDF.",
        )

        target_extract = (
            "odoo.addons.newsassistant_strategy_digest.models."
            "strategy_strategy.pdfminer_extract_text"
        )
        with patch(target_extract, return_value="PDF content here."), \
             patch.object(strategy.__class__, "_call_ai", return_value=mock_result):
            strategy.action_distill_prompt()

        self.assertIn("Generated prompt from PDF.", strategy.prompt)
        self.assertEqual(len(strategy.label_ids), 1)
        self.assertEqual(strategy.label_ids[0].name, "PDFLabel")

    def test_distill_prompt_no_labels_in_response_raises_user_error(self):
        """Distill raises UserError when AI returns empty labels list."""
        import json
        strategy = self.StrategyStrategy.create({
            "name": "No Labels Test",
            "description": "Some description.",
        })
        mock_result = {
            "content": json.dumps({"labels": [], "prompt": "Some prompt."}),
            "usage": {},
            "duration_ms": 100,
        }
        with patch.object(strategy.__class__, "_call_ai", return_value=mock_result):
            with self.assertRaises(UserError):
                strategy.action_distill_prompt()

    def test_distill_prompt_no_prompt_in_response_raises_user_error(self):
        """Distill raises UserError when AI returns empty prompt."""
        import json
        strategy = self.StrategyStrategy.create({
            "name": "No Prompt Test",
            "description": "Some description.",
        })
        mock_result = {
            "content": json.dumps({"labels": [{"name": "SomeLabel", "description": "desc"}], "prompt": ""}),
            "usage": {},
            "duration_ms": 100,
        }
        with patch.object(strategy.__class__, "_call_ai", return_value=mock_result):
            with self.assertRaises(UserError):
                strategy.action_distill_prompt()

    def test_distill_prompt_invalid_json_raises_user_error(self):
        """Distill raises UserError when AI returns invalid JSON."""
        strategy = self.StrategyStrategy.create({
            "name": "Bad JSON Test",
            "description": "Some description.",
        })
        mock_result = {
            "content": "This is not JSON at all.",
            "usage": {},
            "duration_ms": 100,
        }
        with patch.object(strategy.__class__, "_call_ai", return_value=mock_result):
            with self.assertRaises(UserError):
                strategy.action_distill_prompt()


@tagged("post_install", "-at_install")
class TestStrategyStrategyCallAI(TransactionCase):
    """Tests for _call_ai error branches on strategy.strategy."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.strategy = cls.env["strategy.strategy"].create({"name": "CallAI Test Strategy"})

    def test_call_ai_no_api_key_raises_user_error(self):
        """_call_ai raises UserError when API key is not set."""
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": ""}):
            with self.assertRaises(UserError):
                self.strategy._call_ai("system", "user")

    def test_call_ai_timeout_raises_retryable(self):
        """_call_ai raises RetryableJobError on timeout."""
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": "test-key"}), \
             patch("requests.post", side_effect=requests.exceptions.Timeout()):
            with self.assertRaises(RetryableJobError):
                self.strategy._call_ai("system", "user")

    def test_call_ai_connection_error_raises_retryable(self):
        """_call_ai raises RetryableJobError on connection error."""
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": "test-key"}), \
             patch("requests.post", side_effect=requests.exceptions.ConnectionError("conn")):
            with self.assertRaises(RetryableJobError):
                self.strategy._call_ai("system", "user")

    def test_call_ai_transient_http_raises_retryable(self):
        """_call_ai raises RetryableJobError on transient HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": "test-key"}), \
             patch("requests.post", return_value=mock_response):
            with self.assertRaises(RetryableJobError):
                self.strategy._call_ai("system", "user")

    def test_call_ai_non_200_raises_value_error(self):
        """_call_ai raises ValueError on non-200 non-transient response."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": "test-key"}), \
             patch("requests.post", return_value=mock_response):
            with self.assertRaises(ValueError):
                self.strategy._call_ai("system", "user")

    def test_call_ai_malformed_response_raises_value_error(self):
        """_call_ai raises ValueError on malformed response structure."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": []}
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": "test-key"}), \
             patch("requests.post", return_value=mock_response):
            with self.assertRaises(ValueError):
                self.strategy._call_ai("system", "user")

    def test_call_ai_success(self):
        """_call_ai returns content on successful response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Strategy AI response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": "test-key"}), \
             patch("requests.post", return_value=mock_response):
            result = self.strategy._call_ai("system", "user")
        self.assertEqual(result["content"], "Strategy AI response")

    def test_parse_ai_json_plain(self):
        """_parse_ai_json handles plain JSON."""
        result = self.strategy._parse_ai_json('{"key": "value"}')
        self.assertEqual(result["key"], "value")

    def test_parse_ai_json_with_markdown_fences(self):
        """_parse_ai_json strips markdown fences."""
        raw = '```json\n{"is_relevant": false}\n```'
        result = self.strategy._parse_ai_json(raw)
        self.assertFalse(result["is_relevant"])

    def test_parse_ai_json_with_think_blocks(self):
        """_parse_ai_json strips <think> blocks."""
        raw = '<think>thinking...</think>\n{"key": "value"}'
        result = self.strategy._parse_ai_json(raw)
        self.assertEqual(result["key"], "value")

    def test_distill_prompt_empty_pdf_logs_warning(self):
        """Distill with PDF that yields no text logs a warning but continues with description."""
        import json as json_mod
        strategy = self.env["strategy.strategy"].create({
            "name": "Empty PDF Strategy",
            "description": "Fallback description content.",
        })
        attachment = self.env["ir.attachment"].create({
            "name": "scanned.pdf",
            "datas": base64.b64encode(b"%PDF-1.4 empty").decode(),
            "mimetype": "application/pdf",
        })
        strategy.write({"document_ids": [(4, attachment.id)]})

        mock_ai_result = {
            "content": json_mod.dumps({
                "labels": [{"name": "EmptyPDFLabel", "description": "Articles from description."}],
                "prompt": "Generated from description only.",
            }),
            "usage": {"total_tokens": 100},
            "duration_ms": 300,
        }
        target = (
            "odoo.addons.newsassistant_strategy_digest.models."
            "strategy_strategy.pdfminer_extract_text"
        )
        # PDF yields no text — warning should be logged and description used
        with patch(target, return_value=""), \
             patch.object(strategy.__class__, "_call_ai", return_value=mock_ai_result):
            result = strategy.action_distill_prompt()

        self.assertIn("Generated from description only.", strategy.prompt)
        self.assertEqual(len(strategy.label_ids), 1)
        self.assertEqual(result["params"]["type"], "success")

    def test_action_distill_retryable_error_reraises(self):
        """action_distill_prompt re-raises RetryableJobError from AI call."""
        strategy = self.env["strategy.strategy"].create({
            "name": "Retryable Distill Test",
            "description": "Test description for retryable error.",
        })
        with patch.object(strategy.__class__, "_call_ai",
                          side_effect=RetryableJobError("timeout", seconds=300)):
            with self.assertRaises(RetryableJobError):
                strategy.action_distill_prompt()

    def test_action_distill_user_error_reraises(self):
        """action_distill_prompt re-raises UserError from AI call."""
        strategy = self.env["strategy.strategy"].create({
            "name": "UserError Distill Test",
            "description": "Test description for user error.",
        })
        with patch.object(strategy.__class__, "_call_ai",
                          side_effect=UserError("No API key")):
            with self.assertRaises(UserError):
                strategy.action_distill_prompt()

    def test_action_distill_generic_exception_raises_user_error(self):
        """action_distill_prompt wraps generic exception in UserError."""
        strategy = self.env["strategy.strategy"].create({
            "name": "Generic Exception Distill Test",
            "description": "Test description.",
        })
        with patch.object(strategy.__class__, "_call_ai",
                          side_effect=Exception("something went wrong")):
            with self.assertRaises(UserError):
                strategy.action_distill_prompt()


@tagged("post_install", "-at_install")
class TestStrategyState(TransactionCase):
    """Tests for strategy.strategy state transitions and activation guard."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.StrategyStrategy = cls.env["strategy.strategy"]

    def _make_strategy(self, **kwargs):
        defaults = {"name": "State Test Strategy"}
        defaults.update(kwargs)
        return self.StrategyStrategy.create(defaults)

    def _mock_distill(self, strategy):
        """Return a mock AI result for distillation."""
        import json as json_mod
        return {
            "content": json_mod.dumps({
                "labels": [{"name": "TestLabel_State", "description": "desc"}],
                "prompt": "Test prompt text.",
            }),
            "usage": {"total_tokens": 100},
            "duration_ms": 200,
        }

    # ── Default state ────────────────────────────────────────────────────────

    def test_new_strategy_defaults_to_draft(self):
        """Newly created strategy has state='draft'."""
        s = self._make_strategy()
        self.assertEqual(s.state, "draft")

    # ── State selection values ────────────────────────────────────────────────

    def test_state_selection_values(self):
        """State field transitions work via write() when prompt is set."""
        s = self._make_strategy(prompt="<p>Prompt</p>")
        s.write({"state": "active"})
        self.assertEqual(s.state, "active")
        s.write({"state": "archived"})
        self.assertEqual(s.state, "archived")
        s.write({"state": "draft"})
        self.assertEqual(s.state, "draft")

    # ── State transitions via write() ─────────────────────────────────────────

    def test_set_draft_from_active(self):
        """write(state=draft) works from active."""
        s = self._make_strategy(state="active")
        s.write({"state": "draft"})
        self.assertEqual(s.state, "draft")

    def test_set_draft_from_archived(self):
        """write(state=draft) works from archived."""
        s = self._make_strategy(state="archived")
        s.write({"state": "draft"})
        self.assertEqual(s.state, "draft")

    def test_archive_from_draft(self):
        """write(state=archived) works from draft."""
        s = self._make_strategy()
        s.write({"state": "archived"})
        self.assertEqual(s.state, "archived")

    def test_archive_from_active(self):
        """write(state=archived) works from active."""
        s = self._make_strategy(state="active")
        s.write({"state": "archived"})
        self.assertEqual(s.state, "archived")

    # ── Activation guard ──────────────────────────────────────────────────────

    def test_activate_with_prompt_succeeds(self):
        """write(state=active) succeeds when prompt is set."""
        s = self._make_strategy(prompt="<p>Existing prompt</p>")
        s.write({"state": "active"})
        self.assertEqual(s.state, "active")

    def test_action_activate_with_prompt(self):
        """action_activate() activates immediately when prompt is set."""
        s = self._make_strategy(prompt="<p>Existing prompt</p>")
        s.action_activate()
        self.assertEqual(s.state, "active")

    def test_action_activate_auto_distills(self):
        """action_activate() auto-distills prompt when description is set."""
        s = self._make_strategy(description="Some description.")
        with patch.object(s.__class__, "_call_ai", return_value=self._mock_distill(s)):
            s.action_activate()
        self.assertEqual(s.state, "active")
        self.assertTrue(html_has_content(s.prompt))

    def test_action_activate_no_content_raises(self):
        """action_activate() raises UserError when no prompt and no content."""
        s = self._make_strategy()
        with self.assertRaises(UserError):
            s.action_activate()

    def test_activate_no_prompt_no_content_raises_user_error(self):
        """write(state=active) raises UserError when no prompt and no content."""
        s = self._make_strategy()
        with self.assertRaises(UserError):
            s.write({"state": "active"})

    def test_activate_empty_html_prompt_raises_user_error(self):
        """write(state=active) raises UserError when prompt is HTML editor empty state."""
        # The HTML editor stores '<p><br></p>' when cleared — must be treated as no prompt
        s = self._make_strategy(prompt="<p><br></p>")
        with self.assertRaises(UserError):
            s.write({"state": "active"})

    def test_activate_no_prompt_with_description_distills_and_activates(self):
        """write(state=active) auto-distills prompt and activates when description is set."""
        s = self._make_strategy(description="Some description.")
        with patch.object(s.__class__, "_call_ai", return_value=self._mock_distill(s)):
            s.write({"state": "active"})
        self.assertEqual(s.state, "active")
        self.assertTrue(html_has_content(s.prompt))

    def test_activate_no_prompt_with_documents_distills_and_activates(self):
        """write(state=active) auto-distills prompt and activates when documents are attached."""
        attachment = self.env["ir.attachment"].create({
            "name": "test.pdf",
            "datas": base64.b64encode(b"%PDF fake").decode(),
            "mimetype": "application/pdf",
        })
        s = self._make_strategy()
        s.write({"document_ids": [(4, attachment.id)]})
        with patch.object(s.__class__, "_call_ai", return_value=self._mock_distill(s)):
            s.write({"state": "active"})
        self.assertEqual(s.state, "active")
        self.assertTrue(html_has_content(s.prompt))

    # ── action_distill_prompt — overwrite confirmation ────────────────────────

    def test_distill_skips_label_with_empty_name(self):
        """_do_distill_prompt skips AI-returned labels with empty names."""
        import json as json_mod
        s = self._make_strategy(description="Description.")
        mock_result = {
            "content": json_mod.dumps({
                "labels": [
                    {"name": "", "description": "Empty name label."},
                    {"name": "ValidLabel_EmptySkip", "description": "Valid label."},
                ],
                "prompt": "Valid prompt text.",
            }),
            "usage": {"total_tokens": 100},
            "duration_ms": 200,
        }
        with patch.object(s.__class__, "_call_ai", return_value=mock_result):
            s._do_distill_prompt()
        # Only the valid label should be created
        label_names = s.label_ids.mapped("name")
        self.assertNotIn("", label_names)
        self.assertIn("ValidLabel_EmptySkip", label_names)

    def test_distill_prompt_when_prompt_exists_opens_wizard(self):
        """action_distill_prompt opens wizard when prompt already set."""
        s = self._make_strategy(
            prompt="<p>Existing prompt</p>",
            description="Some description.",
        )
        result = s.action_distill_prompt()
        self.assertEqual(result["type"], "ir.actions.act_window")
        self.assertEqual(result["res_model"], "strategy.distill.confirm")

    def test_distill_prompt_when_no_prompt_runs_directly(self):
        """action_distill_prompt runs distillation directly when no prompt set."""
        s = self._make_strategy(description="Some description.")
        with patch.object(s.__class__, "_call_ai", return_value=self._mock_distill(s)):
            result = s.action_distill_prompt()
        # Should return notification, not a wizard
        self.assertEqual(result["type"], "ir.actions.client")
        self.assertEqual(result["tag"], "display_notification")

    # ── strategy.distill.confirm wizard ──────────────────────────────────────

    def test_distill_confirm_wizard_runs_distillation(self):
        """StrategyDistillConfirm.action_confirm_distill() overwrites existing prompt."""
        s = self._make_strategy(
            prompt="<p>Old prompt</p>",
            description="New description for distillation.",
        )
        wizard = self.env["strategy.distill.confirm"].create({"strategy_id": s.id})

        with patch.object(s.__class__, "_call_ai", return_value=self._mock_distill(s)):
            wizard.action_confirm_distill()

        # Prompt should be updated (contains the new content)
        self.assertIn("<p>", s.prompt)
        self.assertNotIn("Old prompt", s.prompt)

    # ── HTML prompt storage ───────────────────────────────────────────────────

    def test_distill_writes_html_prompt(self):
        """_do_distill_prompt writes the prompt as HTML (wrapped in <p> tags)."""
        s = self._make_strategy(description="Description for HTML prompt test.")
        with patch.object(s.__class__, "_call_ai", return_value=self._mock_distill(s)):
            s._do_distill_prompt()
        self.assertIn("<p>", s.prompt)

    def test_prompt_field_accepts_html(self):
        """prompt field (Html) accepts and stores HTML content."""
        s = self._make_strategy()
        s.write({"prompt": "<h2>Title</h2><p>Body text.</p>"})
        self.assertIn("<h2>", s.prompt)

    # ── Reactivation from archived ────────────────────────────────────────────

    def test_reactivate_from_archived_with_prompt(self):
        """Can reactivate an archived strategy that has a prompt."""
        s = self._make_strategy(state="archived", prompt="<p>Prompt</p>")
        s.write({"state": "active"})
        self.assertEqual(s.state, "active")


@tagged("post_install", "-at_install")
class TestStrategyActiveFilter(TransactionCase):
    """Tests for active-only filtering in digest and article evaluation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.StrategyStrategy = cls.env["strategy.strategy"]

        cls.active_strategy = cls.StrategyStrategy.create({
            "name": "Active Strategy Filter Test",
            "state": "active",
            "prompt": "<p>Active prompt</p>",
        })
        cls.draft_strategy = cls.StrategyStrategy.create({
            "name": "Draft Strategy Filter Test",
            "state": "draft",
            "prompt": "<p>Draft prompt</p>",
        })
        cls.archived_strategy = cls.StrategyStrategy.create({
            "name": "Archived Strategy Filter Test",
            "state": "archived",
            "prompt": "<p>Archived prompt</p>",
        })

    def test_get_active_strategies_excludes_draft_and_archived(self):
        """_get_active_strategies_for_period only returns state='active' strategies."""
        from datetime import date
        digest = self.env["strategy.digest"].create({
            "name": "Filter Test Digest",
            "date_from": date(2020, 1, 1),
            "date_to": date(2030, 12, 31),
        })
        result = digest._get_active_strategies_for_period()
        result_ids = result.ids
        self.assertIn(self.active_strategy.id, result_ids)
        self.assertNotIn(self.draft_strategy.id, result_ids)
        self.assertNotIn(self.archived_strategy.id, result_ids)
