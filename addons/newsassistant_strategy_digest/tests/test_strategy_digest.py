import os
from datetime import date
from unittest.mock import MagicMock, patch

import requests

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged

try:
    from odoo.addons.queue_job.exception import RetryableJobError
except ImportError:  # pragma: no cover
    RetryableJobError = Exception  # pragma: no cover


def _make_article_with_label(env, title, label, article_date=None, suffix=""):
    if article_date is None:
        article_date = date(2026, 6, 15)
    source = env["news.source"].create({
        "name": f"DigestSrc {suffix or title[:8]}",
        "source_type": "website",
        "url": f"https://digesttest-{suffix or title[:5].lower().replace(' ', '')}.com",
    })
    snapshot = env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
        "source_id": source.id,
        "raw_content": f"<p>Content for {title}</p>",
    })
    article = env["news.article"].create({
        "title": title,
        "snapshot_id": snapshot.id,
        "url": f"https://digesttest-{suffix or title[:5].lower().replace(' ', '')}.com/article",
        "state": "scraped",
        "date": article_date,
        "strategy_label_ids": [(4, label.id)],
    })
    return article


@tagged("post_install", "-at_install")
class TestStrategyDigest(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.StrategyDigest = cls.env["strategy.digest"]
        cls.StrategyStrategy = cls.env["strategy.strategy"]
        cls.StrategyLabel = cls.env["strategy.label"]

        cls.label = cls.StrategyLabel.create({"name": "DigestTestLabel"})
        cls.strategy_eternal = cls.StrategyStrategy.create({
            "name": "EternalDigestStrategy",
            "state": "active",
            "prompt": "<p>Test prompt for strategy evaluation.</p>",
            "label_ids": [(4, cls.label.id)],
        })
        cls.strategy_2026 = cls.StrategyStrategy.create({
            "name": "2026DigestStrategy",
            "state": "active",
            "date_from": date(2026, 1, 1),
            "date_to": date(2026, 12, 31),
            "prompt": "<p>Test prompt for 2026 strategy.</p>",
            "label_ids": [(4, cls.label.id)],
        })
        cls.strategy_2025 = cls.StrategyStrategy.create({
            "name": "2025OnlyDigestStrategy",
            "state": "active",
            "date_from": date(2025, 1, 1),
            "date_to": date(2025, 12, 31),
            "prompt": "<p>Old prompt.</p>",
        })

        cls.article_in_period = _make_article_with_label(
            cls.env,
            title="Digest Article InPeriod",
            label=cls.label,
            article_date=date(2026, 6, 15),
            suffix="inperiod",
        )
        cls.article_out_of_period = _make_article_with_label(
            cls.env,
            title="Digest Article OutPeriod",
            label=cls.label,
            article_date=date(2025, 3, 1),
            suffix="outperiod",
        )

    def _make_digest(self, date_from=None, date_to=None, name="Test Digest"):
        return self.StrategyDigest.create({
            "name": name,
            "date_from": date_from or date(2026, 1, 1),
            "date_to": date_to or date(2026, 12, 31),
        })

    # -------------------------------------------------------------------------
    # Model tests
    # -------------------------------------------------------------------------

    def test_create_digest(self):
        """Digest can be created with required fields."""
        digest = self._make_digest(name="Create Test Digest")
        self.assertEqual(digest.state, "draft")
        self.assertFalse(digest.brief)

    def test_state_clickable_via_write(self):
        """State can be set directly via write (statusbar is clickable)."""
        digest = self._make_digest(name="Clickable State Digest")
        digest.write({"state": "done"})
        self.assertEqual(digest.state, "done")
        digest.write({"state": "draft"})
        self.assertEqual(digest.state, "draft")

    def test_has_brief_false_when_empty(self):
        """has_brief is False when brief is empty, whitespace-only, or editor artefact HTML."""
        digest = self._make_digest(name="HasBrief Empty Digest")
        self.assertFalse(digest.has_brief)
        digest.write({"brief": "<p><br></p>"})
        self.assertFalse(digest.has_brief)
        digest.write({"brief": '<h2 data-oe-version="1.2"><br></h2>'})
        self.assertFalse(digest.has_brief)

    def test_has_brief_true_when_content(self):
        """has_brief is True when brief has real text content."""
        digest = self._make_digest(name="HasBrief Content Digest")
        digest.write({"brief": "<h2>Summary</h2><p>Content.</p>"})
        self.assertTrue(digest.has_brief)

    def test_date_validation(self):
        """date_from > date_to raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.StrategyDigest.create({
                "name": "Invalid Dates Test",
                "date_from": date(2026, 12, 31),
                "date_to": date(2026, 1, 1),
            })

    # -------------------------------------------------------------------------
    # Period resolution tests
    # -------------------------------------------------------------------------

    def test_get_active_strategies_includes_eternal(self):
        """Eternal strategy is included in any period."""
        digest = self._make_digest(date(2026, 1, 1), date(2026, 12, 31), "StratTest Eternal")
        strategies = digest._get_active_strategies_for_period()
        self.assertIn(self.strategy_eternal, strategies)

    def test_get_active_strategies_includes_overlapping(self):
        """Strategy overlapping the period is included."""
        digest = self._make_digest(date(2026, 1, 1), date(2026, 12, 31), "StratTest 2026")
        strategies = digest._get_active_strategies_for_period()
        self.assertIn(self.strategy_2026, strategies)

    def test_get_active_strategies_excludes_past(self):
        """Strategy entirely in the past is excluded."""
        digest = self._make_digest(date(2026, 1, 1), date(2026, 12, 31), "StratTest Excl")
        strategies = digest._get_active_strategies_for_period()
        self.assertNotIn(self.strategy_2025, strategies)

    def test_get_articles_for_period_includes_in_period(self):
        """Articles with labels and date in period are included."""
        digest = self._make_digest(date(2026, 1, 1), date(2026, 12, 31), "ArtTest Incl")
        articles = digest._get_articles_for_period()
        self.assertIn(self.article_in_period, articles)

    def test_get_articles_for_period_excludes_out_of_period(self):
        """Articles outside the date range are excluded."""
        digest = self._make_digest(date(2026, 1, 1), date(2026, 12, 31), "ArtTest Excl")
        articles = digest._get_articles_for_period()
        self.assertNotIn(self.article_out_of_period, articles)

    def test_get_articles_excludes_unlabelled(self):
        """Articles without strategy labels are excluded."""
        source = self.env["news.source"].create({
            "name": "Unlabelled DigestSrc",
            "source_type": "website",
            "url": "https://unlabelled-digest.com",
        })
        snapshot = self.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": source.id,
            "raw_content": "<p>Content</p>",
        })
        unlabelled_article = self.env["news.article"].create({
            "title": "Unlabelled Digest Article",
            "snapshot_id": snapshot.id,
            "url": "https://unlabelled-digest.com/art",
            "state": "scraped",
            "date": date(2026, 6, 1),
        })
        digest = self._make_digest(date(2026, 1, 1), date(2026, 12, 31), "ArtTest Unlabelled")
        articles = digest._get_articles_for_period()
        self.assertNotIn(unlabelled_article, articles)

    # -------------------------------------------------------------------------
    # action_generate_brief tests
    # -------------------------------------------------------------------------

    def test_generate_brief_no_articles_raises_user_error(self):
        """Generate brief with no articles raises UserError."""
        digest = self._make_digest(date(2020, 1, 1), date(2020, 12, 31), "Empty Period Digest")
        with self.assertRaises(UserError):
            digest.action_generate_brief()

    def test_generate_brief_success(self):
        """Generate brief calls AI and stores result."""
        digest = self._make_digest(date(2026, 1, 1), date(2026, 12, 31), "Brief Gen Digest")

        mock_html = "<h2>Executive Summary</h2><p>Test brief content.</p>"
        mock_result = {
            "content": mock_html,
            "usage": {"total_tokens": 500},
            "duration_ms": 1200,
        }

        with patch.object(digest.__class__, "_call_ai", return_value=mock_result):
            result = digest.action_generate_brief()

        self.assertIn("Executive Summary", digest.brief)
        self.assertIn(self.article_in_period, digest.article_ids)
        self.assertTrue(digest.has_brief)
        self.assertFalse(result)

    def test_generate_brief_can_regenerate(self):
        """Brief can be regenerated (overwrite) even when state is done."""
        digest = self._make_digest(date(2026, 1, 1), date(2026, 12, 31), "Regen Digest")

        mock_html_v1 = "<h2>Version 1</h2>"
        mock_html_v2 = "<h2>Version 2</h2>"

        mock_v1 = {"content": mock_html_v1, "usage": {}, "duration_ms": 100}
        mock_v2 = {"content": mock_html_v2, "usage": {}, "duration_ms": 100}

        with patch.object(digest.__class__, "_call_ai", return_value=mock_v1):
            digest.action_generate_brief()
        self.assertIn("Version 1", digest.brief)

        with patch.object(digest.__class__, "_call_ai", return_value=mock_v2):
            digest.action_generate_brief()
        self.assertIn("Version 2", digest.brief)

    def test_build_brief_prompt_german(self):
        """Brief prompt includes German instruction for de_DE."""
        digest = self._make_digest(date(2026, 1, 1), date(2026, 12, 31), "German Lang Digest")
        strategies = digest._get_active_strategies_for_period()
        articles = digest._get_articles_for_period()

        system_prompt, user_content = digest._build_brief_prompt(strategies, articles, "de_DE")
        self.assertIn("German", system_prompt)
        self.assertIn(str(date(2026, 1, 1)), user_content)

    def test_build_brief_prompt_french(self):
        """Brief prompt uses French for fr language code."""
        digest = self._make_digest(date(2026, 1, 1), date(2026, 12, 31), "French Lang Digest")
        strategies = digest._get_active_strategies_for_period()
        articles = digest._get_articles_for_period()

        system_prompt, _ = digest._build_brief_prompt(strategies, articles, "fr_FR")
        self.assertIn("French", system_prompt)

    def test_build_brief_prompt_english_fallback(self):
        """Brief prompt defaults to English for unknown language."""
        digest = self._make_digest(date(2026, 1, 1), date(2026, 12, 31), "English Fallback")
        strategies = digest._get_active_strategies_for_period()
        articles = digest._get_articles_for_period()

        system_prompt, _ = digest._build_brief_prompt(strategies, articles, "xx_XX")
        self.assertIn("English", system_prompt)

    def test_build_brief_prompt_with_article_summary(self):
        """Brief prompt includes article summary when available."""
        digest = self._make_digest(date(2026, 1, 1), date(2026, 12, 31), "Summary Article Test")
        original_summary = self.article_in_period.summary
        self.article_in_period.write({"summary": "This is an important test summary."})

        strategies = digest._get_active_strategies_for_period()
        articles = digest._get_articles_for_period()
        _, user_content = digest._build_brief_prompt(strategies, articles, "en_US")

        self.assertIn("This is an important test summary.", user_content)
        self.article_in_period.write({"summary": original_summary or False})

    def test_build_brief_prompt_truncates_large_article_set(self):
        """Brief prompt includes truncation note when more than 50 articles."""
        digest = self._make_digest(date(2026, 1, 1), date(2026, 12, 31), "Large Set Test")
        label = self.env["strategy.label"].create({"name": "LargeSetTestLabel"})

        # Create 51 articles to exceed MAX_ARTICLES_IN_BRIEF
        articles_list = []
        for i in range(51):
            source_i = self.env["news.source"].create({
                "name": f"LargeSetSrc {i}",
                "source_type": "website",
                "url": f"https://largeset-test-{i}.com",
            })
            snap_i = self.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
                "source_id": source_i.id,
                "raw_content": "<p>Content</p>",
            })
            art_i = self.env["news.article"].create({
                "title": f"LargeSet Art {i}",
                "snapshot_id": snap_i.id,
                "url": f"https://largeset-test-{i}.com/article",
                "state": "scraped",
                "date": date(2026, 6, 1),
                "strategy_label_ids": [(4, label.id)],
            })
            articles_list.append(art_i)

        all_articles = articles_list[0]
        for a in articles_list[1:]:
            all_articles |= a

        strategies = self.env["strategy.strategy"].search([])
        _, user_content = digest._build_brief_prompt(strategies, all_articles, "en_US")
        self.assertIn("additional articles", user_content)
        self.assertIn("omitted for brevity", user_content)


@tagged("post_install", "-at_install")
class TestStrategyDigestCallAI(TransactionCase):
    """Tests for _call_ai error branches on strategy.digest."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.digest = cls.env["strategy.digest"].create({
            "name": "CallAI Test Digest",
            "date_from": date(2026, 1, 1),
            "date_to": date(2026, 12, 31),
        })

    def test_call_ai_no_api_key_raises_user_error(self):
        """_call_ai raises UserError when API key is not set."""
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": ""}):
            with self.assertRaises(UserError):
                self.digest._call_ai("system", "user")

    def test_call_ai_timeout_raises_retryable(self):
        """_call_ai raises RetryableJobError on timeout."""
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": "test-key"}), \
             patch("requests.post", side_effect=requests.exceptions.Timeout()):
            with self.assertRaises(RetryableJobError):
                self.digest._call_ai("system", "user")

    def test_call_ai_connection_error_raises_retryable(self):
        """_call_ai raises RetryableJobError on connection error."""
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": "test-key"}), \
             patch("requests.post", side_effect=requests.exceptions.ConnectionError("conn")):
            with self.assertRaises(RetryableJobError):
                self.digest._call_ai("system", "user")

    def test_call_ai_transient_http_raises_retryable(self):
        """_call_ai raises RetryableJobError on transient HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": "test-key"}), \
             patch("requests.post", return_value=mock_response):
            with self.assertRaises(RetryableJobError):
                self.digest._call_ai("system", "user")

    def test_call_ai_non_200_raises_value_error(self):
        """_call_ai raises ValueError on non-200 response."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": "test-key"}), \
             patch("requests.post", return_value=mock_response):
            with self.assertRaises(ValueError):
                self.digest._call_ai("system", "user")

    def test_call_ai_malformed_response_raises_value_error(self):
        """_call_ai raises ValueError on malformed response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": []}
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": "test-key"}), \
             patch("requests.post", return_value=mock_response):
            with self.assertRaises(ValueError):
                self.digest._call_ai("system", "user")

    def test_call_ai_success(self):
        """_call_ai returns content dict on success."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "<h2>Brief</h2>"}}],
            "usage": {"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150},
        }
        with patch.dict(os.environ, {"INFOMANIAK_AI_API_KEY": "test-key"}), \
             patch("requests.post", return_value=mock_response):
            result = self.digest._call_ai("system", "user")
        self.assertEqual(result["content"], "<h2>Brief</h2>")
        self.assertEqual(result["usage"]["total_tokens"], 150)

    def test_generate_brief_retryable_error_reraises(self):
        """action_generate_brief re-raises RetryableJobError from AI call."""
        digest = self.env["strategy.digest"].create({
            "name": "Retryable Brief Digest",
            "date_from": date(2026, 1, 1),
            "date_to": date(2026, 12, 31),
        })
        label = self.env["strategy.label"].create({"name": "RetryableBriefLabel"})
        source = self.env["news.source"].create({
            "name": "RetryableBrief Source",
            "source_type": "website",
            "url": "https://retryablebrief.com",
        })
        snapshot = self.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": source.id,
            "raw_content": "<p>Content</p>",
        })
        self.env["news.article"].create({
            "title": "RetryableBrief Article",
            "snapshot_id": snapshot.id,
            "url": "https://retryablebrief.com/article",
            "state": "scraped",
            "date": date(2026, 6, 1),
            "strategy_label_ids": [(4, label.id)],
        })

        with patch.object(digest.__class__, "_call_ai",
                          side_effect=RetryableJobError("timeout", seconds=300)):
            with self.assertRaises(RetryableJobError):
                digest.action_generate_brief()

    def test_generate_brief_ai_error_raises_user_error(self):
        """action_generate_brief raises UserError when AI call fails."""
        # Add a labelled article so we don't hit the "no articles" error
        label = self.env["strategy.label"].create({"name": "DigestCallAILabel"})
        source = self.env["news.source"].create({
            "name": "DigestCallAI Source",
            "source_type": "website",
            "url": "https://digestcallai.com",
        })
        snapshot = self.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": source.id,
            "raw_content": "<p>Content</p>",
        })
        self.env["news.article"].create({
            "title": "DigestCallAI Article",
            "snapshot_id": snapshot.id,
            "url": "https://digestcallai.com/article",
            "state": "scraped",
            "date": date(2026, 6, 1),
            "strategy_label_ids": [(4, label.id)],
        })

        with patch.object(self.digest.__class__, "_call_ai", side_effect=Exception("AI error")):
            with self.assertRaises(UserError):
                self.digest.action_generate_brief()

    def test_generate_brief_strips_markdown_fences(self):
        """action_generate_brief strips markdown fences from AI output."""
        digest = self.env["strategy.digest"].create({
            "name": "Fence Strip Digest",
            "date_from": date(2026, 1, 1),
            "date_to": date(2026, 12, 31),
        })
        label = self.env["strategy.label"].create({"name": "FenceStripLabel"})
        source = self.env["news.source"].create({
            "name": "FenceStrip Source",
            "source_type": "website",
            "url": "https://fencestrip.com",
        })
        snapshot = self.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": source.id,
            "raw_content": "<p>Content</p>",
        })
        self.env["news.article"].create({
            "title": "FenceStrip Article",
            "snapshot_id": snapshot.id,
            "url": "https://fencestrip.com/article",
            "state": "scraped",
            "date": date(2026, 6, 1),
            "strategy_label_ids": [(4, label.id)],
        })

        # AI returns HTML wrapped in markdown fences
        mock_result = {
            "content": "```html\n<h2>Summary</h2>\n<p>Content</p>\n```",
            "usage": {},
            "duration_ms": 100,
        }
        with patch.object(digest.__class__, "_call_ai", return_value=mock_result):
            digest.action_generate_brief()

        self.assertIn("<h2>Summary</h2>", digest.brief)
        self.assertNotIn("```", digest.brief)


