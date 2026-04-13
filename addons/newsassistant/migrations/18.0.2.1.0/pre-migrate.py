"""Rename error_message to status_message and add active field."""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Rename error_message column to status_message.

    This is a pre-migration to rename the column before the ORM
    tries to create status_message as a new column.
    """
    if not version:
        return

    _logger.info("Renaming error_message to status_message...")

    # Check if error_message column exists
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'news_article'
          AND column_name = 'error_message'
    """)
    if cr.fetchone():
        cr.execute("""
            ALTER TABLE news_article
            RENAME COLUMN error_message TO status_message
        """)
        _logger.info("Renamed error_message to status_message")
    else:
        _logger.info("Column error_message does not exist, skipping rename")

    # Add active column if it doesn't exist (with default True)
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'news_article'
          AND column_name = 'active'
    """)
    if not cr.fetchone():
        cr.execute("""
            ALTER TABLE news_article
            ADD COLUMN active BOOLEAN DEFAULT TRUE
        """)
        _logger.info("Added active column with default True")
    else:
        _logger.info("Column active already exists, skipping")
