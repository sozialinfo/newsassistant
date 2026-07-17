{
    "name": "Newsassistant Blog",
    "version": "18.0.1.4.0",
    "category": "Website",
    "summary": "AI-powered news curation and blog publishing",
    "description": """
        Newsassistant Blog automates article triage using AI evaluation against a
        user-defined content strategy. Relevant articles get AI-generated
        teasers and are automatically published to the Odoo blog.

        Features:
        - Three-way AI triage: relevant, uncertain, discard
        - Configurable content strategy prompt
        - Automatic teaser generation
        - Blog post creation with source attribution
        - Integration with existing kanban workflow
    """,
    "author": "Verein sozialinfo.ch",
    "website": "https://sozialinfo.ch",
    "license": "LGPL-3",
    "depends": [
        "newsassistant",
        "website_blog",
    ],
    "data": [
        "data/ir_config_parameter_data.xml",
        "data/ir_cron_data.xml",
        "views/news_article_views.xml",
        "views/blog_post_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "demo": [
        "demo/demo_data.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
}