@tagged("post_install", "-at_install")
class TestStrategyDigestHtmlConversion(TransactionCase):
    """Tests for HTML→Markdown conversion in digest brief generation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.StrategyDigest = cls.env["strategy.digest"]
        cls.StrategyStrategy = cls.env["strategy.strategy"]
        cls.StrategyLabel = cls.env["strategy.label"]

        cls.label = cls.StrategyLabel.create({"name": "HtmlConvTestLabel"})
        cls.strategy_html = cls.StrategyStrategy.create({
            "name": "HtmlConvTestStrategy",
            "state": "active",
            "prompt": "<h2>Focus Areas</h2><p>Evaluate articles about <strong>innovation</strong>.</p>",
            "label_ids": [(4, cls.label.id)],
        })

    def test_build_brief_prompt_converts_html_prompt_to_text(self):
        """_build_brief_prompt converts HTML strategy prompt to plain text for LLM."""
        digest = self.StrategyDigest.create({
            "name": "HtmlConv Digest",
            "date_from": date(2026, 1, 1),
            "date_to": date(2026, 12, 31),
        })
        source = self.env["news.source"].create({
            "name": "HtmlConvSrc",
            "source_type": "website",
            "url": "https://htmlconv-test.com",
        })
        snapshot = self.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": source.id,
            "raw_content": "<p>Article content</p>",
        })
        article = self.env["news.article"].create({
            "title": "HtmlConv Article",
            "snapshot_id": snapshot.id,
            "url": "https://htmlconv-test.com/article",
            "state": "scraped",
            "date": date(2026, 6, 15),
            "strategy_label_ids": [(4, self.label.id)],
        })

        strategies = self.strategy_html
        articles = article
        _, user_content = digest._build_brief_prompt(strategies, articles, "en_US")

        # Prompt should be plain text — no raw HTML tags in the brief prompt
        self.assertNotIn("<h2>", user_content)
        self.assertNotIn("<strong>", user_content)
        # But the text content should be there
        self.assertIn("innovation", user_content)
