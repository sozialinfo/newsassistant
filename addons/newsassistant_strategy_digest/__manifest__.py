{
    "name": "News Assistant - Strategy Digest",
    "version": "18.0.1.0.1",
    "category": "Productivity",
    "summary": "AI-powered strategy digest: label articles by strategic relevance and generate executive briefs",
    "description": """
        Strategy Digest extends News Assistant with strategy-aware article labelling and
        executive brief generation.

        Features:
        - Strategy labels: coloured tags for strategic relevance (managed in Configuration)
        - Strategy management: define strategies with PDF documents, date ranges, and labels
        - AI prompt distillation: extract text from strategy PDFs and generate a labelling prompt
        - Automatic article evaluation: cron job evaluates articles against active strategies
        - Strategy digest: AI-generated HTML brief for a selected period, exportable as PDF
        - PDF export inherits company paper format, logo, fonts and colours from company settings
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
        "views/strategy_label_views.xml",
        "views/strategy_strategy_views.xml",
        "views/strategy_digest_views.xml",
        "views/news_article_views.xml",
        "views/menu.xml",
        "report/strategy_digest_report.xml",
        "report/strategy_digest_report_template.xml",
    ],
    "demo": [
        "demo/strategy_label_demo.xml",
        "demo/strategy_strategy_demo.xml",
        "demo/strategy_digest_demo.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
