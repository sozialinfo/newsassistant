"""Migrate strategy.strategy: rename column prompt → digest_prompt.

The strategy base module was extracted from newsassistant_strategy_digest in
v18.0.3.0.1. The old ``prompt`` field on strategy.strategy was renamed to
``digest_prompt`` to make room for the new ``watch_prompt`` field in the
newsassistant_strategy_watch module.

Without this migration, Odoo drops ``prompt`` and creates ``digest_prompt``
as a new column, losing any previously distilled AI labelling prompts.
"""


def migrate(cr, version):
    cr.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'strategy_strategy'
                  AND column_name = 'prompt'
                  AND NOT EXISTS (
                      SELECT 1 FROM information_schema.columns
                      WHERE table_name = 'strategy_strategy'
                        AND column_name = 'digest_prompt'
                  )
            ) THEN
                ALTER TABLE strategy_strategy RENAME COLUMN prompt TO digest_prompt;
            END IF;
        END
        $$;
        """
    )