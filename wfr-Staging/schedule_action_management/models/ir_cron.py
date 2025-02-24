from odoo import api, fields, models, _


class IrCronManagement(models.Model):
    _inherit = "ir.cron"

    is_processed = fields.Boolean("Is Processed?")
