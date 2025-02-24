from odoo import api, fields, models, _


class EdiCustomerStore(models.Model):
    _name = 'edi.customer.store'

    name = fields.Char(string="Name")
    trading_partner_id = fields.Char(string="Trading Partner ID")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    edi_store_id = fields.Many2one("edi.customer.store", string="EDI Store ID")
    send_edi_inv = fields.Boolean(string='Send 810 Invoice',
                                  help='Whether the contact sends outbound 810 Invoices to the EDI.')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    edi_store_id = fields.Many2one("edi.customer.store", string="EDI Store ID")
