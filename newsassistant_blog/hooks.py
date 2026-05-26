import logging

_logger = logging.getLogger(__name__)


def _find_or_create_stage(env, name, sequence, fold=False):
    """Find a stage by name or create it if missing. Returns the stage record."""
    stage = env["news.article.stage"].search([("name", "=", name)], limit=1)
    if not stage:
        _logger.info("newsassistant_blog post_init_hook: creating stage '%s'", name)
        stage = env["news.article.stage"].create({
            "name": name,
            "sequence": sequence,
            "fold": fold,
        })
    return stage


def post_init_hook(env):
    """Auto-link or create standard pipeline stages and the News blog on install."""
    ICP = env["ir.config_parameter"].sudo()

    # --- Pipeline stages ---
    shortlist = _find_or_create_stage(env, "Shortlist", sequence=20, fold=False)
    ICP.set_param("newsassistant_blog.shortlist_stage_id", str(shortlist.id))

    published = _find_or_create_stage(env, "Published", sequence=30, fold=True)
    ICP.set_param("newsassistant_blog.published_stage_id", str(published.id))

    discarded = _find_or_create_stage(env, "Discarded", sequence=40, fold=True)
    ICP.set_param("newsassistant_blog.discard_stage_id", str(discarded.id))

    # --- Default blog ---
    blog = env["blog.blog"].search([("name", "=", "News")], limit=1)
    if not blog:
        _logger.info("newsassistant_blog post_init_hook: creating blog 'News'")
        blog = env["blog.blog"].create({"name": "News"})
    ICP.set_param("newsassistant_blog.blog_id", str(blog.id))

    _logger.info(
        "newsassistant_blog post_init_hook: "
        "shortlist=%s, published=%s, discarded=%s, blog=%s",
        shortlist.name, published.name, discarded.name, blog.name,
    )
