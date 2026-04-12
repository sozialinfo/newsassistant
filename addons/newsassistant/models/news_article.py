import json
import logging

from odoo import api, fields, models

from odoo.addons.queue_job.exception import RetryableJobError

from .news_source import (
    fetch_page,
    normalize_url,
    parse_ai_json,
)

_logger = logging.getLogger(__name__)


class NewsArticle(models.Model):
    _name = "news.article"
    _description = "News Article"
    _order = "scrape_date desc, date desc, id desc"

    title = fields.Char(required=True)
    source_id = fields.Many2one("news.source", required=True, ondelete="cascade")
    url = fields.Char(required=True, index=True)
    date = fields.Date()
    summary = fields.Text()
    content = fields.Html(sanitize=True, sanitize_overridable=True)
    stage_id = fields.Many2one(
        "news.article.stage",
        string="Stage",
        default=lambda self: self._default_stage_id(),
        group_expand="_read_group_stage_ids",
    )
    scrape_date = fields.Datetime(readonly=True)

    _sql_constraints = [
        ("url_unique", "UNIQUE(url)", "An article with this URL already exists."),
    ]

    @api.model
    def _default_stage_id(self):
        """Return the 'New' stage as default."""
        return self.env.ref(
            "newsassistant.news_article_stage_new", raise_if_not_found=False
        )

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        """Always show all stages in kanban, even empty ones."""
        return self.env["news.article.stage"].search([])

    def action_refetch(self):
        """Button action: manually re-fetch and re-extract article content."""
        self.ensure_one()
        self._fetch_and_extract()

    def _fetch_and_extract(self):
        """Queue job: fetch article page and extract content using AI.

        Stage 2 of the two-stage pipeline. Fetches the individual article
        page using Jina Reader API (renders JavaScript, handles PDFs),
        and uses AI to extract structured content.
        """
        self.ensure_one()
        _logger.info("Extracting article: %s (%s)", self.title, self.url)

        # Fetch article page via Jina (renders JavaScript, handles PDFs)
        try:
            content = fetch_page(self.url)
        except RetryableJobError:
            raise
        except ValueError as e:
            _logger.warning("Fetch error for article %s: %s", self.url, e)
            self.write({
                "content": f"[Error: {e}]",
                "scrape_date": fields.Datetime.now(),
            })
            return

        if not content or not content.strip():
            _logger.warning("No content extracted from %s", self.url)
            self.write({
                "content": "[Error: No content could be extracted]",
                "scrape_date": fields.Datetime.now(),
            })
            return

        # AI Stage 2: extract article content from markdown
        system_prompt = (
            "/no_think\n"
            "You are a news extraction assistant. Given markdown content from a news article, "
            "extract the article content. Return ONLY a single JSON object with these fields:\n"
            '- "title": the article title (string)\n'
            '- "date": the publication date in ISO 8601 format YYYY-MM-DD, or null if not found\n'
            '- "summary": a 2-3 sentence summary of the article, plain text (string)\n'
            '- "content": the full article text as clean HTML. Use semantic HTML tags: '
            "<h2>/<h3> for headings, <p> for paragraphs, <ul>/<ol>/<li> for lists, "
            "<strong>/<em> for emphasis. Do NOT include <html>, <head>, <body>, "
            "<nav>, <header>, <footer>, <script>, <style> or any wrapper tags. "
            "Just the article body content as a sequence of HTML elements. "
            "No navigation, no boilerplate, no ads. (string)\n"
            "Keep the original language of the article. Do not translate.\n"
            "IMPORTANT: Return a single valid JSON object like {\"title\": ..., \"date\": ..., \"summary\": ..., \"content\": ...}. "
            "No markdown formatting, no explanation, no code fences."
        )

        try:
            ai_response = self.source_id._call_infomaniak_ai(
                system_prompt, content
            )
        except RetryableJobError:
            raise
        except Exception as e:
            _logger.exception("AI error extracting article %s", self.url)
            self.write({
                "content": f"[Error: AI extraction failed: {e}]",
                "scrape_date": fields.Datetime.now(),
            })
            return

        # Parse AI response
        try:
            article_data = parse_ai_json(ai_response, expect_array=False)
            # If we got a list, take the first element
            if isinstance(article_data, list) and article_data:
                article_data = article_data[0]
            if not isinstance(article_data, dict):
                raise ValueError("Expected a JSON object")
        except (json.JSONDecodeError, ValueError) as e:
            _logger.warning(
                "Malformed AI response for article %s: %s",
                self.url,
                ai_response[:500],
            )
            self.write({
                "content": f"[Error: Invalid AI response: {e}]",
                "scrape_date": fields.Datetime.now(),
            })
            return

        # Update article with extracted data
        vals = {
            "scrape_date": fields.Datetime.now(),
        }

        if article_data.get("title"):
            vals["title"] = article_data["title"]
        if article_data.get("date"):
            try:
                vals["date"] = article_data["date"]
            except Exception:
                _logger.warning(
                    "Invalid date format from AI for article %s: %s",
                    self.url,
                    article_data.get("date"),
                )
        if article_data.get("summary"):
            vals["summary"] = article_data["summary"]
        if article_data.get("content"):
            vals["content"] = article_data["content"]

        self.write(vals)
        _logger.info("Successfully extracted article: %s", self.title)
