{
    "name": "News Assistant",
    "version": "18.0.3.5.0",
    "category": "Marketing",
    "summary": "Automated news capture and triage — base module",
    "description": """
        News Assistant base module. Provides the core data model:
        - news.source (typed: website or email)
        - news.snapshot (raw HTML capture)
        - news.article (extracted and structured content)
        - news.log / news.log.entry (unified logging)

        Install newsassistant_website for website scraping.
        Install newsassistant_email for inbound email capture.
    """,
    "author": "Verein sozialinfo.ch",
    "maintainer": "Verein sozialinfo.ch",
    "website": "https://sozialinfo.ch",
    "license": "LGPL-3",
    "external_dependencies": {"python": ["requests", "beautifulsoup4"]},
    "depends": [
        "base",
        "queue_job",
    ],
    "data": [
        "security/newsassistant_security.xml",
        "security/newsassistant_record_rules.xml",
        "security/ir.model.access.csv",
        "data/news_article_stage_data.xml",
        "data/ir_config_parameter_data.xml",
        "data/queue_job_data.xml",
        "data/server_actions.xml",
        "views/res_config_settings_views.xml",
        "views/news_snapshot_views.xml",
        "views/news_article_views.xml",
        "views/news_source_views.xml",
        "views/news_article_stage_views.xml",
        "views/news_log_views.xml",
        "views/menu.xml",
    ],
    "demo": [
        "demo/news_source_demo.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": True,
    "auto_install": False,
}
