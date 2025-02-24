import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

GS1_COMPANY_PREFIX = '0628820'


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    edi_contact_type_code = fields.Selection(related='partner_id.edi_contact_type_code')
    tradingpartner_id = fields.Char(related='edi_source_so_id.partner_id.trading_partnerid')
    state_name = fields.Char(related='partner_id.state_id.name')
    state_code = fields.Char(related='partner_id.state_id.code')
    country_name = fields.Char(related='partner_id.country_id.name')
    country_code = fields.Char(related='partner_id.country_id.code')
    edi_status = fields.Selection(selection=[
                                ('draft', 'Draft'),
                                ('pending', 'Pending'),
                                ('sent', 'Sent'),
                                ('fail', 'Failed')
                            ], string='EDI Status', default='draft', copy=False)
    edi_date = fields.Datetime(string='EDI Document Date')
    edi_shipment_identification = fields.Char(string='EDI Shipment Identification')
    asn_number = fields.Char(string='ASN Number', help='Identification number assigned to the shipment by the shipper that uniquely identifies the shipment from origin to ultimate destination and is not subject to modification')
    asn_structure_code = fields.Char(string='ASN Structure Code', help='Code is the reflection of the structure of the document. For EDI purposes.', default='0001')
    all_contacts = fields.Text(string='Contacts',
                        help='Buyer and Receiving contacts transferred from the EDI')
    contact_name = fields.Char(string='Contact Name', help='Contact Name. Passed on to the EDI 856 Outbound file.')
    contact_phone = fields.Char(string='Contact Phone', help='Contact Phone Number. Passed on to the EDI 856 Outbound file.')
    carrier_trans_method_code = fields.Selection(selection=[
                                ('A', 'Air'),
                                ('C', 'Consolidation'),
                                ('M', 'Motor[Common Carrier]'),
                                ('P', 'Private Carrier'),
                                ('BU', 'Bus'),
                                ('E', 'Expedited Truck'),
                                ('H', 'Customer Pickup'),
                                ('L', 'Contract Carrier'),
                                ('R', 'Rail'),
                                ('O', 'Containerized Ocean'),
                                ('T', 'Best Way[Shippers Option]'),
                            ], string='Carrier Trans Method', default='M')

    edi_shipment_identifier = fields.Char(string='EDI Shipment Identifier')
    edi_create_date = fields.Date(string='EDI Date')
    edi_asn_structure_code = fields.Char(string='EDI ASN Structure Code')
    edi_bill_of_lading_number = fields.Char(string='EDI Bill of Lading Number')
    edi_addresses = fields.Char(string='EDI All Addresses')
    edi_carrier_routing = fields.Char(string='EDI Carrier Routing')
    edi_lading_qty = fields.Integer(string='EDI Lading Qty')
    edi_weight = fields.Float(string='Weight (EDI)', help='Weight of the shipment used on EDI')
    edi_weight_uom_name = fields.Char(string='EDI Weight UOM Name', related='weight_uom_name')
    edi_purchase_order_number = fields.Char(string='EDI Purchase Order Number')

    edi_carrier_alpha_code = fields.Char(string='Carrier Alpha Code',
                        help='4 digit SCAC code for applicable carrier (e.g. UPSN for UPS Ground)')

    edi_carrier_routing = fields.Char(string='Carrier Routing',
                        help='Free-form description of the routing/requested routing for shipment or the originating carrier\'s identity')
    edi_weight_qualifier = fields.Selection(selection=[('G', 'Gross Weight'), ('N', 'Net Weight')], string='EDI Weight Qualifier', default='N')

    bill_of_lading_number = fields.Char(string='Bill Of Lading Number', required=False, help='A shipper assigned number that outlines the ownership, terms of carriage and is a receipt of goods')

    edi_backorder_origin = fields.Many2one(string='EDI Backorder Origin', related='sale_id.edi_backorder_origin_id')
    edi_total_line_item_number = fields.Integer(string='EDI Total Line Item Number', compute='_compute_edi_total_line_item_number')
    edi_packing_medium = fields.Selection(selection=[('CTN', 'Carton'), ('PLT', 'Pallet')], string='EDI Packing Medium', default='CTN')
    edi_fob_pay_code = fields.Selection(selection=[('PP', 'Prepaid'), ('CC', 'Collect')], string='EDI FOB Pay Code', default='PP')
    edi_source_so_id = fields.Many2one(string='EDI Source SO', related='sale_id')
    edi_tset_purpose_code = fields.Selection(related='edi_source_so_id.edi_tset_purpose_code')
    commitment_date = fields.Datetime(related='edi_source_so_id.commitment_date')
    edi_vendor = fields.Char(related='edi_source_so_id.edi_vendor')
    edi_pack_size = fields.Float(related='edi_source_so_id.edi_pack_size')
    
    edi_pack_level_type = fields.Selection(selection=[('P', 'Pack'), ('T', 'Tare/Pallet')], string='EDI Pack Level Type', default='P')
    edi_pack_weight = fields.Float(string='EDI Pack Weight', help='Weight of the pack used on EDI', related='shipping_weight')
    edi_pack_value = fields.Float(string='EDI Pack Value', help='Value of the pack used on EDI')
    edi_reference_qual = fields.Selection(selection= [
        ('CN', 'Carrier Pro Number'),
        ('GK', 'Third Party Reference Number'),
        ('WU', 'Vessel'),
        ('87', 'Functional Category'),
        ('OC', 'Ocean Container Number'),], string='EDI Reference Qualifier', default='CN')
    edi_reference_id = fields.Char(string='EDI Reference ID', help='Reference ID for the EDI')
    edi_header_reference_description = fields.Html(string='EDI Header Reference Description', help='Description of the reference ID for the EDI', related='note')
    edi_pack_qualifier = fields.Selection(string='EDI Pack Qualifier', selection=[('OU', 'Outer Pack'), ('IN', 'Inner Pack'), ('CP', 'Consumer Package')], default='CP', help='Code identifying the type of packaging; Part of the <Packaging> field on the EDI file.')
    edi_ship_from_location_id = fields.Many2one(string='EDI Ship From Location', comodel_name='res.partner', help='Ship From Location for the EDI', related='company_id.partner_id')
    edi_partner_shipping_id = fields.Many2one(string='EDI Partner Shipping', related='edi_source_so_id.partner_shipping_id')
    edi_company_warehouse_id = fields.Many2one(string='EDI Company Warehouse', comodel_name='res.partner', compute='_compute_edi_company_warehouse_id')
    edi_bill_of_landing_number = fields.Char(string='CarrierProNumber')
    edi_date_time_qualifier = fields.Char(string='Datetime Qualifier', help='Code specifying the type of date')
    qualifier_date = fields.Datetime(string='Qualifier Datetime', help='Qualifier Date')

    reference_line_ids = fields.Many2many(related="edi_source_so_id.reference_line_ids")
    notes_line_ids = fields.Many2many(related="edi_source_so_id.notes_line_ids")
    edi_po_number = fields.Char(string='EDI PO Number', related="edi_source_so_id.edi_po_number")

    def _compute_edi_company_warehouse_id(self):
        for picking in self:
            company_warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', picking.company_id.id)], limit=1)
            if not company_warehouse_id:
                company_warehouse_id = self.company_id.ids[0]
            picking.edi_company_warehouse_id = company_warehouse_id.partner_id

    def _compute_edi_total_line_item_number(self):
        for picking in self:
            picking.edi_total_line_item_number = len(picking.move_line_ids_without_package)

    @api.constrains('edi_carrier_alpha_code')
    def _check_edi_carrier_alpha_code(self):
        for picking in self:
            if (not picking.edi_carrier_alpha_code or len(
                    picking.edi_carrier_alpha_code) != 4) and picking.edi_bill_of_lading_number:
                raise ValidationError(_('Carrier Alpha Code should be 4 characters long.'))


    def generate_sscc_with_check_digit(self, sscc):
        """
        Generate the check digit for an SSCC and append it.
        Following the algorithm described here: https://www.gs1.org/services/how-calculate-check-digit-manually
        :param sscc: The SSCC without the check digit
        :return: SSCC with check digit appended
        """
        check_sum = 0
        for i, value in enumerate(sscc):
            digit = int(value)
            if i % 2 == 0:
                check_sum += 3 * digit
            else:
                check_sum += digit
        # python is weird here, and a % b will always have the same sign as b,
        # so modding a negative number is the same as subtracting from the nearest multiple of 10
        check_digit = -check_sum % 10
        sscc_complete = sscc + str(check_digit)
        _logger.info('SSCC-18 generated: %s' % sscc_complete)
        return sscc_complete


    def generate_sscc(self, pallet):
        """
        The SSCC-18 ID is an 18 digit number used in the shipping label pallet that uniquely identifies the pallet.
        It is constructed by concatenating the following:
            '00' - Application Identifier
            '0' - Extension digit
            GS1 Company Prefix - 7 digits
            Pallet Number - 9 digits
            Check digit - 1 digit
        """

        pallet_number = ''.join(e for e in pallet if e.isdigit())
        pallet_number = pallet_number.rjust(9, '0')
        sscc_without_check_digit = '0' + GS1_COMPANY_PREFIX + pallet_number
        return '00%s' % self.generate_sscc_with_check_digit(sscc_without_check_digit)

    def write_STOP(self, vals):
        """
        ToDo: Stopped this method because it's writing the data in self and based on that it's going on deadlock
        """
        res = super().write(vals)
        for picking in self:
            if picking.sale_id:
                if not picking.carrier_trans_method_code and picking.sale_id.carrier_trans_method_code:
                    picking['carrier_trans_method_code'] = picking.sale_id.carrier_trans_method_code
                if not picking.edi_carrier_routing and picking.sale_id.edi_carrier_routing:
                    picking['edi_carrier_routing'] = picking.sale_id.edi_carrier_routing

            related_picking_update_values = {key: vals.get(key) for key in picking._get_related_picking_keys() if
                                             key in vals}
            self.env['stock.picking'].sudo().search([('origin', '=', picking.origin)]).write(
                related_picking_update_values)
        return res

    def _get_related_picking_keys(self):
        return ['bill_of_lading_number', 'edi_carrier_alpha_code', 'edi_carrier_routing', 'carrier_trans_method_code', 'edi_weight', 'contact_name', 'contact_phone']

    def _check_required_edi_fields(self):
        if not self.edi_bill_of_lading_number or not self.carrier_trans_method_code or not self.edi_carrier_alpha_code:
            raise ValidationError('Bill Of Lading Number, Carrier Trans Method, and Carrier Alpha Code are mandatory fields.')

        for line in self.move_line_ids_without_package:
            if not line.product_uom_id:
                raise ValidationError('All lines must have an EDI UoM assigned to create the ASN file.')


    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        pickings_to_sync = self.env['stock.picking']
        for picking in self:
            # Only selected partners with output deliveries that come from a sale order need ASN
            if (picking.partner_id.outbound_edi_asn or picking.partner_id.parent_id.outbound_edi_asn) \
                    and picking.picking_type_id.sequence_code == 'OUT' \
                    and picking.origin and not picking.company_id.is_logistics:
                pickings_to_sync |= picking
                picking._check_required_edi_fields()


        if pickings_to_sync:
            base_edi = self.env['edi.sync.action']
            sync_action = base_edi.search([('doc_type_id.doc_code', '=', 'export_shipment_xml')], limit=1)
            if sync_action:
                base_edi._do_doc_sync_cron(sync_action_id=sync_action, records=pickings_to_sync)
        return res

    def _get_edi_partner(self):
        self.ensure_one()
        return self.partner_id

    def get_edi_name(self):
        self.ensure_one()
        return self.name.replace('/', '_')
