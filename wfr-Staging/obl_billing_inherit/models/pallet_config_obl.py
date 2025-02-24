from odoo import fields, models, api


class PalletConfigOBLInherit(models.Model):
    _inherit = 'pallet.config.obl'

    fulfillment_method = fields.Selection(selection=[('bulk_orders', 'Bulk Order'),
                                                     ('e-commerce', 'E-Commerce')], string="Fulfillment Method")
