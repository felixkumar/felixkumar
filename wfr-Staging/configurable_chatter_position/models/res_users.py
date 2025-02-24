from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    context_chatter_position = fields.Selection([
        ("chatter_bottom", "Bottom"),
        ("chatter_right", "Right")
    ],
        string="Chatter Position",
        default="chatter_right",
    )

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ['context_chatter_position']

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ['context_chatter_position']