"""Image selection and validation utilities for website article header images."""
import logging
from urllib.parse import urljoin, urlparse

import requests

_logger = logging.getLogger(__name__)

MIN_IMAGE_WIDTH = 800
MIN_IMAGE_HEIGHT = 400
SKIP_URL_PATTERNS = (".svg", "logo", "icon", "footer", "avatar", "sprite", "button")
ACCEPTED_IMAGE_TYPES = ("image/jpeg", "image/png", "image/webp")
USER_AGENT = "NewsAssistant/1.0"


def should_skip_image_url(url):
    """Check if an image URL should be skipped based on patterns.

    Skips likely non-content images like logos, icons, SVGs, etc.

    Args:
        url: The image URL to check.

    Returns:
        True if the URL should be skipped, False otherwise.
    """
    url_lower = url.lower()
    return any(pattern in url_lower for pattern in SKIP_URL_PATTERNS)


def validate_and_download_image(url, base_url=None, timeout=15):
    """Download an image and validate it for use as a header image.

    Validates:
    - Format: JPEG, PNG, or WebP
    - Dimensions: minimum 800x400 pixels
    - Orientation: landscape (width > height)

    Args:
        url: The image URL to download.
        base_url: Optional base URL for resolving relative URLs.
        timeout: Request timeout in seconds.

    Returns:
        Tuple of (image_data, filename) if valid, or (None, None) if invalid.
    """
    from io import BytesIO

    try:
        from PIL import Image
    except ImportError:
        _logger.warning("Pillow not available; skipping image validation")
        return None, None

    # Resolve relative URLs
    if base_url and not url.startswith("http"):
        url = urljoin(base_url, url)

    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)

        if response.status_code != 200:
            _logger.debug("Image fetch failed: HTTP %s for %s", response.status_code, url)
            return None, None

        content_type = response.headers.get("Content-Type", "").lower()
        if not any(t in content_type for t in ACCEPTED_IMAGE_TYPES):
            _logger.debug("Image rejected: unsupported format %s for %s", content_type, url)
            return None, None

        img = Image.open(BytesIO(response.content))
        width, height = img.size

        if width <= height:
            _logger.debug("Image rejected: not landscape (%dx%d) for %s", width, height, url)
            return None, None

        if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT:
            _logger.debug("Image rejected: too small (%dx%d) for %s", width, height, url)
            return None, None

        parsed_url = urlparse(url)
        filename = parsed_url.path.split("/")[-1] or "header_image.jpg"
        if "?" in filename:
            filename = filename.split("?")[0]

        _logger.debug("Image accepted: %dx%d from %s", width, height, url)
        return response.content, filename

    except requests.exceptions.Timeout:
        _logger.debug("Image fetch timeout for %s", url)
        return None, None
    except requests.exceptions.RequestException as e:
        _logger.debug("Image fetch error for %s: %s", url, e)
        return None, None
    except Exception as e:
        _logger.debug("Image validation error for %s: %s", url, e)
        return None, None


def select_header_image(images_dict, base_url=None):
    """Select the first suitable header image from a dictionary of images.

    Args:
        images_dict: Dictionary of {label: url} from Jina response.
        base_url: Optional base URL for resolving relative URLs.

    Returns:
        Tuple of (image_data, filename) if found, or (None, None) if no suitable image.
    """
    if not images_dict:
        return None, None

    for label, url in images_dict.items():
        if not url:
            continue
        if should_skip_image_url(url):
            _logger.debug("Skipping image by URL pattern: %s", url[:80])
            continue
        image_data, filename = validate_and_download_image(url, base_url)
        if image_data:
            _logger.info("Selected header image: %s (%s)", filename, label)
            return image_data, filename

    _logger.debug("No suitable header image found in %d candidates", len(images_dict))
    return None, None
