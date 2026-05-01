import json
import logging
from urllib.parse import urlparse, urlunparse

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
    source_type = fields.Selection(
        [("website", "Website"), ("email", "E-Mail")],
        string="Type",
        required=True,
        default="website",
    )
    url = fields.Char(string="URL")
    sender_domain = fields.Char(
        string="Sender Domain",
        help="Email domain to match inbound emails (e.g. newsletter.example.com)",
    )
    active = fields.Boolean(default=True)
    last_scrape_date = fields.Datetime(readonly=True)
    state = fields.Selection(
        [("ok", "OK"), ("error", "Error")],
        default="ok",
        readonly=True,
    )
    error_message = fields.Text(readonly=True)
    article_count = fields.Integer(compute="_compute_article_count", string="Article Count")
    snapshot_ids = fields.One2many("news.snapshot", "source_id", string="Snapshots")
    article_ids = fields.One2many("news.article", "source_id", string="Articles")
    log_ids = fields.One2many("news.log", "source_id", string="Logs")

    # Computed field for scraping indicator
    is_scraping = fields.Boolean(
        compute="_compute_is_scraping",
        string="Currently Scraping",
    )

    def _compute_is_scraping(self):
        """Check if this source has any running scrape jobs."""
        if not self.ids:
            return

        # Use SQL to check for running jobs since 'records' is a serialized field
        self.env.cr.execute("""
            SELECT DISTINCT records->>'res_id' AS source_id
            FROM queue_job
            WHERE state = 'started'
              AND channel = 'root.newsassistant'
              AND model_name = 'news.source'
              AND records->>'res_id' IN %s
        """, [tuple(str(id) for id in self.ids)])

        scraping_ids = {int(row[0]) for row in self.env.cr.fetchall() if row[0]}

        for source in self:
            source.is_scraping = source.id in scraping_ids

    def _compute_article_count(self):
        for source in self:
            source.article_count = self.env["news.article"].search_count(
                [("source_id", "=", source.id)]
            )

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
            dict with keys:
                - content: The parsed content string from the AI response
                - usage: Token usage dict with prompt_tokens, completion_tokens, total_tokens
                - request: Original request details for logging
                - duration_ms: Response time in milliseconds
                - status_code: HTTP status code

        Raises:
            RetryableJobError: On transient API errors (rate limit, timeout, 5xx).
            ValueError: On malformed AI response.
        """
        import time

        api_key = self._get_ai_api_key()
        product_id = self._get_ai_product_id()
        url = f"https://api.infomaniak.com/2/ai/{product_id}/openai/v1/chat/completions"

        model = "qwen3"
        temperature = 0.1
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        start_time = time.time()
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
        duration_ms = int((time.time() - start_time) * 1000)

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

        # Extract usage information if available
        usage = data.get("usage", {})

        return {
            "content": content,
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            "request": {
                "model": model,
                "temperature": temperature,
                "system_prompt": system_prompt,
                "user_content": user_content,
            },
            "response": {
                "content": content,
                "status_code": response.status_code,
            },
            "duration_ms": duration_ms,
        }


