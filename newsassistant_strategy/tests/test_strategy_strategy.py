import base64
import os
from datetime import date
from unittest.mock import MagicMock, patch

import requests

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.newsassistant.models.utils import html_has_content

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

        cls.strategy = cls.StrategyStrategy.create({
            "name": "Test Strategy Base",
        })

    # -------------------------------------------------------------------------
    # _is_active_for_period tests
    # -------------------------------------------------------------------------

    def test_no_dates_is_eternal(self):
        strategy = self.StrategyStrategy.create({"name": "Eternal Test"})
        self.assertTrue(strategy._is_active_for_period(date(2020, 1, 1), date(2030, 12, 31)))
        self.assertTrue(strategy._is_active_for_period(date(2000, 1, 1), date(2000, 12, 31)))

    def test_date_from_only(self):
        strategy = self.StrategyStrategy.create({
            "name": "FromOnly Test",
            "date_from": date(2026, 1, 1),
        })
        self.assertTrue(strategy._is_active_for_period(date(2026, 6, 1), date(2026, 12, 31)))
        self.assertTrue(strategy._is_active_for_period(date(2025, 12, 31), date(2026, 1, 1)))
        self.assertFalse(strategy._is_active_for_period(date(2025, 1, 1), date(2025, 12, 31)))

    def test_date_to_only(self):
        strategy = self.StrategyStrategy.create({
            "name": "ToOnly Test",
            "date_to": date(2026, 12, 31),
        })
        self.assertTrue(strategy._is_active_for_period(date(2026, 1, 1), date(2026, 6, 1)))
        self.assertTrue(strategy._is_active_for_period(date(2026, 12, 31), date(2027, 1, 1)))
        self.assertFalse(strategy._is_active_for_period(date(2027, 1, 1), date(2027, 12, 31)))

    def test_both_dates_overlap(self):
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
        attachment = MagicMock()
        attachment.datas = None
        attachment.name = "empty.pdf"
        result = self.strategy._extract_pdf_text(attachment)
        self.assertEqual(result, "")

    def test_extract_pdf_text_with_mocked_pdfminer(self):
        attachment = MagicMock()
        attachment.name = "test.pdf"
        attachment.datas = base64.b64encode(b"%PDF-1.4 fake content").decode()

        target = (
            "odoo.addons.newsassistant_strategy.models."
            "strategy_strategy.pdfminer_extract_text"
        )
        with patch(target, return_value="Extracted strategy text.") as mock_extract:
            result = self.strategy._extract_pdf_text(attachment)
            self.assertEqual(result, "Extracted strategy text.")
            self.assertTrue(mock_extract.called)

    def test_extract_pdf_text_exception_returns_empty(self):
        attachment = MagicMock()
        attachment.name = "corrupt.pdf"
        attachment.datas = base64.b64encode(b"not a pdf").decode()

        target = (
            "odoo.addons.newsassistant_strategy.models."
            "strategy_strategy.pdfminer_extract_text"
        )
        with patch(target, side_effect=Exception("PDF parse error")):
            result = self.strategy._extract_pdf_text(attachment)
        self.assertEqual(result, "")

    # -------------------------------------------------------------------------
    # action_distill_prompt tests (base — dispatches to sisters)
    # -------------------------------------------------------------------------

    def test_distill_prompt_no_content_raises_user_error(self):
        strategy = self.StrategyStrategy.create({"name": "Empty Distill Test"})
        with self.assertRaises(UserError):
            strategy.action_distill_prompt()

    def test_distill_prompt_no_sisters_raises_user_error(self):
        """Distill raises UserError when no sister modules are installed."""
        strategy = self.StrategyStrategy.create({
            "name": "No Sisters Test",
            "description": "Has content but no distillation target.",
        })
        with self.assertRaises(UserError):
            strategy._do_distill_prompt()


