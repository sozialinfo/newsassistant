from random import randint

from odoo import fields, models


class StrategyLabel(models.Model):
    _name = "strategy.label"
    _description = "Strategy Label"
    _order = "name"

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(
        string="Name",
        required=True,
        translate=True,
    )
    color = fields.Integer(
        string="Color",
        default=_get_default_color,
    )

    _sql_constraints = [
        ("name_uniq", "unique(name)", "A strategy label with this name already exists."),
    ]
