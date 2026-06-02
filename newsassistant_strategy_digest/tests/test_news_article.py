import json
import os
from datetime import date
from unittest.mock import MagicMock, patch

import requests

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

try:
    from odoo.addons.queue_job.tests.common import trap_jobs
    from odoo.addons.queue_job.exception import RetryableJobError
except ImportError:  # pragma: no cover
    trap_jobs = None  # pragma: no cover
    RetryableJobError = Exception  # pragma: no cover


def _make_source_and_article(env, suffix=""):
    source = env["news.source"].create({
        "name": f"EvalSource {suffix}",
        "source_type": "website",
        "url": f"https://evaltest{suffix}.com",
    })
    snapshot = env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
        "source_id": source.id,
        "raw_content": "<p>Test article content about technology and innovation.</p>",
    })
    article = env["news.article"].create({
        "title": f"Eval Test Article {suffix}",
        "snapshot_id": snapshot.id,
        "url": f"https://evaltest{suffix}.com/article",
        "state": "scraped",
        "date": date.today(),
    })
    return article


@tagged("post_install", "-at_install")
class TestNewsArticleStrategyEval(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.article = _make_source_and_article(cls.env, suffix="main")
        cls.label = cls.env["strategy.label"].create({"name": "EvalTestLabel"})
        cls.strategy = cls.env["strategy.strategy"].create({
            "name": "EvalTestStrategy",
            "state": "active",
            "digest_prompt": "<p>Evaluate articles about technology.</p>",
            "label_ids": [(4, cls.label.id)],
        })

    def test_strategy_eval_state_default_pending(self):
        """New articles default to strategy_eval_state = pending."""
        article = _make_source_and_article(self.env, suffix="default")
        self.assertEqual(article.strategy_eval_state, "pending")

    def test_action_reevaluate_resets_state(self):
        """Re-evaluate action resets strategy_eval_state to pending."""
        self.article.write({"strategy_eval_state": "processed"})
        self.assertEqual(self.article.strategy_eval_state, "processed")

        if trap_jobs:
            with trap_jobs() as trap:
                result = self.article.action_reevaluate_strategy_labels()
        else:
            with patch.object(
                self.article.__class__,
                "_evaluate_strategy_labels",
                return_value=None,
            ):
                result = self.article.action_reevaluate_strategy_labels()

        self.assertEqual(self.article.strategy_eval_state, "pending")
        self.assertEqual(result["params"]["type"], "info")

    def test_evaluate_against_strategy_relevant(self):
        """Evaluation assigns labels when AI returns is_relevant=True."""
        ai_response = json.dumps({
            "is_relevant": True,
            "labels": ["EvalTestLabel"],
        })
        mock_result = {
            "content": ai_response,
            "usage": {"total_tokens": 100},
            "duration_ms": 300,
        }

        with patch.object(self.article.__class__, "_call_ai", return_value=mock_result):
            labels, reasoning = self.article._evaluate_against_strategy(self.strategy)

        self.assertIn(self.label, labels)

    def test_evaluate_against_strategy_not_relevant(self):
        """Evaluation returns empty recordset when AI returns is_relevant=False."""
        ai_response = json.dumps({
            "is_relevant": False,
            "labels": [],
        })
        mock_result = {
            "content": ai_response,
            "usage": {"total_tokens": 80},
            "duration_ms": 200,
        }

        with patch.object(self.article.__class__, "_call_ai", return_value=mock_result):
            labels, reasoning = self.article._evaluate_against_strategy(self.strategy)

        self.assertFalse(labels)

    def test_evaluate_against_strategy_unknown_label(self):
        """Unknown label names from AI are logged and skipped."""
        ai_response = json.dumps({
            "is_relevant": True,
            "labels": ["EvalTestLabel", "NonExistentLabel"],
        })
        mock_result = {
            "content": ai_response,
            "usage": {"total_tokens": 90},
            "duration_ms": 250,
        }

        with patch.object(self.article.__class__, "_call_ai", return_value=mock_result):
            labels, reasoning = self.article._evaluate_against_strategy(self.strategy)

        self.assertEqual(len(labels), 1)
        self.assertIn(self.label, labels)

    def test_cron_queues_pending_articles(self):
        """Cron queues evaluation jobs for scraped, pending articles."""
        article = _make_source_and_article(self.env, suffix="cron")
        self.assertEqual(article.strategy_eval_state, "pending")

        if trap_jobs:
            with trap_jobs() as trap:
                self.env["news.article"]._cron_strategy_eval_impl()
            self.assertGreater(len(trap.enqueued_jobs), 0)
        else:
            count = self.env["news.article"]._cron_strategy_eval_impl()
            self.assertGreaterEqual(count, 0)

    def test_evaluate_strategy_labels_sets_processed(self):
        """_evaluate_strategy_labels sets strategy_eval_state=processed."""
        article = _make_source_and_article(self.env, suffix="fulleval")

        ai_response = json.dumps({"is_relevant": False, "labels": []})
        mock_result = {
            "content": ai_response,
            "usage": {"total_tokens": 50},
            "duration_ms": 100,
        }

        with patch.object(article.__class__, "_call_ai", return_value=mock_result):
            article._evaluate_strategy_labels()

        self.assertEqual(article.strategy_eval_state, "processed")

    def test_evaluate_strategy_labels_no_active_strategies(self):
        """When no strategies have prompts, article is marked processed."""
        article = _make_source_and_article(self.env, suffix="noprompt")
        # Ensure this specific test has no strategies with prompts
        strategies_with_prompts = self.env["strategy.strategy"].search([
            ("digest_prompt", "!=", False),
            ("digest_prompt", "!=", ""),
        ])
        strategies_with_prompts.write({"digest_prompt": ""})

        article._evaluate_strategy_labels()
        self.assertEqual(article.strategy_eval_state, "processed")

    def test_bulk_reevaluate_action(self):
        """Bulk re-evaluate resets strategy_eval_state for scraped articles."""
        article1 = _make_source_and_article(self.env, suffix="bulk1")
        article2 = _make_source_and_article(self.env, suffix="bulk2")
        articles = article1 | article2
        articles.write({"strategy_eval_state": "processed"})

        if trap_jobs:
            with trap_jobs():
                result = articles.action_reevaluate_strategy_labels_bulk()
        else:
            with patch.object(
                article1.__class__,
                "_evaluate_strategy_labels",
                return_value=None,
            ):
                result = articles.action_reevaluate_strategy_labels_bulk()

        self.assertEqual(article1.strategy_eval_state, "pending")
        self.assertEqual(article2.strategy_eval_state, "pending")
        self.assertEqual(result["params"]["type"], "info")

    def test_bulk_reevaluate_no_scraped_articles(self):
        """Bulk re-evaluate returns warning when no articles are in scraped state."""
        source = self.env["news.source"].create({
            "name": "Pending Source bulk",
            "source_type": "website",
            "url": "https://pending-bulk.com",
        })
        snapshot = self.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": source.id,
            "raw_content": "<p>Content</p>",
        })
        pending_article = self.env["news.article"].create({
            "title": "Pending Article bulk",
            "snapshot_id": snapshot.id,
            "url": "https://pending-bulk.com/article",
            "state": "pending",
        })
        result = pending_article.action_reevaluate_strategy_labels_bulk()
        self.assertEqual(result["params"]["type"], "warning")

    def test_bulk_reevaluate_mixed_states_shows_skipped_count(self):
        """Bulk re-evaluate with mixed states shows skipped count in message."""
        scraped_article = _make_source_and_article(self.env, suffix="mixscraped")
        source2 = self.env["news.source"].create({
            "name": "MixPending Source",
            "source_type": "website",
            "url": "https://mixpending.com",
        })
        snapshot2 = self.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": source2.id,
            "raw_content": "<p>Content</p>",
        })
        pending_article = self.env["news.article"].create({
            "title": "MixPending Article",
            "snapshot_id": snapshot2.id,
            "url": "https://mixpending.com/article",
            "state": "pending",
        })
        articles = scraped_article | pending_article

        if trap_jobs:
            with trap_jobs():
                result = articles.action_reevaluate_strategy_labels_bulk()
        else:
            with patch.object(
                scraped_article.__class__,
                "_evaluate_strategy_labels",
                return_value=None,
            ):
                result = articles.action_reevaluate_strategy_labels_bulk()

        # Result should mention the skipped article
        self.assertIn("Skipped", result["params"]["message"])


