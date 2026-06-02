import json as json_mod
from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


def _make_source_and_article(env, suffix=""):
    source = env["news.source"].create({
        "name": f"WatchTest Source {suffix}",
        "source_type": "website",
        "url": f"https://watchtest{suffix}.com",
    })
    snapshot = env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
        "source_id": source.id,
        "raw_content": "<p>Test content for watch.</p>",
    })
    article = env["news.article"].create({
        "title": f"Watch Test Article {suffix}",
        "snapshot_id": snapshot.id,
        "url": f"https://watchtest{suffix}.com/article",
        "state": "scraped",
        "content": "<p>Strategic policy change announcement.</p>",
        "summary": "Important policy change.",
    })
    return article


@tagged("post_install", "-at_install")
class TestStrategyWatchArticle(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.StrategyStrategy = cls.env["strategy.strategy"]
        cls.StrategyLabel = cls.env["strategy.label"]

        cls.strategy = cls.StrategyStrategy.create({
            "name": "Watch Test Strategy",
            "state": "active",
            "watch_prompt": "<p>Flag articles about policy changes and regulatory developments.</p>",
        })

    def _mock_ai_result(self, is_watch_relevant=True, reasoning="Test reasoning."):
        return {
            "content": json_mod.dumps({
                "is_watch_relevant": is_watch_relevant,
                "reasoning": reasoning,
            }),
            "usage": {"total_tokens": 50},
            "duration_ms": 100,
        }

    def test_strategy_watch_defaults_false(self):
        """New article has strategy_watch = False by default."""
        article = _make_source_and_article(self.env, suffix="default")
        self.assertFalse(article.strategy_watch)
        self.assertEqual(article.strategy_watch_state, "pending")

    def test_watch_eval_sets_watch_true(self):
        """Watch evaluation sets strategy_watch = True when AI flags it."""
        article = _make_source_and_article(self.env, suffix="flagged")

        with patch.object(article.__class__, "_call_ai",
                          return_value=self._mock_ai_result(is_watch_relevant=True)):
            article._evaluate_strategy_watch()

        self.assertTrue(article.strategy_watch)
        self.assertEqual(article.strategy_watch_state, "processed")
        self.assertIn("Test reasoning.", article.strategy_watch_reasoning)

    def test_watch_eval_sets_watch_false(self):
        """Watch evaluation keeps strategy_watch = False when AI does not flag it."""
        article = _make_source_and_article(self.env, suffix="notflagged")

        with patch.object(article.__class__, "_call_ai",
                          return_value=self._mock_ai_result(is_watch_relevant=False)):
            article._evaluate_strategy_watch()

        self.assertFalse(article.strategy_watch)
        self.assertEqual(article.strategy_watch_state, "processed")

    def test_watch_eval_skips_already_processed(self):
        """Watch evaluation skips articles already in processed state."""
        article = _make_source_and_article(self.env, suffix="skip")
        article.write({"strategy_watch_state": "processed", "strategy_watch": True})

        article._evaluate_strategy_watch()
        # Should not have made any AI call or changed state
        self.assertTrue(article.strategy_watch)
        self.assertEqual(article.strategy_watch_state, "processed")

    def test_watch_eval_no_active_strategies(self):
        """Watch eval marks as processed when no active strategies with watch prompt."""
        self.strategy.write({"state": "draft"})
        article = _make_source_and_article(self.env, suffix="nostrat")

        article._evaluate_strategy_watch()
        self.assertEqual(article.strategy_watch_state, "processed")
        self.assertFalse(article.strategy_watch)

    def test_watch_eval_empty_watch_prompt(self):
        """Watch eval marks as processed when strategy has empty watch_prompt."""
        self.strategy.write({"description": "Test description.", "state": "active", "watch_prompt": ""})
        article = _make_source_and_article(self.env, suffix="emptyprompt")

        article._evaluate_strategy_watch()
        self.assertEqual(article.strategy_watch_state, "processed")

    def test_manual_reevaluate_clears_data(self):
        """Manual re-evaluation clears watch data and re-queues."""
        article = _make_source_and_article(self.env, suffix="manual")
        article.write({
            "strategy_watch_state": "processed",
            "strategy_watch": True,
            "strategy_watch_reasoning": "Old reasoning.",
        })

        article.action_reevaluate_strategy_watch()
        self.assertEqual(article.strategy_watch_state, "pending")
        self.assertFalse(article.strategy_watch)
        self.assertFalse(article.strategy_watch_reasoning)

    def test_evaluate_watch_json_parse_error(self):
        """Watch eval handles invalid JSON gracefully."""
        article = _make_source_and_article(self.env, suffix="badjson")

        mock_result = {
            "content": "not valid json",
            "usage": {},
            "duration_ms": 100,
        }
        with patch.object(article.__class__, "_call_ai", return_value=mock_result):
            article._evaluate_strategy_watch()

        self.assertEqual(article.strategy_watch_state, "processed")
        self.assertFalse(article.strategy_watch)

    def test_evaluate_strategies_dispatches_to_watch(self):
        """_evaluate_strategies calls _evaluate_strategy_watch."""
        article = _make_source_and_article(self.env, suffix="dispatch")

        call_records = []
        def track_call():
            call_records.append(True)

        with patch.object(article.__class__, "_evaluate_strategy_watch",
                          side_effect=lambda: track_call()), \
             patch.object(article.__class__, "_evaluate_strategy_labels"):
            article._evaluate_strategies()

        self.assertEqual(len(call_records), 1)


@tagged("post_install", "-at_install")
class TestStrategyWatchDistillation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.StrategyStrategy = cls.env["strategy.strategy"]

    def _mock_distill_response(self, prompt="Watch for policy changes and regulatory shifts."):
        return {
            "content": json_mod.dumps({"prompt": prompt}),
            "usage": {"total_tokens": 100},
            "duration_ms": 200,
        }

    def test_distill_watch_prompt_from_description(self):
        """Distill watch prompt from strategy description."""
        strategy = self.StrategyStrategy.create({
            "name": "Watch Distill Test",
            "description": "Focus on policy developments in the social sector.",
        })

        with patch.object(strategy.__class__, "_call_ai",
                          return_value=self._mock_distill_response()):
            result = strategy.action_distill_watch_prompt()

        self.assertIn("Watch for policy changes", strategy.watch_prompt)
        self.assertEqual(result["type"], "ir.actions.client")
        self.assertEqual(result["tag"], "display_notification")

    def test_distill_watch_prompt_empty_raises(self):
        """Distill raises UserError when AI returns empty prompt."""
        strategy = self.StrategyStrategy.create({
            "name": "Empty Watch Distill",
            "description": "Some content.",
        })

        mock_result = {
            "content": json_mod.dumps({"prompt": ""}),
            "usage": {},
            "duration_ms": 100,
        }
        with patch.object(strategy.__class__, "_call_ai", return_value=mock_result):
            with self.assertRaises(UserError):
                strategy.action_distill_watch_prompt()

    def test_distill_watch_prompt_invalid_json_raises(self):
        """Distill raises UserError when AI returns invalid JSON."""
        strategy = self.StrategyStrategy.create({
            "name": "Bad JSON Watch Distill",
            "description": "Content.",
        })

        mock_result = {
            "content": "not json",
            "usage": {},
            "duration_ms": 100,
        }
        with patch.object(strategy.__class__, "_call_ai", return_value=mock_result):
            with self.assertRaises(UserError):
                strategy.action_distill_watch_prompt()

    def test_distill_watch_prompt_no_content_raises(self):
        """Distill raises UserError when strategy has no content."""
        strategy = self.StrategyStrategy.create({"name": "No Content Watch"})
        with self.assertRaises(UserError):
            strategy.action_distill_watch_prompt()

    def test_distill_watch_prompt_overwrite_wizard(self):
        """Distill opens confirmation wizard when watch_prompt already exists."""
        strategy = self.StrategyStrategy.create({
            "name": "Overwrite Watch Test",
            "description": "New content.",
            "watch_prompt": "<p>Existing watch prompt.</p>",
        })
        result = strategy.action_distill_watch_prompt()
        self.assertEqual(result["type"], "ir.actions.act_window")
        self.assertEqual(result["res_model"], "strategy.distill.confirm")