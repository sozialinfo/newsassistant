{
    "name": "News Assistant - Strategy Watch",
    "version": "18.0.1.1.0",
    "category": "Productivity",
    "summary": "Strategy impact detection: flag articles with strategic watch relevance",
    "description": """
        Strategy Watch extends the Strategy base module with strategic impact detection.

        Features:
        - Watch prompt per strategy: AI-generated prompt for detecting strategic impact
        - Article watch flagging: boolean star toggle on kanban cards
        - Automatic evaluation: articles evaluated against active strategies' watch prompts
        - Kanban star: clickable boolean_favorite star widget
        - Search filters: filter by watch status and pending evaluation state
    """,
    "author": "Verein sozialinfo.ch",
    "website": "https://sozialinfo.ch",
    "license": "LGPL-3",
    "depends": [
        "newsassistant_strategy",
        "newsassistant",
    ],
    "data": [
        "views/strategy_strategy_views.xml",
        "views/news_article_views.xml",
        "views/menu.xml",
    ],
    "demo": [
        "demo/strategy_watch_demo.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "newsassistant_strategy_watch/static/src/views/fields/strategy_watch/strategy_watch_field.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}