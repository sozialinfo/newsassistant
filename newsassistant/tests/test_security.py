"""Security tests for the newsassistant module.

Tests:
- Group hierarchy: Admin implies User
- Per-role CRUD on core models
- AccessError for unauthorized operations
"""
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSecurityGroups(TransactionCase):
    """Tests for group hierarchy and access control."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_user = cls.env.ref("newsassistant.newsassistant_group_user")
        cls.group_admin = cls.env.ref("newsassistant.newsassistant_group_admin")

        # Create a user-role user
        cls.user_user = cls.env["res.users"].create({
            "name": "Test User",
            "login": "test_na_user@test.com",
            "groups_id": [(6, 0, [cls.group_user.id])],
        })

        # Create an admin-role user
        cls.user_admin = cls.env["res.users"].create({
            "name": "Test Admin",
            "login": "test_na_admin@test.com",
            "groups_id": [(6, 0, [cls.group_admin.id])],
        })

        # Create a plain internal user (no newsassistant groups)
        cls.user_plain = cls.env["res.users"].create({
            "name": "Plain User",
            "login": "test_na_plain@test.com",
            "groups_id": [(6, 0, [cls.env.ref("base.group_user").id])],
        })

        # Create source and snapshot as admin
        cls.source = cls.env["news.source"].create({
            "name": "Security Test Source",
            "source_type": "website",
            "url": "https://security-test.example.com",
        })
        cls.stage = cls.env.ref("newsassistant.news_article_stage_new")
        cls.snapshot = cls.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": cls.source.id,
            "raw_content": "<p>Test</p>",
        })
        cls.article = cls.env["news.article"].create({
            "title": "Security Test Article",
            "snapshot_id": cls.snapshot.id,
            "stage_id": cls.stage.id,
        })

    def test_admin_implies_user_group(self):
        """Admin group must imply User group."""
        self.assertIn(self.group_user, self.group_admin.implied_ids)

    def test_admin_user_is_in_user_group(self):
        """Admin user should have access to user-level features."""
        self.assertTrue(self.user_admin.has_group("newsassistant.newsassistant_group_user"))
        self.assertTrue(self.user_admin.has_group("newsassistant.newsassistant_group_admin"))

    def test_user_not_in_admin_group(self):
        """Regular user should not have admin access."""
        self.assertTrue(self.user_user.has_group("newsassistant.newsassistant_group_user"))
        self.assertFalse(self.user_user.has_group("newsassistant.newsassistant_group_admin"))

    # -------------------------------------------------------------------------
    # news.source CRUD
    # -------------------------------------------------------------------------

    def test_user_can_read_sources(self):
        """Users can read news sources."""
        source = self.env["news.source"].with_user(self.user_user).browse(self.source.id)
        self.assertEqual(source.name, "Security Test Source")

    def test_user_cannot_create_source(self):
        """Users cannot create news sources (admin-only)."""
        with self.assertRaises(AccessError):
            self.env["news.source"].with_user(self.user_user).create({
                "name": "User-Created Source",
                "source_type": "website",
                "url": "https://user-test.example.com",
            })

    def test_plain_user_cannot_read_sources(self):
        """Plain internal users (without newsassistant groups) cannot read sources."""
        with self.assertRaises(AccessError):
            self.env["news.source"].with_user(self.user_plain).browse(self.source.id).read(["name"])

    # -------------------------------------------------------------------------
    # news.snapshot CRUD
    # -------------------------------------------------------------------------

    def test_user_can_read_snapshots(self):
        """Users can read snapshots."""
        snapshot = self.env["news.snapshot"].with_user(self.user_user).browse(self.snapshot.id)
        self.assertEqual(snapshot.source_id.id, self.source.id)

    def test_user_cannot_create_snapshot(self):
        """Regular users cannot create snapshots (read-only access)."""
        with self.assertRaises(AccessError):
            self.env["news.snapshot"].with_user(self.user_user).create({
                "source_id": self.source.id,
                "raw_content": "<p>Test</p>",
            })

    def test_system_can_create_snapshot(self):
        """System (superuser context) can create snapshots."""
        snapshot = self.env["news.snapshot"].with_context(skip_snapshot_extraction=True).create({
            "source_id": self.source.id,
            "raw_content": "<p>System test</p>",
        })
        self.assertTrue(snapshot.id)

    # -------------------------------------------------------------------------
    # news.article CRUD
    # -------------------------------------------------------------------------

    def test_user_can_read_articles(self):
        """Users can read articles."""
        article = self.env["news.article"].with_user(self.user_user).browse(self.article.id)
        self.assertEqual(article.title, "Security Test Article")

    def test_user_can_write_articles(self):
        """Users can update articles (e.g. move stages)."""
        self.env["news.article"].with_user(self.user_user).browse(self.article.id).write({
            "stage_id": self.stage.id,
        })

    def test_plain_user_cannot_read_articles(self):
        """Plain internal users cannot read articles."""
        with self.assertRaises(AccessError):
            self.env["news.article"].with_user(self.user_plain).browse(self.article.id).read(["title"])

    # -------------------------------------------------------------------------
    # news.log access
    # -------------------------------------------------------------------------

    def test_admin_can_read_logs(self):
        """Admin users can read logs."""
        log = self.env["news.log"].create({
            "level": "success",
            "category": "extraction",
            "message": "Test log",
            "source_id": self.source.id,
        })
        log_as_admin = self.env["news.log"].with_user(self.user_admin).browse(log.id)
        self.assertEqual(log_as_admin.message, "Test log")

    def test_user_cannot_read_logs(self):
        """Regular users cannot read logs (admin-only)."""
        log = self.env["news.log"].create({
            "level": "success",
            "category": "extraction",
            "message": "Test log restricted",
            "source_id": self.source.id,
        })
        with self.assertRaises(AccessError):
            self.env["news.log"].with_user(self.user_user).browse(log.id).read(["message"])
