from odoo.tests.common import TransactionCase, tagged

from odoo.addons.newsassistant.models.news_source import clean_html, parse_ai_json


@tagged("post_install", "-at_install")
class TestHtmlCleaner(TransactionCase):
    def test_strip_script_tags(self):
        """Test that <script> tags are removed."""
        html = "<html><body><script>alert('x')</script><p>Content</p></body></html>"
        result = clean_html(html)
        self.assertNotIn("script", result)
        self.assertNotIn("alert", result)
        self.assertIn("Content", result)

    def test_strip_style_tags(self):
        """Test that <style> tags are removed."""
        html = "<html><body><style>.foo{color:red}</style><p>Content</p></body></html>"
        result = clean_html(html)
        self.assertNotIn("style", result.lower().replace("<p>content</p>", ""))
        self.assertNotIn("color:red", result)
        self.assertIn("Content", result)

    def test_strip_nav_tags(self):
        """Test that <nav> tags are removed."""
        html = "<html><body><nav><a href='/'>Home</a></nav><p>Article text</p></body></html>"
        result = clean_html(html)
        self.assertNotIn("nav", result)
        self.assertNotIn("Home", result)
        self.assertIn("Article text", result)

    def test_strip_header_footer(self):
        """Test that <header> and <footer> tags are removed."""
        html = (
            "<html><body>"
            "<header><h1>Site Title</h1></header>"
            "<p>Article content</p>"
            "<footer>Copyright 2025</footer>"
            "</body></html>"
        )
        result = clean_html(html)
        self.assertNotIn("Site Title", result)
        self.assertNotIn("Copyright", result)
        self.assertIn("Article content", result)

    def test_strip_aside_and_form(self):
        """Test that <aside> and <form> tags are removed."""
        html = (
            "<html><body>"
            "<aside>Sidebar content</aside>"
            "<p>Main content</p>"
            "<form><input type='text'/></form>"
            "</body></html>"
        )
        result = clean_html(html)
        self.assertNotIn("Sidebar", result)
        self.assertNotIn("form", result)
        self.assertIn("Main content", result)

    def test_remove_most_attributes(self):
        """Test that non-essential HTML attributes are stripped."""
        html = '<html><body><div class="article" id="main" data-id="5"><p style="color:red">Text</p></div></body></html>'
        result = clean_html(html)
        self.assertNotIn("class=", result)
        self.assertNotIn("id=", result)
        self.assertNotIn("data-id=", result)
        self.assertNotIn("style=", result)
        self.assertIn("Text", result)

    def test_preserve_href_on_links(self):
        """Test that href attributes are preserved on <a> tags."""
        html = '<html><body><a href="https://example.com/article" class="link" id="a1">Click here</a></body></html>'
        result = clean_html(html)
        self.assertIn('href="https://example.com/article"', result)
        self.assertNotIn("class=", result)
        self.assertNotIn("id=", result)
        self.assertIn("Click here", result)

    def test_truncation(self):
        """Test that output is truncated to 30,000 characters."""
        # Create HTML larger than 30,000 chars
        long_content = "A" * 40000
        html = f"<html><body><p>{long_content}</p></body></html>"
        result = clean_html(html)
        self.assertLessEqual(len(result), 30000)

    def test_empty_input(self):
        """Test that empty input returns empty string."""
        self.assertEqual(clean_html(""), "")
        self.assertEqual(clean_html(None), "")

    def test_preserves_content_structure(self):
        """Test that article content structure is preserved."""
        html = (
            "<html><body>"
            "<h1>Article Title</h1>"
            "<p>First paragraph.</p>"
            "<p>Second paragraph.</p>"
            "<ul><li>Point one</li><li>Point two</li></ul>"
            "</body></html>"
        )
        result = clean_html(html)
        self.assertIn("Article Title", result)
        self.assertIn("First paragraph", result)
        self.assertIn("Second paragraph", result)
        self.assertIn("Point one", result)


@tagged("post_install", "-at_install")
class TestParseAiJson(TransactionCase):
    def test_parse_standard_json_array(self):
        """Test parsing a standard JSON array."""
        text = '[{"title": "A", "url": "http://a.com"}, {"title": "B", "url": "http://b.com"}]'
        result = parse_ai_json(text, expect_array=True)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["title"], "A")

    def test_parse_jsonl(self):
        """Test parsing newline-delimited JSON objects (JSONL)."""
        text = '{"title": "A", "url": "http://a.com"}\n{"title": "B", "url": "http://b.com"}'
        result = parse_ai_json(text, expect_array=True)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["title"], "A")
        self.assertEqual(result[1]["title"], "B")

    def test_parse_single_object_as_array(self):
        """Test that a single object is wrapped in an array when expected."""
        text = '{"title": "A", "url": "http://a.com"}'
        result = parse_ai_json(text, expect_array=True)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "A")

    def test_parse_markdown_fenced_json(self):
        """Test parsing JSON wrapped in markdown code fences."""
        text = '```json\n[{"title": "A", "url": "http://a.com"}]\n```'
        result = parse_ai_json(text, expect_array=True)
        self.assertEqual(len(result), 1)

    def test_parse_json_with_thinking_block(self):
        """Test parsing JSON with <think> blocks removed."""
        text = '<think>Let me analyze...</think>\n[{"title": "A", "url": "http://a.com"}]'
        result = parse_ai_json(text, expect_array=True)
        self.assertEqual(len(result), 1)

    def test_parse_json_object_not_array(self):
        """Test parsing a JSON object when not expecting array."""
        text = '{"title": "A", "date": "2025-01-01", "summary": "S", "content": "C"}'
        result = parse_ai_json(text, expect_array=False)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["title"], "A")

    def test_parse_json_with_extra_text(self):
        """Test parsing JSON array embedded in extra text."""
        text = 'Here are the results:\n[{"title": "A", "url": "http://a.com"}]\nDone.'
        result = parse_ai_json(text, expect_array=True)
        self.assertEqual(len(result), 1)

    def test_parse_invalid_json_raises(self):
        """Test that completely invalid text raises ValueError."""
        with self.assertRaises(ValueError):
            parse_ai_json("This is not JSON at all", expect_array=True)
