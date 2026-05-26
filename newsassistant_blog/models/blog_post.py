from odoo import fields, models


class BlogPost(models.Model):
    _inherit = "blog.post"

    news_article_id = fields.Many2one(
        "news.article",
        string="Source Article",
        readonly=True,
        ondelete="set null",
        index=True,
        help="The news article this blog post was generated from",
    )

    _sql_constraints = [
        (
            "news_article_unique",
            "UNIQUE(news_article_id)",
            "A blog post already exists for this news article.",
        ),
    ]
