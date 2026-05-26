from odoo.tests.common import TransactionCase, tagged

from odoo.addons.newsassistant.models.news_source import normalize_url


@tagged("post_install", "-at_install")
class TestUrlNormalization(TransactionCase):
    def test_strip_trailing_slash(self):
        """Test that trailing slashes are removed."""
        self.assertEqual(
            normalize_url("https://example.com/article/1/"),
            "https://example.com/article/1",
        )

    def test_preserve_root_slash(self):
        """Test that root path slash is preserved."""
        self.assertEqual(
            normalize_url("https://example.com/"),
            "https://example.com/",
        )

    def test_strip_fragment(self):
        """Test that URL fragments are removed."""
        self.assertEqual(
            normalize_url("https://example.com/article/1#section"),
            "https://example.com/article/1",
        )

    def test_strip_trailing_slash_and_fragment(self):
        """Test both trailing slash and fragment removal."""
        self.assertEqual(
            normalize_url("https://example.com/article/1/#top"),
            "https://example.com/article/1",
        )

    def test_preserve_query_params(self):
        """Test that query parameters are preserved."""
        self.assertEqual(
            normalize_url("https://example.com/article?id=1&page=2"),
            "https://example.com/article?id=1&page=2",
        )

    def test_dedup_matching(self):
        """Test that URLs that should match after normalization do match."""
        url1 = normalize_url("https://example.com/article/1/")
        url2 = normalize_url("https://example.com/article/1")
        self.assertEqual(url1, url2)

    def test_dedup_with_fragments(self):
        """Test that URLs differing only by fragment match."""
        url1 = normalize_url("https://example.com/article/1#top")
        url2 = normalize_url("https://example.com/article/1#bottom")
        self.assertEqual(url1, url2)

    def test_empty_url(self):
        """Test that empty/None URLs pass through."""
        self.assertFalse(normalize_url(""))
        self.assertIsNone(normalize_url(None))

    def test_no_change_needed(self):
        """Test URL that needs no normalization."""
        url = "https://example.com/article/1"
        self.assertEqual(normalize_url(url), url)