@tagged("post_install", "-at_install")
class TestStrategyStrategyCallAI(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.strategy = cls.env["strategy.strategy"].create({"name": "CallAI Test Strategy"})

    def test_call_ai_no_api_key_raises_user_error(self):
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": ""}):
            with self.assertRaises(UserError):
                self.strategy._call_ai("system", "user")

    def test_call_ai_timeout_raises_retryable(self):
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": "test-key"}), \
             patch("requests.post", side_effect=requests.exceptions.Timeout()):
            with self.assertRaises(RetryableJobError):
                self.strategy._call_ai("system", "user")

    def test_call_ai_connection_error_raises_retryable(self):
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": "test-key"}), \
             patch("requests.post", side_effect=requests.exceptions.ConnectionError("conn")):
            with self.assertRaises(RetryableJobError):
                self.strategy._call_ai("system", "user")

    def test_call_ai_transient_http_raises_retryable(self):
        mock_response = MagicMock()
        mock_response.status_code = 503
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": "test-key"}), \
             patch("requests.post", return_value=mock_response):
            with self.assertRaises(RetryableJobError):
                self.strategy._call_ai("system", "user")

    def test_call_ai_non_200_raises_value_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": "test-key"}), \
             patch("requests.post", return_value=mock_response):
            with self.assertRaises(ValueError):
                self.strategy._call_ai("system", "user")

    def test_call_ai_malformed_response_raises_value_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": []}
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": "test-key"}), \
             patch("requests.post", return_value=mock_response):
            with self.assertRaises(ValueError):
                self.strategy._call_ai("system", "user")

    def test_call_ai_success(self):
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
        result = self.strategy._parse_ai_json('{"key": "value"}')
        self.assertEqual(result["key"], "value")

    def test_parse_ai_json_with_markdown_fences(self):
        raw = '```json\n{"is_relevant": false}\n```'
        result = self.strategy._parse_ai_json(raw)
        self.assertFalse(result["is_relevant"])

    def test_parse_ai_json_with_think_blocks(self):
        raw = 'thinking\nSome AI thoughts here\n response\n{"key": "value"}'
        result = self.strategy._parse_ai_json(raw)
        self.assertEqual(result["key"], "value")


@tagged("post_install", "-at_install")
class TestStrategyState(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.StrategyStrategy = cls.env["strategy.strategy"]

    def _make_strategy(self, **kwargs):
        defaults = {"name": "State Test Strategy"}
        defaults.update(kwargs)
        return self.StrategyStrategy.create(defaults)

    def test_new_strategy_defaults_to_draft(self):
        s = self._make_strategy()
        self.assertEqual(s.state, "draft")

    def test_set_draft_from_active(self):
        s = self._make_strategy(state="active")
        s.write({"state": "draft"})
        self.assertEqual(s.state, "draft")

    def test_set_draft_from_archived(self):
        s = self._make_strategy(state="archived")
        s.write({"state": "draft"})
        self.assertEqual(s.state, "draft")

    def test_archive_from_draft(self):
        s = self._make_strategy()
        s.write({"state": "archived"})
        self.assertEqual(s.state, "archived")

    def test_archive_from_active(self):
        s = self._make_strategy(state="active")
        s.write({"state": "archived"})
        self.assertEqual(s.state, "archived")

    # ── Activation guard ──────────────────────────────────────────────────────

    def test_activate_no_content_raises_user_error(self):
        s = self._make_strategy()
        with self.assertRaises(UserError):
            s.write({"state": "active"})

    def test_activate_with_description_succeeds(self):
        s = self._make_strategy(description="Some description.")
        s.write({"state": "active"})
        self.assertEqual(s.state, "active")

    def test_activate_with_documents_succeeds(self):
        attachment = self.env["ir.attachment"].create({
            "name": "test.pdf",
            "datas": base64.b64encode(b"%PDF fake").decode(),
            "mimetype": "application/pdf",
        })
        s = self._make_strategy()
        s.write({"document_ids": [(4, attachment.id)]})
        s.write({"state": "active"})
        self.assertEqual(s.state, "active")

    def test_action_activate_no_content_raises(self):
        s = self._make_strategy()
        with self.assertRaises(UserError):
            s.action_activate()

    def test_action_activate_with_description_succeeds(self):
        s = self._make_strategy(description="Some description.")
        s.action_activate()
        self.assertEqual(s.state, "active")


@tagged("post_install", "-at_install")
class TestDistillConfirmWizard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.StrategyStrategy = cls.env["strategy.strategy"]

    def test_distill_wizard_created(self):
        s = self.StrategyStrategy.create({
            "name": "Wizard Test",
            "description": "Has content.",
        })
        wizard = self.env["strategy.distill.confirm"].create({"strategy_id": s.id})
        self.assertEqual(wizard.strategy_id, s)