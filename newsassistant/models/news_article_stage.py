from odoo import fields, models


class NewsArticleStage(models.Model):
    """Kanban stages for the article triage workflow.

    Stages define the kanban columns used for manual article triage
    (e.g. New, Shortlist, Relevant, Archived, Discarded).
    """
    _name = "news.article.stage"
    _description = "News Article Stage"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    fold = fields.Boolean(default=False)
