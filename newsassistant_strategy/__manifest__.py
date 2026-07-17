{
    "name": "News Assistant - Strategy Base",
    "version": "18.0.1.2.0",
    "category": "Productivity",
    "summary": "Shared strategy model for the News Assistant strategy ecosystem",
    "description": """
        Base module providing the shared strategy.strategy model
        plus unified strategy evaluation infrastructure.

        Sister modules (newsassistant_strategy_digest, newsassistant_strategy_watch)
        extend this model with their own prompt fields and evaluation logic.

        Features:
        - Strategy management: define strategies with PDF documents, date ranges
        - Prompt tab shell: extensible form tab for sister module prompt injection
        - Unified cron: dispatches evaluation to all installed sister modules
    """,
    "author": "Verein sozialinfo.ch",
    "website": "https://sozialinfo.ch",
    "license": "LGPL-3",
    "depends": [
        "newsassistant",
        "queue_job",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron_data.xml",
        "views/strategy_strategy_views.xml",
        "views/menu.xml",
    ],
    "demo": [
        "demo/strategy_strategy_demo.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}