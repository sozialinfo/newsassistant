{
    "name": "News Assistant",
    "version": "18.0.1.1.0",
    "category": "Productivity",
    "summary": "Automated news scraping and triage for Swiss social-sector sources",
    "description": """
        News Assistant automatically scrapes ~60 Swiss social-sector news sources,
        extracts clean article content using AI (Infomaniak AI Services),
        and presents articles in a kanban board for manual triage.
    """,
    "author": "Verein sozialinfo.ch",
    "website": "https://sozialinfo.ch",
    "license": "LGPL-3",
    "depends": [
        "base",
        "queue_job",
    ],
    "data": [
        "security/newsassistant_security.xml",
        "security/ir.model.access.csv",
        "data/news_article_stage_data.xml",
        "data/queue_job_data.xml",
        "data/ir_cron_data.xml",
        "data/ir_config_parameter_data.xml",
        "views/news_article_views.xml",
        "views/news_source_views.xml",
        "views/pipeline_monitor_views.xml",
        "views/menu.xml",
        "data/server_actions.xml",
    ],
    "demo": [
        "demo/news_source_demo.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
