"""Shared utility functions for the newsassistant module."""

import logging

_logger = logging.getLogger(__name__)

try:
    from bs4 import BeautifulSoup, Comment, NavigableString, Tag
    _BS4_AVAILABLE = True
except ImportError:  # pragma: no cover
    _BS4_AVAILABLE = False  # pragma: no cover
    _logger.warning("beautifulsoup4 not available — html_to_markdown will strip tags only")  # pragma: no cover


def html_to_markdown(html):
    """Convert an HTML string to a plain-text Markdown-like representation.

    Converts common HTML elements to Markdown equivalents:
    - <p>, <br> → newlines
    - <h1>–<h6> → # … ###### prefix
    - <li> → "- " prefix
    - <strong>, <b> → **...**
    - <em>, <i> → *...*
    - All other tags → stripped, inner text preserved

    Args:
        html (str | None): HTML string to convert. None or empty returns "".

    Returns:
        str: Plain-text Markdown representation, stripped of leading/trailing whitespace.
    """
    if not html:
        return ""

    if not _BS4_AVAILABLE:  # pragma: no cover
        # Fallback: strip all tags via simple replacement  # pragma: no cover
        import re  # pragma: no cover
        text = re.sub(r"<[^>]+>", " ", html)  # pragma: no cover
        return re.sub(r"\s+", " ", text).strip()  # pragma: no cover

    soup = BeautifulSoup(html, "html.parser")
    return _node_to_markdown(soup).strip()


def _node_to_markdown(node):
    """Recursively convert a BeautifulSoup node to Markdown text."""
    if isinstance(node, Comment):
        return ""

    if isinstance(node, NavigableString):
        return str(node)

    if not isinstance(node, Tag):
        return ""

    tag = node.name.lower() if node.name else ""

    # Block-level elements that produce newlines
    if tag in ("p", "div", "blockquote", "pre"):
        inner = "".join(_node_to_markdown(c) for c in node.children)
        return "\n" + inner.strip() + "\n"

    if tag == "br":
        return "\n"

    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        level = int(tag[1])
        inner = "".join(_node_to_markdown(c) for c in node.children).strip()
        return "\n" + "#" * level + " " + inner + "\n"

    if tag in ("ul", "ol"):
        items = []
        for child in node.children:
            if isinstance(child, Tag) and child.name == "li":
                item_text = "".join(_node_to_markdown(c) for c in child.children).strip()
                items.append("- " + item_text)
        return "\n" + "\n".join(items) + "\n"

    if tag == "li":
        inner = "".join(_node_to_markdown(c) for c in node.children).strip()
        return "- " + inner + "\n"

    # Inline formatting
    if tag in ("strong", "b"):
        inner = "".join(_node_to_markdown(c) for c in node.children).strip()
        return "**" + inner + "**" if inner else ""

    if tag in ("em", "i"):
        inner = "".join(_node_to_markdown(c) for c in node.children).strip()
        return "*" + inner + "*" if inner else ""

    # Ignored structural tags — just recurse into children
    return "".join(_node_to_markdown(c) for c in node.children)


def html_has_content(html):
    """Return True if the HTML contains any visible text content.

    Uses BeautifulSoup's get_text() which correctly handles cases like
    ``<h2><br></h2>`` or ``<p><br></p>`` (empty editor states) returning False.

    Args:
        html (str | Markup | None): HTML string to check.

    Returns:
        bool: True if there is any non-whitespace text in the HTML.
    """
    if not html:
        return False
    if not _BS4_AVAILABLE:  # pragma: no cover
        import re  # pragma: no cover
        return bool(re.sub(r"<[^>]+>", "", str(html)).strip())  # pragma: no cover
    return bool(BeautifulSoup(str(html), "html.parser").get_text().strip())