@tagged("post_install", "-at_install")
class TestNewsArticleCallAI(TransactionCase):
    """Tests for _call_ai error branches."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.article = _make_source_and_article(cls.env, suffix="callai")

    def test_call_ai_no_api_key_raises_user_error(self):
        """_call_ai raises UserError when API key is not set."""
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": ""}):
            with self.assertRaises(UserError):
                self.article._call_ai("system", "user")

    def test_call_ai_timeout_raises_retryable(self):
        """_call_ai raises RetryableJobError on timeout."""
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": "test-key"}), \
             patch("requests.post", side_effect=requests.exceptions.Timeout()):
            with self.assertRaises(RetryableJobError):
                self.article._call_ai("system", "user")

    def test_call_ai_connection_error_raises_retryable(self):
        """_call_ai raises RetryableJobError on connection error."""
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": "test-key"}), \
             patch("requests.post", side_effect=requests.exceptions.ConnectionError("conn")):
            with self.assertRaises(RetryableJobError):
                self.article._call_ai("system", "user")

    def test_call_ai_transient_http_raises_retryable(self):
        """_call_ai raises RetryableJobError on transient HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": "test-key"}), \
             patch("requests.post", return_value=mock_response):
            with self.assertRaises(RetryableJobError):
                self.article._call_ai("system", "user")

    def test_call_ai_non_200_raises_value_error(self):
        """_call_ai raises ValueError on non-200 response."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": "test-key"}), \
             patch("requests.post", return_value=mock_response):
            with self.assertRaises(ValueError):
                self.article._call_ai("system", "user")

    def test_call_ai_malformed_response_raises_value_error(self):
        """_call_ai raises ValueError on malformed AI response structure."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": []}  # No message content
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": "test-key"}), \
             patch("requests.post", return_value=mock_response):
            with self.assertRaises(ValueError):
                self.article._call_ai("system", "user")

    def test_call_ai_success(self):
        """_call_ai returns content on successful response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "AI response text"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": "test-key"}), \
             patch("requests.post", return_value=mock_response):
            result = self.article._call_ai("system", "user")

        self.assertEqual(result["content"], "AI response text")
        self.assertEqual(result["usage"]["total_tokens"], 15)

    def test_parse_ai_json_with_think_blocks(self):
        """_parse_ai_json strips <think> blocks."""
        raw = '<think>thinking...</think>\n{"is_relevant": true}'
        result = self.article._parse_ai_json(raw)
        self.assertTrue(result["is_relevant"])

    def test_parse_ai_json_with_markdown_fences(self):
        """_parse_ai_json strips markdown code fences."""
        raw = '```json\n{"is_relevant": false}\n```'
        result = self.article._parse_ai_json(raw)
        self.assertFalse(result["is_relevant"])


@tagged("post_install", "-at_install")
class TestNewsArticleEvalCoverage(TransactionCase):
    """Additional coverage tests for edge cases in _evaluate_against_strategy."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.label = cls.env["strategy.label"].create({"name": "CoverageLabel"})
        cls.strategy = cls.env["strategy.strategy"].create({
            "name": "CoverageStrategy",
            "state": "active",
            "digest_prompt": "<p>Evaluate for coverage.</p>",
            "label_ids": [(4, cls.label.id)],
        })
        # Article with summary and content
        source = cls.env["news.source"].create({
            "name": "Coverage Source",
            "source_type": "website",
            "url": "https://coverage-test.com",
        })
        snapshot = cls.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": source.id,
            "raw_content": "<p>Coverage content</p>",
        })
        cls.article_with_content = cls.env["news.article"].create({
            "title": "Coverage Article with Summary",
            "snapshot_id": snapshot.id,
            "url": "https://coverage-test.com/article",
            "state": "scraped",
            "date": date.today(),
            "summary": "This is a test summary for coverage.",
            "content": "<p>Full article content for coverage testing.</p>",
        })

    def test_evaluate_with_summary_and_content(self):
        """Evaluation includes summary and content in article text."""
        ai_response = '{"is_relevant": true, "labels": ["CoverageLabel"]}'
        mock_result = {
            "content": ai_response,
            "usage": {"total_tokens": 50},
            "duration_ms": 100,
        }
        with patch.object(self.article_with_content.__class__, "_call_ai", return_value=mock_result):
            labels, reasoning = self.article_with_content._evaluate_against_strategy(self.strategy)
        self.assertIn(self.label, labels)

    def test_evaluate_json_parse_error_returns_empty(self):
        """JSON parse error in _evaluate_against_strategy returns empty labelset."""
        mock_result = {
            "content": "this is not json",
            "usage": {"total_tokens": 20},
            "duration_ms": 50,
        }
        with patch.object(self.article_with_content.__class__, "_call_ai", return_value=mock_result):
            labels, reasoning = self.article_with_content._evaluate_against_strategy(self.strategy)
        self.assertFalse(labels)

    def test_evaluate_labels_exception_in_strategy_eval(self):
        """Exception in _evaluate_against_strategy is caught and logged."""
        source = self.env["news.source"].create({
            "name": "ExcTest Source",
            "source_type": "website",
            "url": "https://exc-test.com",
        })
        snapshot = self.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": source.id,
            "raw_content": "<p>Content</p>",
        })
        article = self.env["news.article"].create({
            "title": "ExcTest Article",
            "snapshot_id": snapshot.id,
            "url": "https://exc-test.com/article",
            "state": "scraped",
            "date": date.today(),
        })

        with patch.object(article.__class__, "_evaluate_against_strategy",
                          side_effect=ValueError("unexpected error")):
            # Should not raise — exception is caught and logged
            article._evaluate_strategy_labels()
        # Article should still be marked as processed
        self.assertEqual(article.strategy_eval_state, "processed")

    def test_evaluate_against_strategy_non_list_labels(self):
        """AI returning labels as non-list is handled gracefully."""
        # AI returns labels as a string instead of list
        ai_response = '{"is_relevant": true, "labels": "CoverageLabel"}'
        mock_result = {
            "content": ai_response,
            "usage": {"total_tokens": 30},
            "duration_ms": 80,
        }
        with patch.object(self.article_with_content.__class__, "_call_ai", return_value=mock_result):
            labels, reasoning = self.article_with_content._evaluate_against_strategy(self.strategy)
        # Non-list labels should result in empty matched set
        self.assertFalse(labels)

    def test_evaluate_strategy_labels_retryable_reraises(self):
        """RetryableJobError from _evaluate_against_strategy is re-raised."""
        source = self.env["news.source"].create({
            "name": "Retryable Eval Source",
            "source_type": "website",
            "url": "https://retryable-eval.com",
        })
        snapshot = self.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": source.id,
            "raw_content": "<p>Content</p>",
        })
        article = self.env["news.article"].create({
            "title": "Retryable Eval Article",
            "snapshot_id": snapshot.id,
            "url": "https://retryable-eval.com/article",
            "state": "scraped",
            "date": date.today(),
        })
        with patch.object(article.__class__, "_evaluate_against_strategy",
                          side_effect=RetryableJobError("API timeout", seconds=300)):
            with self.assertRaises(RetryableJobError):
                article._evaluate_strategy_labels()

    def test_evaluate_assigns_labels_when_matched(self):
        """Labels are written to strategy_label_ids when evaluation returns matches."""
        source = self.env["news.source"].create({
            "name": "LabelAssign Source",
            "source_type": "website",
            "url": "https://labelassign.com",
        })
        snapshot = self.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": source.id,
            "raw_content": "<p>Content</p>",
        })
        article = self.env["news.article"].create({
            "title": "LabelAssign Article",
            "snapshot_id": snapshot.id,
            "url": "https://labelassign.com/article",
            "state": "scraped",
            "date": date.today(),
        })
        ai_response = '{"is_relevant": true, "labels": ["CoverageLabel"]}'
        mock_result = {"content": ai_response, "usage": {}, "duration_ms": 100}

        with patch.object(article.__class__, "_call_ai", return_value=mock_result):
            article._evaluate_strategy_labels()

        self.assertIn(self.label, article.strategy_label_ids)
        self.assertEqual(article.strategy_eval_state, "processed")


