import json
import logging
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from odoo import fields, models

from odoo.addons.queue_job.exception import RetryableJobError

_logger = logging.getLogger(__name__)

# Tags to strip during HTML pre-cleaning
STRIP_TAGS = {"script", "style", "nav", "header", "footer", "aside", "form", "noscript", "svg", "iframe"}
MAX_CLEAN_HTML_LENGTH = 30000
HTTP_TIMEOUT = 30
AI_TIMEOUT = 120
USER_AGENT = "NewsAssistant/1.0"

# Transient HTTP status codes that should be retried
TRANSIENT_HTTP_CODES = {408, 429, 500, 502, 503, 504}


def normalize_url(url):
    """Normalize a URL for deduplication: strip trailing slashes and fragments."""
    if not url:
        return url
    parsed = urlparse(url)
    # Remove fragment, strip trailing slash from path
    path = parsed.path.rstrip("/") if parsed.path != "/" else "/"
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc,
        path,
        parsed.params,
        parsed.query,
        "",  # no fragment
    ))
    return normalized


def clean_html(raw_html):
    """Pre-clean HTML for LLM consumption.

    Strips navigation, footer, script, style and other non-content tags.
    Removes most HTML attributes to reduce token count, but preserves
    href on <a> tags (needed for URL extraction) and src on <img> tags.
    Truncates to MAX_CLEAN_HTML_LENGTH characters.
    """
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "lxml")

    # Remove unwanted tags entirely
    for tag_name in STRIP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Remove most attributes but preserve href on links and src on images
    for tag in soup.find_all(True):
        preserved = {}
        if tag.name == "a" and tag.get("href"):
            preserved["href"] = tag["href"]
        if tag.name == "img" and tag.get("src"):
            preserved["src"] = tag["src"]
        tag.attrs = preserved

    result = str(soup)
    if len(result) > MAX_CLEAN_HTML_LENGTH:
        result = result[:MAX_CLEAN_HTML_LENGTH]
    return result


def fetch_page(url):
    """Fetch a page using the Jina Reader API.

    Jina renders JavaScript and returns clean markdown content.
    Requires JINA_API_KEY environment variable.

    Args:
        url: The URL to fetch.

    Returns:
        Markdown content from the page (truncated to MAX_CLEAN_HTML_LENGTH).

    Raises:
        ValueError: If JINA_API_KEY is not set or on permanent API errors.
        RetryableJobError: On transient failures (timeout, 5xx, rate limit).
    """
    import os
    jina_key = os.environ.get("JINA_API_KEY")
    if not jina_key:
        raise ValueError("JINA_API_KEY environment variable not set")

    jina_url = f"https://r.jina.ai/{url}"
    try:
        response = requests.get(
            jina_url,
            timeout=HTTP_TIMEOUT * 2,  # 60 seconds - Jina may take longer
            headers={
                "Authorization": f"Bearer {jina_key}",
                "Accept": "text/plain",
            },
        )
    except requests.exceptions.Timeout:
        raise RetryableJobError(
            f"Timeout fetching via Jina: {url}",
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

    content = response.text
    if len(content) > MAX_CLEAN_HTML_LENGTH:
        content = content[:MAX_CLEAN_HTML_LENGTH]

    return content


def parse_ai_json(raw_text, expect_array=True):
    """Robustly parse JSON from AI responses.

    Handles:
    - Markdown code fences (```json ... ```)
    - Thinking blocks (<think>...</think>)
    - JSONL (newline-delimited JSON objects) -> wraps in array
    - Single JSON object when array expected -> wraps in array
    - Extra whitespace / trailing content
    """
    text = raw_text.strip()

    # Remove thinking blocks (qwen3 sometimes includes <think>...</think>)
    import re
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    # Strip markdown code fences
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1:]
    if text.endswith("```"):
        text = text[:-3].strip()

    # Try standard JSON parse first
    try:
        result = json.loads(text)
        if expect_array and isinstance(result, dict):
            return [result]
        return result
    except json.JSONDecodeError:
        pass

    # Try to find a JSON array in the text
    if expect_array:
        # Look for [...] block
        start = text.find("[")
        if start != -1:
            # Find matching closing bracket
            depth = 0
            for i in range(start, len(text)):
                if text[i] == "[":
                    depth += 1
                elif text[i] == "]":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start:i + 1])
                        except json.JSONDecodeError:
                            break
                        break

        # Try JSONL: multiple JSON objects separated by newlines
        objects = []
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Skip lines that look like comments or non-JSON
            if line.startswith(("//", "#", "*", "-")):
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    objects.append(obj)
                elif isinstance(obj, list):
                    objects.extend(obj)
            except json.JSONDecodeError:
                continue
        if objects:
            return objects

        # Last resort: find all {..} blocks in the text
        objects = []
        for match in re.finditer(r"\{[^{}]*\}", text):
            try:
                obj = json.loads(match.group())
                if isinstance(obj, dict) and ("title" in obj or "url" in obj):
                    objects.append(obj)
            except json.JSONDecodeError:
                continue
        if objects:
            return objects

    # Nothing worked
    raise ValueError(f"Could not parse JSON from AI response: {text[:200]}")


