from odoo import models, fields


class EdiErrorLog(models.Model):
    _inherit = 'edi.error.log'
    _description = 'EDI Error Log'

    # error_id = fields.Char('Error ID')
    # timestamp = fields.Datetime('Timestamp')
    # error_code = fields.Char('Error Code')
    # description = fields.Text('Description')
    # type = fields.Selection(selection=[
    #     ('error', 'Error'),
    #     ('unmapped_fields', 'Unmapped Fields')], string='Type')
