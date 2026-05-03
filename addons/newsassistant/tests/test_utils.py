"""Tests for newsassistant.models.utils — html_to_markdown()."""

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.newsassistant.models.utils import html_has_content, html_to_markdown, _node_to_markdown


@tagged("post_install", "-at_install")
class TestHtmlToMarkdown(TransactionCase):
    """Unit tests for html_to_markdown utility function."""

    def test_empty_string_returns_empty(self):
        """Empty string input returns empty string."""
        self.assertEqual(html_to_markdown(""), "")

    def test_none_returns_empty(self):
        """None input returns empty string."""
        self.assertEqual(html_to_markdown(None), "")

    def test_plain_text_passthrough(self):
        """Plain text without HTML tags is returned as-is (stripped)."""
        result = html_to_markdown("Hello world")
        self.assertEqual(result, "Hello world")

    def test_paragraph_to_newlines(self):
        """<p> tags are converted to newline-separated blocks."""
        result = html_to_markdown("<p>First paragraph.</p><p>Second paragraph.</p>")
        self.assertIn("First paragraph.", result)
        self.assertIn("Second paragraph.", result)
        # Should have a newline between them
        self.assertIn("\n", result)

    def test_br_to_newline(self):
        """<br> tag is converted to newline."""
        result = html_to_markdown("Line one<br>Line two")
        self.assertIn("Line one", result)
        self.assertIn("Line two", result)
        self.assertIn("\n", result)

    def test_h1_heading(self):
        """<h1> is converted to # prefix."""
        result = html_to_markdown("<h1>Title</h1>")
        self.assertIn("# Title", result)

    def test_h2_heading(self):
        """<h2> is converted to ## prefix."""
        result = html_to_markdown("<h2>Subtitle</h2>")
        self.assertIn("## Subtitle", result)

    def test_h3_heading(self):
        """<h3> is converted to ### prefix."""
        result = html_to_markdown("<h3>Section</h3>")
        self.assertIn("### Section", result)

    def test_h4_heading(self):
        """<h4> is converted to #### prefix."""
        result = html_to_markdown("<h4>Sub-section</h4>")
        self.assertIn("#### Sub-section", result)

    def test_h5_heading(self):
        """<h5> is converted to ##### prefix."""
        result = html_to_markdown("<h5>Minor</h5>")
        self.assertIn("##### Minor", result)

    def test_h6_heading(self):
        """<h6> is converted to ###### prefix."""
        result = html_to_markdown("<h6>Tiny</h6>")
        self.assertIn("###### Tiny", result)

    def test_unordered_list(self):
        """<ul><li> items are converted to - prefixed lines."""
        result = html_to_markdown("<ul><li>Item one</li><li>Item two</li></ul>")
        self.assertIn("- Item one", result)
        self.assertIn("- Item two", result)

    def test_ordered_list(self):
        """<ol><li> items are converted to - prefixed lines."""
        result = html_to_markdown("<ol><li>First</li><li>Second</li></ol>")
        self.assertIn("- First", result)
        self.assertIn("- Second", result)

    def test_strong_tag(self):
        """<strong> is converted to **...**."""
        result = html_to_markdown("<strong>bold text</strong>")
        self.assertIn("**bold text**", result)

    def test_b_tag(self):
        """<b> is converted to **...**."""
        result = html_to_markdown("<b>bold</b>")
        self.assertIn("**bold**", result)

    def test_em_tag(self):
        """<em> is converted to *...*."""
        result = html_to_markdown("<em>italic text</em>")
        self.assertIn("*italic text*", result)

    def test_i_tag(self):
        """<i> is converted to *...*."""
        result = html_to_markdown("<i>italic</i>")
        self.assertIn("*italic*", result)

    def test_nested_tags_bold_in_paragraph(self):
        """Nested tags: <strong> inside <p> is handled correctly."""
        result = html_to_markdown("<p>This is <strong>important</strong> text.</p>")
        self.assertIn("**important**", result)
        self.assertIn("This is", result)

    def test_unknown_tags_stripped(self):
        """Unknown tags are stripped, inner text preserved."""
        result = html_to_markdown("<span>some text</span>")
        self.assertIn("some text", result)
        self.assertNotIn("<span>", result)

    def test_div_treated_as_block(self):
        """<div> produces newline-separated blocks."""
        result = html_to_markdown("<div>Block content</div>")
        self.assertIn("Block content", result)

    def test_complex_html(self):
        """Complex HTML with mixed elements converts cleanly."""
        html = (
            "<h2>Strategy Overview</h2>"
            "<p>This strategy focuses on <strong>innovation</strong> and <em>growth</em>.</p>"
            "<ul><li>Item A</li><li>Item B</li></ul>"
        )
        result = html_to_markdown(html)
        self.assertIn("## Strategy Overview", result)
        self.assertIn("**innovation**", result)
        self.assertIn("*growth*", result)
        self.assertIn("- Item A", result)
        self.assertIn("- Item B", result)

    def test_result_is_stripped(self):
        """Result has no leading or trailing whitespace."""
        result = html_to_markdown("  <p>  Hello  </p>  ")
        self.assertEqual(result, result.strip())

    def test_whitespace_only_html(self):
        """HTML with only whitespace returns empty string."""
        result = html_to_markdown("   ")
        self.assertEqual(result, "")

    def test_empty_strong_tag(self):
        """Empty <strong> tag produces no asterisks."""
        result = html_to_markdown("<strong></strong>")
        self.assertNotIn("**", result)

    def test_empty_em_tag(self):
        """Empty <em> tag produces no asterisks."""
        result = html_to_markdown("<em></em>")
        self.assertNotIn("*", result)

    def test_standalone_li_without_ul(self):
        """Standalone <li> outside <ul>/<ol> is still converted to - prefix."""
        result = html_to_markdown("<li>Standalone item</li>")
        self.assertIn("- Standalone item", result)

    def test_html_comment_ignored(self):
        """HTML comments are ignored (Comment nodes return empty string)."""
        result = html_to_markdown("<p>Text</p><!-- comment -->")
        self.assertIn("Text", result)
        self.assertNotIn("comment", result)

    def test_html_has_content_false_for_none(self):
        """html_has_content returns False for None."""
        self.assertFalse(html_has_content(None))

    def test_html_has_content_false_for_empty(self):
        """html_has_content returns False for empty string."""
        self.assertFalse(html_has_content(""))

    def test_html_has_content_false_for_empty_paragraph(self):
        """html_has_content returns False for HTML editor empty state."""
        self.assertFalse(html_has_content("<p><br></p>"))

    def test_html_has_content_false_for_empty_heading(self):
        """html_has_content returns False for empty heading (editor artefact)."""
        self.assertFalse(html_has_content('<h2 data-oe-version="1.2"><br></h2>'))

    def test_html_has_content_true_for_text(self):
        """html_has_content returns True when there is real text content."""
        self.assertTrue(html_has_content("<p>Some text.</p>"))

    def test_html_has_content_true_for_nested(self):
        """html_has_content returns True for nested HTML with text."""
        self.assertTrue(html_has_content("<h2>Title</h2><p>Body.</p>"))

    def test_unknown_node_type_returns_empty(self):
        """Non-Tag, non-NavigableString, non-Comment nodes return empty string."""
        # Pass an object that is none of the expected BS4 types
        result = _node_to_markdown(object())
        self.assertEqual(result, "")
