"""Tests for news.log and news.log.entry models."""
import json
from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestNewsLog(TransactionCase):
    """Tests for news.log model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, queue_job__no_delay=True))
        cls.source = cls.env["news.source"].create({
            "name": "Log Test Source",
            "source_type": "website",
            "url": "https://log-test.example.com",
        })
        cls.snapshot = cls.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": cls.source.id,
            "raw_content": "<p>Content</p>",
        })
        cls.article = cls.env["news.article"].create({
            "title": "Log Test Article",
            "snapshot_id": cls.snapshot.id,
        })

    def _create_log(self, level="success", category="extraction", message="Test log"):
        return self.env["news.log"].create({
            "level": level,
            "category": category,
            "message": message,
            "source_id": self.source.id,
            "snapshot_id": self.snapshot.id,
            "article_id": self.article.id,
        })

    def test_log_defaults(self):
        """Log should have correct defaults."""
        log = self._create_log()
        self.assertEqual(log.level, "success")
        self.assertEqual(log.category, "extraction")
        self.assertTrue(log.timestamp)

    def test_log_created_article_count_empty(self):
        """Log with no created articles should have count 0."""
        log = self._create_log()
        self.assertEqual(log.created_article_count, 0)

    def test_log_created_article_count_with_articles(self):
        """Log with linked articles should have correct count."""
        log = self._create_log()
        log.created_article_ids = [(4, self.article.id)]
        self.assertEqual(log.created_article_count, 1)

    def test_action_view_created_articles(self):
        """action_view_created_articles should return window action."""
        log = self._create_log()
        log.created_article_ids = [(4, self.article.id)]
        result = log.action_view_created_articles()
        self.assertEqual(result["type"], "ir.actions.act_window")
        self.assertEqual(result["res_model"], "news.article")

    def test_related_source_name(self):
        """Log should expose source name via related field."""
        log = self._create_log()
        self.assertEqual(log.source_name, self.source.name)

    def test_related_article_title(self):
        """Log should expose article title via related field."""
        log = self._create_log()
        self.assertEqual(log.article_title, self.article.title)


@tagged("post_install", "-at_install")
class TestNewsLogEntry(TransactionCase):
    """Tests for news.log.entry model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, queue_job__no_delay=True))
        cls.source = cls.env["news.source"].create({
            "name": "Entry Test Source",
            "source_type": "website",
            "url": "https://entry-test.example.com",
        })
        cls.log = cls.env["news.log"].create({
            "level": "success",
            "category": "extraction",
            "message": "Parent log for entry tests",
            "source_id": cls.source.id,
        })

    def _create_entry(self, level="info", message="Test entry", metadata=None):
        vals = {
            "log_id": cls.log.id,
            "level": level,
            "message": message,
        }
        if metadata:
            vals["metadata"] = json.dumps(metadata) if isinstance(metadata, dict) else metadata
        return cls.env["news.log.entry"].create(vals)

    def setUp(self):
        super().setUp()
        self._cls_log = self.log

    def test_entry_metadata_pretty_json(self):
        """metadata_pretty should format JSON for display."""
        entry = self.env["news.log.entry"].create({
            "log_id": self._cls_log.id,
            "level": "info",
            "message": "JSON test",
            "metadata": json.dumps({"key": "value", "count": 42}),
        })
        self.assertIn('"key"', entry.metadata_pretty)
        self.assertIn('"value"', entry.metadata_pretty)

    def test_entry_metadata_pretty_invalid_json(self):
        """metadata_pretty should return raw metadata when JSON is invalid."""
        entry = self.env["news.log.entry"].create({
            "log_id": self._cls_log.id,
            "level": "info",
            "message": "Non-JSON test",
            "metadata": "plain text metadata",
        })
        self.assertEqual(entry.metadata_pretty, "plain text metadata")

    def test_entry_metadata_pretty_empty(self):
        """metadata_pretty should return empty string when no metadata."""
        entry = self.env["news.log.entry"].create({
            "log_id": self._cls_log.id,
            "level": "info",
            "message": "No metadata",
        })
        self.assertEqual(entry.metadata_pretty, "")

    def test_action_view_metadata(self):
        """action_view_metadata should return a form popup action."""
        entry = self.env["news.log.entry"].create({
            "log_id": self._cls_log.id,
            "level": "info",
            "message": "View metadata test",
        })
        result = entry.action_view_metadata()
        self.assertEqual(result["type"], "ir.actions.act_window")
        self.assertEqual(result["res_model"], "news.log.entry")
        self.assertEqual(result["target"], "new")

    def test_gc_removes_old_success_entries(self):
        """_gc_successful_log_entries should delete old success entries."""
        # Create a success log with an old entry
        success_log = self.env["news.log"].create({
            "level": "success",
            "category": "extraction",
            "message": "GC test log",
            "source_id": self._cls_log.source_id.id,
        })
        old_entry = self.env["news.log.entry"].create({
            "log_id": success_log.id,
            "level": "info",
            "message": "Old entry to be GCed",
        })
        # Make the entry appear old (> 1 day ago) by writing timestamp directly
        self.env.cr.execute(
            "UPDATE news_log_entry SET timestamp = %s WHERE id = %s",
            [fields.Datetime.now() - timedelta(days=2), old_entry.id],
        )
        # Run GC
        result = self.env["news.log.entry"]._gc_successful_log_entries()
        # Entry should be deleted
        self.assertFalse(old_entry.exists())
        self.assertIn("Deleted", result)

    def test_gc_keeps_recent_success_entries(self):
        """_gc_successful_log_entries should keep recent success entries."""
        success_log = self.env["news.log"].create({
            "level": "success",
            "category": "extraction",
            "message": "Recent GC test log",
            "source_id": self._cls_log.source_id.id,
        })
        recent_entry = self.env["news.log.entry"].create({
            "log_id": success_log.id,
            "level": "info",
            "message": "Recent entry, should not be GCed",
        })
        result = self.env["news.log.entry"]._gc_successful_log_entries()
        # Recent entry should still exist
        self.assertTrue(recent_entry.exists())

    def test_gc_keeps_error_entries(self):
        """_gc_successful_log_entries should not delete entries from error logs."""
        error_log = self.env["news.log"].create({
            "level": "error",
            "category": "extraction",
            "message": "Error GC test log",
            "source_id": self._cls_log.source_id.id,
        })
        error_entry = self.env["news.log.entry"].create({
            "log_id": error_log.id,
            "level": "error",
            "message": "Error entry, should NOT be GCed",
        })
        # Make old
        self.env.cr.execute(
            "UPDATE news_log_entry SET timestamp = %s WHERE id = %s",
            [fields.Datetime.now() - timedelta(days=2), error_entry.id],
        )
        self.env["news.log.entry"]._gc_successful_log_entries()
        # Error entry should still exist
        self.assertTrue(error_entry.exists())
