from odoo import fields, models


class NewsArticleStage(models.Model):
    _name = "news.article.stage"
    _description = "News Article Stage"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    fold = fields.Boolean(default=False)
