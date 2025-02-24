from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        session_info = super().session_info()
        session_info["iot_channel"] = self.env['iot.channel'].get_iot_channel()
        return session_info
