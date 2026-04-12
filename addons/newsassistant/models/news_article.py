import json
import logging
from io import BytesIO
from urllib.parse import urlparse

import requests

from odoo import api, fields, models

from odoo.addons.queue_job.exception import RetryableJobError

from .news_source import (
    AI_TIMEOUT,
    HTTP_TIMEOUT,
    MAX_CLEAN_HTML_LENGTH,
    TRANSIENT_HTTP_CODES,
    USER_AGENT,
    clean_html,
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

    def _fetch_via_jina(self):
        """Fetch article content using the Jina Reader API as fallback.

        Returns the extracted markdown text, or raises an exception.
        Used when direct HTTP fetch fails (403, bot protection, etc.).
        """
        import os
        jina_key = os.environ.get("JINA_API_KEY")
        if not jina_key:
            raise ValueError("JINA_API_KEY environment variable not set")

        jina_url = f"https://r.jina.ai/{self.url}"
        try:
            response = requests.get(
                jina_url,
                timeout=HTTP_TIMEOUT * 2,  # Jina may take longer
                headers={
                    "Authorization": f"Bearer {jina_key}",
                    "Accept": "text/plain",
                },
            )
        except requests.exceptions.Timeout:
            raise RetryableJobError(
                f"Timeout fetching article via Jina: {self.url}",
                seconds=300,
                ignore_retry=False,
            )
        except requests.exceptions.ConnectionError as e:
            raise RetryableJobError(
                f"Connection error fetching via Jina: {e}",
                seconds=300,
                ignore_retry=False,
            )

        if response.status_code in TRANSIENT_HTTP_CODES:
            raise RetryableJobError(
                f"Jina API returned {response.status_code}",
                seconds=300,
                ignore_retry=False,
            )

        if response.status_code != 200:
            raise ValueError(
                f"Jina API error {response.status_code}: {response.text[:200]}"
            )

        return response.text

    def _fetch_and_extract(self):
        """Queue job: fetch article page and extract content using AI.

        Stage 2 of the two-stage pipeline. Fetches the individual article
        page, pre-cleans the HTML, and uses AI to extract structured content.
        Falls back to Jina Reader API for pages that block direct access.
        """
        self.ensure_one()
        _logger.info("Extracting article: %s (%s)", self.title, self.url)

        cleaned_text = None
        source_type = "HTML news article page"
        use_jina = False

        # Fetch article page
        try:
            response = requests.get(
                self.url,
                timeout=HTTP_TIMEOUT,
                headers={"User-Agent": USER_AGENT},
            )
        except requests.exceptions.Timeout:
            raise RetryableJobError(
                f"Timeout fetching article: {self.url}",
                seconds=300,
                ignore_retry=False,
            )
        except requests.exceptions.ConnectionError as e:
            raise RetryableJobError(
                f"Connection error fetching article: {e}",
                seconds=300,
                ignore_retry=False,
            )

        if response.status_code in TRANSIENT_HTTP_CODES:
            raise RetryableJobError(
                f"HTTP {response.status_code} fetching article: {self.url}",
                seconds=300,
                ignore_retry=False,
            )

        if response.status_code == 403:
            # Bot protection — try Jina Reader as fallback
            _logger.info(
                "HTTP 403 for %s, falling back to Jina Reader", self.url
            )
            use_jina = True
        elif response.status_code != 200:
            _logger.warning(
                "Permanent HTTP error %s fetching article %s",
                response.status_code,
                self.url,
            )
            self.write({
                "content": f"[Error: HTTP {response.status_code} fetching article]",
                "scrape_date": fields.Datetime.now(),
            })
            return

        if use_jina:
            # Fetch via Jina Reader
            try:
                cleaned_text = self._fetch_via_jina()
                source_type = "news article"
                if len(cleaned_text) > MAX_CLEAN_HTML_LENGTH:
                    cleaned_text = cleaned_text[:MAX_CLEAN_HTML_LENGTH]
            except RetryableJobError:
                raise
            except Exception as e:
                _logger.warning("Jina fallback failed for %s: %s", self.url, e)
                self.write({
                    "content": f"[Error: Could not fetch article (403 + Jina failed: {e})]",
                    "scrape_date": fields.Datetime.now(),
                })
                return
        else:
            # Detect content type and extract text accordingly
            content_type = response.headers.get("content-type", "").lower()
            is_pdf = (
                "application/pdf" in content_type
                or urlparse(self.url).path.lower().endswith(".pdf")
            )

            if is_pdf:
                # Extract text from PDF
                try:
                    from pdfminer.high_level import extract_text
                    cleaned_text = extract_text(BytesIO(response.content))
                    source_type = "PDF document"
                    if len(cleaned_text) > MAX_CLEAN_HTML_LENGTH:
                        cleaned_text = cleaned_text[:MAX_CLEAN_HTML_LENGTH]
                except Exception as e:
                    _logger.warning(
                        "Failed to extract PDF text from %s: %s", self.url, e
                    )
                    self.write({
                        "content": f"[Error: PDF text extraction failed: {e}]",
                        "scrape_date": fields.Datetime.now(),
                    })
                    return
            else:
                # Pre-clean HTML
                cleaned_text = clean_html(response.text)

        if not cleaned_text or not cleaned_text.strip():
            _logger.warning("No text content extracted from %s", self.url)
            self.write({
                "content": "[Error: No text content could be extracted]",
                "scrape_date": fields.Datetime.now(),
            })
            return

        # AI Stage 2: extract article content
        system_prompt = (
            "/no_think\n"
            f"You are a news extraction assistant. Given the text from a {source_type}, "
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
                system_prompt, cleaned_text
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