@tagged("post_install", "-at_install")
class TestNewsArticleHtmlConversion(TransactionCase):
    """Tests for HTML→Markdown conversion in article strategy evaluation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.label = cls.env["strategy.label"].create({"name": "HtmlConvEvalLabel"})
        cls.strategy_html = cls.env["strategy.strategy"].create({
            "name": "HtmlConvEvalStrategy",
            "state": "active",
            "digest_prompt": "<h2>Strategy Focus</h2><p>Evaluate articles about <strong>technology</strong>.</p>",
            "label_ids": [(4, cls.label.id)],
        })
        source = cls.env["news.source"].create({
            "name": "HtmlConvEvalSource",
            "source_type": "website",
            "url": "https://htmlconveval.com",
        })
        snapshot = cls.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": source.id,
            "raw_content": "<p>Content about technology.</p>",
        })
        cls.article = cls.env["news.article"].create({
            "title": "HtmlConvEval Article",
            "snapshot_id": snapshot.id,
            "url": "https://htmlconveval.com/article",
            "state": "scraped",
            "date": date.today(),
            "content": "<p>This article is about <strong>technology</strong> and innovation.</p>",
        })

    def test_evaluate_against_strategy_converts_html_prompt(self):
        """_evaluate_against_strategy converts HTML prompt to plain text before LLM call."""
        ai_response = json.dumps({"is_relevant": True, "labels": ["HtmlConvEvalLabel"]})
        mock_result = {"content": ai_response, "usage": {}, "duration_ms": 100}

        captured_calls = []

        def capture_call(system_prompt, user_content, temperature=0.1):
            captured_calls.append(system_prompt)
            return mock_result

        with patch.object(self.article.__class__, "_call_ai", side_effect=capture_call):
            self.article._evaluate_against_strategy(self.strategy_html)

        self.assertTrue(captured_calls)
        system_prompt = captured_calls[0]
        # HTML tags from prompt should NOT appear in the system prompt sent to LLM
        self.assertNotIn("<h2>", system_prompt)
        self.assertNotIn("<strong>", system_prompt)
        # But the text content should be present
        self.assertIn("technology", system_prompt)

    def test_evaluate_against_strategy_converts_article_content_html(self):
        """_evaluate_against_strategy converts article content HTML to plain text."""
        ai_response = json.dumps({"is_relevant": False, "labels": []})
        mock_result = {"content": ai_response, "usage": {}, "duration_ms": 100}

        captured_user_content = []

        def capture_call(system_prompt, user_content, temperature=0.1):
            captured_user_content.append(user_content)
            return mock_result

        with patch.object(self.article.__class__, "_call_ai", side_effect=capture_call):
            self.article._evaluate_against_strategy(self.strategy_html)

        self.assertTrue(captured_user_content)
        user_content = captured_user_content[0]
        # HTML tags from article content should NOT appear in user content
        self.assertNotIn("<p>", user_content)
        self.assertNotIn("<strong>", user_content)
        # But the text should be present
        self.assertIn("technology", user_content)
