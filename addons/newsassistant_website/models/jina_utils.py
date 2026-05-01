"""Jina Reader API utilities for website content fetching."""
import logging
import os

import requests

from odoo.addons.queue_job.exception import RetryableJobError

_logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 30
MAX_CONTENT_LENGTH = 30000
TRANSIENT_HTTP_CODES = {408, 429, 500, 502, 503, 504}


def fetch_page(url):
    """Fetch a page using the Jina Reader API.

    Jina renders JavaScript and returns clean markdown content along with
    images found on the page.
    Requires JINA_API_KEY environment variable.

    Args:
        url: The URL to fetch.

    Returns:
        Tuple of (content, images_dict):
            - content: Markdown content from the page (truncated to MAX_CONTENT_LENGTH)
            - images_dict: Dictionary of {label: image_url} for images on the page

    Raises:
        ValueError: If JINA_API_KEY is not set or on permanent API errors.
        RetryableJobError: On transient failures (timeout, 5xx, rate limit).
    """
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
                "Accept": "application/json",
                "X-With-Images-Summary": "all",
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

    # Parse JSON response
    try:
        data = response.json()
        jina_data = data.get("data", {})
        content = jina_data.get("content", "")
        images_dict = jina_data.get("images", {})
    except (ValueError, KeyError) as e:
        raise ValueError(f"Failed to parse Jina JSON response: {e}")

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
        # Minimal fallback: wrap in paragraphs on blank lines
        paragraphs = markdown_text.split("\n\n")
        return "".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())
