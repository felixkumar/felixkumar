import logging
from datetime import datetime, date, time

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'edi.import.tools.mixin']

    edi_shipment_identifier = fields.Char(string='EDI Shipment Identifier')
    edi_create_date = fields.Date(string='EDI Date')
    edi_asn_structure_code = fields.Char(string='EDI ASN Structure Code')
    edi_carrier_routing = fields.Char(string='EDI Carrier Routing')
    edi_bill_of_lading_number = fields.Char(string='EDI Bill of Lading Number')
    edi_addresses = fields.Char(string='EDI All Addresses')
    edi_carrier_alpha_code = fields.Char(string='EDI Carrier Alpha Code')
    edi_lading_qty = fields.Integer(string='EDI Lading Qty')
    edi_weight = fields.Float(string='EDI Weight')
    edi_weight_uom_name = fields.Char(string='EDI Weight UOM Name')
    edi_purchase_order_number = fields.Char(string='EDI Purchase Order Number')

    @api.model_create_multi
    def create(self, vals_list):
        picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing'),('company_id', '=', self.env.company.id)], limit=1)
        loc_from = picking_type.default_location_src_id.id
        loc_from = loc_from or self.env['stock.location'].search([('usage', '=', 'internal'), ('company_id', '=', self.env.company.id)], limit=1).id
        loc_to = self.env['stock.location'].search([('usage', '=', 'customer')], limit=1).id
        for vals in vals_list:
            if 'location_id' not in vals:
                vals.update(picking_type_id=picking_type.id, location_id=loc_from, location_dest_id=loc_to)
        res = super().create(vals_list)
        if self._context.get('is_edi'):
            for picking in res:
                res.action_confirm()
                res.button_validate()
                picking.sale_id = self.env['sale.order'].search(
                    [('edi_po_number', '=', picking.edi_purchase_order_number)])
        return res
    @api.model
    def get_edi_create_date(self, node, additional_fields, nsmap=None):
        ship_date = date.fromisoformat(self.default_text(node)) if node is not None else date.today()
        ship_time = time.fromisoformat(self.default_text(additional_fields.get('ShipNoticeTime')))
        return datetime.combine(ship_date, ship_time)

class StockMoveLine(models.Model):
    _name = 'stock.move.line'
    _inherit = ['stock.move.line', 'edi.import.tools.mixin']

    edi_line_sequence_number = fields.Integer(string='EDI Sequence Number')
    edi_buyer_part_number = fields.Char(string='EDI Buyer Part Number')
    edi_vendor_part_number = fields.Char(string='EDI Vendor Part Number')
    edi_consumer_package_code = fields.Char(string='EDI Consumer Package Code')
    edi_lot_name = fields.Char(string='EDI Lot Name')

    @api.model
    def create(self, vals):
        res = super().create(vals)
        for line in res:
            line.edi_lot_name = line.edi_lot_name or vals.get('edi_lot_name') or ''
            if line.edi_lot_name:
                line.lot_id = self.env['stock.lot'].search([('name', '=', line.edi_lot_name), ('product_id', '=', res.product_id.id)])
        return res

    @api.model
    def get_product_from_xml(self, node, additional_fields, nsmap=None):
        Product = self.env['product.product']
        barcode = node.text
        product = Product.search([('barcode', '=', barcode)], limit=1)

        if not product:  # For variants, strip the leading and trailing characters
            product = Product.search([('barcode', '=', barcode[1:])], limit=1)

        if not product:  # For Case UPC, strip the leading and trailing characters
            product = Product.search([('barcode', '=', barcode[1:-1])], limit=1)

        if product:
            product.sudo().write({
                'edi_gtin': self.default_text(additional_fields.get('GTIN')),
                'edi_ean': self.default_text(additional_fields.get('EAN'))
            })

        if not product:
            _logger.info('Product Not found FROM the EDI:\n Barcode: %s' % (barcode))
            product = self.env.ref('edi_sale_common.edi_product_product_error')

        return {
            'product_id': product.id,
            'edi_consumer_package_code': barcode
        }
