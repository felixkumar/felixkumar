
from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        info = super().session_info()
        info["context_chatter_position"] = self.env.user.context_chatter_position
        return info
