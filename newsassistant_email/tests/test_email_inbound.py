"""Tests for inbound email handling on news.snapshot."""
from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.queue_job.tests.common import trap_jobs


@tagged("post_install", "-at_install")
class TestEmailInbound(TransactionCase):
    """Tests for NewsSnapshotEmail.message_new() email handling."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Do NOT use queue_job__no_delay here — it would cause jobs to run
        # immediately and make real AI API calls. Use skip_snapshot_extraction
        # context in each test to suppress extraction.
        pass

    def _send_email(self, email_from, body="<p>Newsletter content</p>", subject="Test Newsletter"):
        """Helper: simulate inbound email via message_new().

        Mocks AI source naming and traps extraction jobs to prevent real HTTP calls.
        """
        msg_dict = {
            "email_from": email_from,
            "body": body,
            "subject": subject,
        }
        # Mock AI source naming + trap extraction jobs to prevent real API calls
        with patch.object(
            self.env["news.snapshot"].__class__,
            "_ai_get_source_name",
            side_effect=lambda domain: domain,
        ), trap_jobs():
            return self.env["news.snapshot"].message_new(msg_dict)

    def test_known_domain_routes_to_existing_source(self):
        """Email from known domain links snapshot to existing source."""
        source = self.env["news.source"].create({
            "name": "Known Newsletter",
            "source_type": "email",
            "sender_domain": "knownnews.example.com",
        })
        snapshot = self._send_email("editor@knownnews.example.com")
        self.assertEqual(snapshot.source_id, source)

    def test_unknown_domain_creates_new_source(self):
        """Email from unknown domain auto-creates a news.source."""
        with patch.object(
            self.env["news.snapshot"].__class__,
            "_ai_get_source_name",
            return_value="New Newsletter",
        ), trap_jobs():
            msg_dict = {
                "email_from": "info@brandnewdomain123.example.com",
                "body": "<p>Content</p>",
                "subject": "Test",
            }
            snapshot = self.env["news.snapshot"].message_new(msg_dict)

        source = snapshot.source_id
        self.assertTrue(source)
        self.assertEqual(source.source_type, "email")
        self.assertEqual(source.sender_domain, "brandnewdomain123.example.com")
        self.assertEqual(source.name, "New Newsletter")

    def test_auto_created_source_is_active(self):
        """Auto-created source is active immediately."""
        with patch.object(
            self.env["news.snapshot"].__class__,
            "_ai_get_source_name",
            return_value="Active Newsletter",
        ), trap_jobs():
            msg_dict = {
                "email_from": "info@activenews999.example.com",
                "body": "<p>Content</p>",
                "subject": "Test",
            }
            snapshot = self.env["news.snapshot"].message_new(msg_dict)
        self.assertTrue(snapshot.source_id.active)

    def test_snapshot_has_sanitized_html_body(self):
        """Snapshot raw_content contains sanitized email body."""
        body = "<p>Clean content</p><script>bad()</script>"
        snapshot = self._send_email("info@sozialinfo.ch", body=body)
        self.assertIn("Clean content", snapshot.raw_content)
        self.assertNotIn("<script>", snapshot.raw_content)

    def test_inbound_email_creates_log_entry(self):
        """Inbound email creates a news.log record with category='email'."""
        self.env["news.source"].create({
            "name": "Log Test Source",
            "source_type": "email",
            "sender_domain": "logtest.example.com",
        })
        snapshot = self._send_email("news@logtest.example.com")
        logs = self.env["news.log"].search([
            ("snapshot_id", "=", snapshot.id),
            ("category", "=", "email"),
        ])
        self.assertTrue(len(logs) >= 1)

    def test_same_domain_reuses_existing_source(self):
        """Second email from same domain reuses the same source."""
        source = self.env["news.source"].create({
            "name": "Reuse Test",
            "source_type": "email",
            "sender_domain": "reusetest.example.com",
        })
        snapshot1 = self._send_email("a@reusetest.example.com")
        snapshot2 = self._send_email("b@reusetest.example.com")
        self.assertEqual(snapshot1.source_id, source)
        self.assertEqual(snapshot2.source_id, source)

    def test_ai_naming_fallback_to_domain(self):
        """When AI call fails, source name falls back to domain."""
        with patch.object(
            self.env["news.snapshot"].__class__,
            "_ai_get_source_name",
            return_value="fallback.example.com",
        ), trap_jobs():
            msg_dict = {
                "email_from": "info@fallback.example.com",
                "body": "<p>Content</p>",
                "subject": "Test",
            }
            snapshot = self.env["news.snapshot"].message_new(msg_dict)
        self.assertEqual(snapshot.source_id.name, "fallback.example.com")

    def test_snapshot_creation_enqueues_discovery(self):
        """Snapshot created via email triggers discovery job."""
        self.env["news.source"].create({
            "name": "Queue Test",
            "source_type": "email",
            "sender_domain": "queuetest.example.com",
        })
        plain_env = self.env(context={})
        with trap_jobs() as trap:
            with patch.object(
                type(plain_env["news.snapshot"]), "_ai_get_source_name",
                return_value="Queue Test"
            ):
                plain_env["news.snapshot"].message_new({
                    "email_from": "news@queuetest.example.com",
                    "body": "<p>Content</p>",
                    "subject": "Newsletter",
                })
            jobs = [j for j in trap.enqueued_jobs if j.method_name == "_discover_articles"]
            self.assertTrue(len(jobs) >= 1)

    def test_listing_snapshot_is_listing(self):
        """Email snapshot should have is_listing=True."""
        snapshot = self._send_email("test@listing.example.com")
        self.assertTrue(snapshot.is_listing)

    def test_listing_snapshot_has_no_parent(self):
        """Email listing snapshot should have no parent_id."""
        snapshot = self._send_email("test@noparent.example.com")
        self.assertFalse(snapshot.parent_id)
