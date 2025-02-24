# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class Partner(models.Model):
    _inherit = 'res.partner'

    outbound_edi_asn = fields.Boolean(string='Send 856 Advance Shipping Notice', help='Whether the contact sends outbound 855 Purchase Order Acknowledement to the EDI.')
    edi_address_type_code = fields.Selection([
        ('ST', 'Ship To'),
        ('SF', 'Ship From'),
        ('WH', 'Warehouse')],
        string='EDI Address Type Code',
        help='Code identifying an organizational entity, a physical location, property, or an individual<')
    edi_address_location_number = fields.Char(string='Address Location Number', help='Unique value assigned to identify a location. For EDI use.')
    edi_contact_type_code = fields.Selection(selection_add=[( 'IC', 'Primary Information Contact')])
    state_name = fields.Char(string='State Name', related='state_id.name')
    country_name = fields.Char(string='Country Name', related='country_id.name')
