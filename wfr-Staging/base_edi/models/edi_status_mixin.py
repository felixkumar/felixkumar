from odoo import fields, models

class EdiStatusMixin(models.AbstractModel):
    _name = 'edi.status.mixin'
    _description = 'EDI Status Mixin'

    edi_status = fields.Selection(selection=[
            ('draft', 'Draft'),
            ('pending', 'Pending'),
            ('sent', 'Sent'),
            ('fail', 'Failed')
        ], string='EDI Status', default='draft', copy=False)
    edi_date = fields.Date(string='Edi Date')

