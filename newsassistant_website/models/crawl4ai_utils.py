"""crawl4ai REST API utilities for website content fetching."""
import logging

import requests

from odoo.addons.queue_job.exception import RetryableJobError

_logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 120
MAX_CONTENT_LENGTH = 30000
DEFAULT_CRAWL4AI_URL = "http://crawl4ai:11235"


def fetch_page(url, crawl4ai_url=None, crawl4ai_api_token=None):
    """Fetch a page using self-hosted crawl4ai server.

    crawl4ai renders JavaScript using Chromium and returns clean markdown
    content along with images found on the page.

    Args:
        url: The URL to fetch.
        crawl4ai_url: Optional crawl4ai server URL. Falls back to
                      DEFAULT_CRAWL4AI_URL if not provided.
        crawl4ai_api_token: Optional Bearer token for authenticated servers.

    Returns:
        Tuple of (content, images_dict):
            - content: Markdown content from the page (truncated to MAX_CONTENT_LENGTH)
            - images_dict: Dictionary of {alt: src} for images on the page

    Raises:
        ValueError: On permanent API errors (success=false, no results, parse failure).
        RetryableJobError: On transient failures (timeout, connection error, non-200).
    """
    if not crawl4ai_url:
        crawl4ai_url = DEFAULT_CRAWL4AI_URL
    api_url = f"{crawl4ai_url}/crawl"

    headers = {}
    if crawl4ai_api_token:
        headers["Authorization"] = f"Bearer {crawl4ai_api_token}"

    payload = {
        "urls": [url],
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "wait_until": "networkidle",
                "page_timeout": 30000,
            },
        },
    }
    try:
        response = requests.post(
            api_url,
            json=payload,
            headers=headers or None,
            timeout=HTTP_TIMEOUT,
        )
    except requests.exceptions.Timeout:
        raise RetryableJobError(
            f"Timeout fetching via crawl4ai: {url}",
            seconds=300,
            ignore_retry=False,
        )
    except requests.exceptions.ConnectionError as e:
        raise RetryableJobError(
            f"Connection error fetching via crawl4ai: {e}",
            seconds=300,
            ignore_retry=False,
        )

    if response.status_code != 200:
        raise RetryableJobError(
            f"crawl4ai returned HTTP {response.status_code}",
            seconds=300,
            ignore_retry=False,
        )

    try:
        data = response.json()
    except ValueError as e:
        raise ValueError(f"Failed to parse crawl4ai JSON response: {e}")

    if not data.get("success"):
        error_msg = data.get("error", "unknown error")
        raise ValueError(f"crawl4ai crawl failed: {error_msg}")

    results = data.get("results", [])
    if not results:
        raise ValueError("crawl4ai returned no results")

    result = results[0]
    raw = result.get("markdown", "") or ""
    if isinstance(raw, dict):
        content = raw.get("raw_markdown", "") or ""
    else:
        content = str(raw)
    images_dict = {}

    media = result.get("media", {}) or {}
    raw_images = media.get("images", []) or []
    for img in raw_images:
        src = img.get("src", "")
        alt = img.get("alt", "") or img.get("caption", "") or src
        if src:
            images_dict[alt] = src

    if len(content) > MAX_CONTENT_LENGTH:
        content = content[:MAX_CONTENT_LENGTH]

    return content, images_dict


def markdown_to_html(markdown_text):
    """Convert Markdown text to HTML.

    Uses the markdown library if available, falls back to basic conversion.

    Args:
        markdown_text: Markdown string to convert.

    Returns:
        HTML string.
    """
    if not markdown_text:
        return ""
    try:
        import markdown
        return markdown.markdown(
            markdown_text,
            extensions=["tables", "fenced_code"],
        )
    except ImportError:
        paragraphs = markdown_text.split("\n\n")
        return "".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())
