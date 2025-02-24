from odoo import fields, models, api


class ProductPackaging(models.Model):
    _inherit = 'stock.package.type'

    package_carrier_type = fields.Selection(selection_add=[('shipstation', 'Shipstation')],
                                            ondelete={'shipstation': 'set default'})

