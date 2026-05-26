"""Set initial state on existing articles based on scrape_date and content."""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Set initial article states based on existing data.

    Logic:
    - scrape_date IS NULL → pending (never extracted)
    - content LIKE '[Error:%' → error (extraction failed)
    - else → scraped (successfully extracted)
    """
    if not version:
        return

    _logger.info("Setting initial article states...")

    # Set pending for articles that were never scraped
    cr.execute("""
        UPDATE news_article
        SET state = 'pending'
        WHERE scrape_date IS NULL
          AND (state IS NULL OR state = 'pending')
    """)
    pending_count = cr.rowcount
    _logger.info("Set %d articles to 'pending' state", pending_count)

    # Set error for articles with error content
    cr.execute("""
        UPDATE news_article
        SET state = 'error',
            error_message = content,
            last_error_date = scrape_date,
            retry_count = 1
        WHERE scrape_date IS NOT NULL
          AND content LIKE '[Error:%'
          AND (state IS NULL OR state = 'pending')
    """)
    error_count = cr.rowcount
    _logger.info("Set %d articles to 'error' state", error_count)

    # Set scraped for all remaining articles
    cr.execute("""
        UPDATE news_article
        SET state = 'scraped'
        WHERE scrape_date IS NOT NULL
          AND (content IS NULL OR content NOT LIKE '[Error:%')
          AND (state IS NULL OR state = 'pending')
    """)
    scraped_count = cr.rowcount
    _logger.info("Set %d articles to 'scraped' state", scraped_count)

    _logger.info(
        "Migration complete: %d pending, %d error, %d scraped",
        pending_count, error_count, scraped_count
    )
