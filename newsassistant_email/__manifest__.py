{
    "name": "News Assistant — Email",
    "version": "18.0.1.0.2",
    "category": "Productivity",
    "summary": "Inbound email capture for News Assistant",
    "description": """
        Extends News Assistant with inbound email capabilities:
        - Configurable mail alias (default: newsassistant@yourdomain.com)
        - Automatic news source creation from sender domain with AI naming
        - HTML sanitization of inbound emails
        - Snapshot creation per received email (auto-triggers article extraction)
    """,
    "author": "Verein sozialinfo.ch",
    "website": "https://sozialinfo.ch",
    "license": "LGPL-3",
    "depends": [
        "newsassistant",
        "mail",
    ],
    "data": [
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
