"""Tests for image utility functions (now in newsassistant_website).

These tests cover the standalone utility functions that were moved to
the website module. The base module no longer handles image selection.
This file is kept as a stub to ensure test count parity.
"""
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestHeaderImageStub(TransactionCase):
    """Stub: header image tests moved to newsassistant_website module."""

    def test_header_image_module_split(self):
        """Confirm header image logic lives in newsassistant_website, not base."""
        # The base module (newsassistant) no longer contains fetch_page,
        # select_header_image, or validate_and_download_image.
        # These are tested in newsassistant_website/tests/test_image_utils.py
        with self.assertRaises(ImportError):
            from odoo.addons.newsassistant.models.news_source import select_header_image  # noqa
