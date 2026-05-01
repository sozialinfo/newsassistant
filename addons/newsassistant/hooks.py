import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Set the default new article stage to 'New' on install."""
    stage = env["news.article.stage"].search([("name", "=", "New")], limit=1)
    if stage:
        env["ir.config_parameter"].sudo().set_param(
            "newsassistant.new_article_stage_id", str(stage.id)
        )
        _logger.info(
            "newsassistant post_init_hook: default new article stage set to '%s' (id=%s)",
            stage.name, stage.id,
        )
    else:
        _logger.warning(
            "newsassistant post_init_hook: 'New' stage not found, default stage not set"
        )
