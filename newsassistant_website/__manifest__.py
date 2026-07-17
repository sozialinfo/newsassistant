{
    "name": "News Assistant — Website",
    "version": "18.0.2.1.0",
    "category": "Marketing",
    "summary": "Website scraping for News Assistant",
    "description": """
        Extends News Assistant with website scraping capabilities:
        - crawl4ai integration for JavaScript-rendered pages
        - AI-powered article URL discovery from listing pages
        - Per-article snapshot creation with Markdown→HTML conversion
        - Header image selection and validation
        - Daily cron job for all active website sources
    """,
    "author": "Verein sozialinfo.ch",
    "website": "https://sozialinfo.ch",
    "license": "LGPL-3",
    "depends": [
        "newsassistant",
        "queue_job",
    ],
    "data": [
        "data/queue_job_data.xml",
        "data/ir_cron_data.xml",
        "views/news_source_website_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "demo": [
        "demo/demo_setup.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "post_init_hook": "hooks.post_init_hook",
}
