{
    "name": "News Assistant — Email",
    "version": "18.0.1.2.0",
    "category": "Productivity",
    "summary": "Inbound email capture for News Assistant",
    "description": "Inbound email capture, alias-based snapshot creation, and AI-powered news source discovery for News Assistant.",
    "images": ["static/description/icon.png"],
    "author": "Verein sozialinfo.ch",
    "website": "https://sozialinfo.ch",
    "license": "LGPL-3",
    "depends": [
        "newsassistant",
        "mail",
    ],
    "data": [
        "data/queue_job_email_data.xml",
        "security/ir.model.access.csv",
        "data/mail_alias_data.xml",
        "views/res_config_settings_views.xml",
        "views/news_snapshot_views.xml",
    ],
    "demo": [
        "demo/email_source_demo.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