class NewsSource(models.Model):
    _name = "news.source"
    _description = "News Source"
    _order = "name"

    name = fields.Char(required=True)
    url = fields.Char(required=True)
    active = fields.Boolean(default=True)
    last_scrape_date = fields.Datetime(readonly=True)
    state = fields.Selection(
        [("ok", "OK"), ("error", "Error")],
        default="ok",
        readonly=True,
    )
    error_message = fields.Text(readonly=True)
    article_count = fields.Integer(compute="_compute_article_count", string="Article Count")
    article_ids = fields.One2many("news.article", "source_id", string="Articles")

    def _compute_article_count(self):
        for source in self:
            source.article_count = len(source.article_ids)

    # -------------------------------------------------------------------------
    # AI Service
    # -------------------------------------------------------------------------

    def _get_ai_api_key(self):
        """Get the Infomaniak AI API key from environment."""
        import os
        api_key = os.environ.get("INFOMANIAK_AI_API_KEY")
        if not api_key:
            raise models.UserError(
                "Infomaniak AI API key not configured. "
                "Set the INFOMANIAK_AI_API_KEY environment variable."
            )
        return api_key

    def _get_ai_product_id(self):
        """Get the Infomaniak AI product ID from system parameters."""
        return self.env["ir.config_parameter"].sudo().get_param(
            "newsassistant.infomaniak_product_id", default="103794"
        )

    def _call_infomaniak_ai(self, system_prompt, user_content):
        """Call the Infomaniak AI chat completion API.

        Args:
            system_prompt: The system prompt instructing the AI.
            user_content: The user message content (typically cleaned HTML).

        Returns:
            The parsed content string from the AI response.

        Raises:
            RetryableJobError: On transient API errors (rate limit, timeout, 5xx).
            ValueError: On malformed AI response.
        """
        api_key = self._get_ai_api_key()
        product_id = self._get_ai_product_id()
        url = f"https://api.infomaniak.com/2/ai/{product_id}/openai/v1/chat/completions"

        payload = {
            "model": "qwen3",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.1,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                url, json=payload, headers=headers, timeout=AI_TIMEOUT
            )
        except requests.exceptions.Timeout:
            raise RetryableJobError(
                "Infomaniak AI API timeout", seconds=300, ignore_retry=False
            )
        except requests.exceptions.ConnectionError as e:
            raise RetryableJobError(
                f"Infomaniak AI API connection error: {e}",
                seconds=300,
                ignore_retry=False,
            )

        if response.status_code in TRANSIENT_HTTP_CODES:
            raise RetryableJobError(
                f"Infomaniak AI API returned {response.status_code}",
                seconds=300,
                ignore_retry=False,
            )

        if response.status_code != 200:
            raise ValueError(
                f"Infomaniak AI API error {response.status_code}: {response.text[:500]}"
            )

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise ValueError(f"Unexpected AI response structure: {e}")

        return content

    # -------------------------------------------------------------------------
    # Scraping Pipeline
    # -------------------------------------------------------------------------

    def _cron_scrape_all(self):
        """Cron entry point: enqueue a scrape job for each active source."""
        sources = self.search([("active", "=", True)])
        for source in sources:
            source.with_delay(
                channel="root.newsassistant",
                description=f"Scrape listing: {source.name}",
            )._scrape_listing()

    def _scrape_listing(self):
        """Queue job: fetch the listing page and discover article URLs.

        Stage 1 of the two-stage pipeline. Discovers article URLs from the
        listing page using Jina Reader API (renders JavaScript) and AI extraction,
        then creates news.article stubs and enqueues Stage 2 jobs for each new article.
        """
        self.ensure_one()
        _logger.info("Scraping listing for source: %s (%s)", self.name, self.url)

        # Fetch listing page via Jina (renders JavaScript)
        try:
            content = fetch_page(self.url)
        except RetryableJobError:
            raise
        except ValueError as e:
            self.write({
                "state": "error",
                "error_message": str(e),
            })
            _logger.warning("Fetch error for source %s: %s", self.name, e)
            return

        # AI Stage 1: discover article URLs from markdown content
        system_prompt = (
            "/no_think\n"
            "You are a news extraction assistant. Given markdown content from a news listing page, "
            "extract all news article links. Return ONLY a JSON array of objects, each with "
            '"title" (string) and "url" (string) fields. '
            "Only include actual news/blog article links, not navigation, category, "
            "pagination, or social media links. "
            "Extract URLs exactly as they appear in the markdown links [text](url). "
            "Return a single valid JSON array like [{...}, {...}]. "
            "Do NOT return separate JSON objects on separate lines. "
            "No markdown formatting, no explanation, no code fences."
        )

        try:
            ai_response = self._call_infomaniak_ai(system_prompt, content)
        except RetryableJobError:
            raise
        except Exception as e:
            self.write({
                "state": "error",
                "error_message": f"AI extraction error: {e}",
            })
            _logger.exception("AI error for source %s", self.name)
            return

        # Parse AI response
        try:
            articles_data = parse_ai_json(ai_response, expect_array=True)
            if not isinstance(articles_data, list):
                raise ValueError("Expected a JSON array")
        except (json.JSONDecodeError, ValueError) as e:
            self.write({
                "state": "error",
                "error_message": f"Invalid AI response (not valid JSON): {e}",
            })
            _logger.warning(
                "Malformed AI response for source %s: %s",
                self.name,
                ai_response[:500],
            )
            return

        # Process discovered articles
        Article = self.env["news.article"]
        new_count = 0

        for item in articles_data:
            title = item.get("title", "").strip()
            url = item.get("url", "").strip()
            if not url:
                continue

            # Resolve relative and protocol-relative URLs
            if url.startswith("//"):
                # Protocol-relative URL: add scheme from source URL
                url = urlparse(self.url).scheme + ":" + url
            elif not url.startswith(("http://", "https://")):
                url = urljoin(self.url, url)

            # Normalize for dedup
            normalized = normalize_url(url)

            # Skip if URL is the same as the source listing page
            if normalized == normalize_url(self.url):
                _logger.debug(
                    "Skipping article with same URL as source listing: %s",
                    normalized,
                )
                continue

            # Skip non-http URLs (mailto:, javascript:, tel:, etc.)
            if not normalized.startswith(("http://", "https://")):
                continue

            # Skip binary resources that can never be news articles
            path_lower = urlparse(normalized).path.lower()
            skip_extensions = (
                ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
                ".zip", ".rar", ".gz", ".tar",
                ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
                ".mp3", ".mp4", ".avi", ".mov",
            )
            if path_lower.endswith(skip_extensions):
                _logger.debug(
                    "Skipping non-article resource: %s", normalized,
                )
                continue

            # Check for duplicates
            existing = Article.search([("url", "=", normalized)], limit=1)
            if existing:
                continue

            # Create article stub and enqueue extraction
            article = Article.create({
                "title": title or "Untitled",
                "source_id": self.id,
                "url": normalized,
            })
            article.with_delay(
                channel="root.newsassistant",
                description=f"Extract article: {title[:50]}",
            )._fetch_and_extract()
            new_count += 1

        # Update source state
        self.write({
            "state": "ok",
            "error_message": False,
            "last_scrape_date": fields.Datetime.now(),
        })
        _logger.info(
            "Source %s: discovered %d articles, %d new",
            self.name,
            len(articles_data),
            new_count,
        )
