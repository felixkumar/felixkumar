from odoo import fields, models


class IrActionsReportXml(models.Model):
    _inherit = 'ir.actions.report'

    report_type = fields.Selection(selection_add=[("xlsx", "xlsx")])
