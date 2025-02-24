from odoo import api, fields, models


class ReferenceLine(models.Model):
    _name = "reference.line"

    ReferenceQual = fields.Char(string='Reference Qual', required=True)
    ReferenceID = fields.Char(string='Reference ID', required=True)


class NotesLine(models.Model):
    _name = "notes.line"

    NoteCode = fields.Char(string='Note Code', required=True)
    Note = fields.Char(string='Note', required=True)


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'edi.status.mixin']

    reference_line_ids = fields.Many2many('reference.line')
    notes_line_ids = fields.Many2many('notes.line')

    trading_partnerid = fields.Char(related='partner_id.trading_partnerid')
    edi_contact_type_code = fields.Selection(related='partner_id.edi_contact_type_code')

    edi_po_number = fields.Char(string='EDI PO Number', help='Purchase order number from the EDI')
    edi_vendor = fields.Char(string='EDI Vendor Number')
    edi_department = fields.Char(string='EDI Department Number')
    edi_backorder_origin_id = fields.Many2one('sale.order', string='EDI Backorder Origin', help='Order from the EDI for which the current order is a backorder.')
    edi_all_contacts = fields.Text(string='Contacts', help='Buyer and Receiving contacts transferred from the EDI')
    edi_addresses = fields.Text(string='Addresses', help='Delivery and Invoicing addresses transferred from the EDI')
    edi_date = fields.Datetime(string='EDI Document Date')
    edi_tset_purpose_code = fields.Selection([
        ('00', 'New Purcahse Order'),
        ('05', 'Cancellation'),
        ('06', 'Confirmation'),
        ('07', 'Duplicate'),
        ('NA', 'Unavailable')],
        string='TSET Purpose Code',
        help='Code identifying purpose or function of the transmission')
    edi_primary_PO_type_code = fields.Selection([
        ('SA', 'Stock Assisted'),
        ('SAD', 'Stock Assisted Delivery'),
        ('NE', 'New Order'),
        ('PR', 'Promotion Information'),
        ('RO', 'Rush Order'),
        ('CF', 'Confirmation'),
        ('NA', 'Unavailable')],
        string='Primary PO Type Code',
        help='Code indicating the specific details regarding the ordering document')
    edi_primary_PO_type_description = fields.Char(string='Primary PO Type Description', help='Free form text to describe the specific details regarding the ordering document.')
    edi_contract_type = fields.Char(string='contract Type', help='Contract Type')
    edi_customer_payment_terms = fields.Text(string='Payment Terms')
    edi_date_time_qualifier = fields.Char(string='Datetime Qualifier', help='Code specifying the type of date')
    edi_requested_pickup_date = fields.Datetime(string='Requested Pickup Date', help='Date and time when x_date_time_qualifier equals 118')
    ship_not_before_date = fields.Datetime(string='Ship Not Before', help='Date and time when x_date_time_qualifier equals 038')
    delivery_requested_date = fields.Datetime(string='Delivery Requested', help='Date and time when x_date_time_qualifier equals 037')
    evaluation_date = fields.Datetime(string='Evaluation Date', help='Date and time when x_date_time_qualifier equals 063')
    edi_additional_date = fields.Datetime(string='Additional Date', help='Date and time when x_date_time_qualifier is neithor 002 nor 118')
    edi_carrier_trans_method_code = fields.Selection(selection=[
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
        ('T',  'Best Way[Shippers Option]'),
        ('U', 'Private Parcel Service')], string='Carrier Trans Method', default='M')
    edi_carrier_routing = fields.Char(string='Carrier Routing', help='Free-form description of the routing/requested routing for shipment or the originating carrier\'s identity')
    edi_reference_qual = fields.Selection([
        ('12', 'IA: Billing Account Number'),
        ('AH', 'Agreement Number'),
        ('IT', 'Internal Customer Number'),
        ('CT', 'Contract Number'),
        ('NA', 'Undefined')], string='Reference Qualifier', help='Code specifying the type of data in the ReferenceID/ReferenceDescription')
    edi_reference_id = fields.Char(string='Reference ID', help='Value as defined by the ReferenceQual')
    edi_description = fields.Char(string='Description', help='Free-form textual description to clarify the related data elements and their content')
    edi_note_code = fields.Selection([
                        ('GEN', 'ZZ: General Note'),
                        ('SHP', 'Shipping Note'),
                        ('NA', 'Undefined')], string='Note Code', help='Code specifying the type of note')
    edi_charges_allowance_ids = fields.Many2many(comodel_name='charge.allowance',
                                          string='Charges Allowances',
                                          help='Charges Allowances from EDI at Header and LineItem level.')
    edi_total_line_item_number = fields.Integer(string='Total Line Item Number', help='Sum of the total number of line items in this document', compute="_compute_edi_total_line_item_number")
    edi_acknowledgement_type = fields.Selection([
        ('AC', 'Acknowledge-With Detail and Change'),
        ('AD', 'Acknowledge-With Detail No Change'),
        ('AP', 'Acknowledge-Product Replenishment'),
        ('RD', 'Reject with Detail')], default='AC', string='Acknowledgement Type', help='Code defining the vendor\'s status of the order as well as how much detail is being provided in the acknowledgement')
    edi_bill_of_lading_number = fields.Char(string='Bill Of Lading Number', required=False, help='A shipper assigned number that outlines the ownership, terms of carriage and is a receipt of goods')

    edi_is_drop_ship = fields.Boolean(string='Dropship', required=False, help='Is DropShip')
    edi_purchase_order_date = fields.Char(string='Purchase Order Date', required=False, compute='_compute_purchase_order_date', help='Purchase Order Date')
    edi_purchase_order_time = fields.Char(string='Purchase Order Time', required=False, compute='_compute_purchase_order_time', help='Purchase Order Time')
    edi_pack_size = fields.Float(string='Total Pack Size', help='Measurable size of the all sellable unit.', compute='_compute_pack_size')

    def _compute_pack_size(self):
        for order in self:
            order.edi_pack_size = sum(order.order_line.mapped('edi_pack_size')) or 0.0

    def _compute_purchase_order_date(self):
        for order in self:
            order.edi_purchase_order_date = order.date_order.date()

    def _compute_purchase_order_time(self):
        for order in self:
            order.edi_purchase_order_time = order.date_order.time()

    @api.depends('order_line')
    def _compute_edi_total_line_item_number(self):
        for order in self:
            valid_order_line_ids = order.order_line.filtered_domain([('display_type','not in',['line_note', 'line_section'])])
            order.edi_total_line_item_number = len(valid_order_line_ids)

    def _get_partner(self):
        self.ensure_one()
        return self.partner_id
    
    def get_edi_name(self):
        self.ensure_one()
        return self.display_name

class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _inherit = ['sale.order.line', 'edi.import.tools.mixin']

    edi_consumer_package_code = fields.Char(string='Consumer Package Code (EDI)', help='Consumer Package Code passed from the EDI. We store it because sometime it contains leading or training zeros that we need to transmit outbound. When searching for a product sometimes we need to strip these zeros to find the match.')
    edi_line_sequence_number = fields.Char(string='Line Sequence Number', help='For an initiated document, this is a unique number for the line item[s]. For a return transaction, this number should be the same as what was received from the source transaction. Example: You received a Purchase Order with the first LineSequenceNumber of 10. You would then send back an Invoice with the first LineSequenceNumber of 10')
    edi_buyer_part_number = fields.Char(string='Buyer Part Number', help='Buyer\'s primary product identifier')
    edi_vendor_part_number = fields.Char(string='Vendor Part Number', help='Vendor\'s primary product identifier')
    edi_part_number = fields.Char(string='Part Number', help='Vendor\'s part number. Belongs to the <ProductID> field on the EDI file.')
    edi_pack_size = fields.Float(string='Pack Size', help='Measurable size of the sellable unit.')
    edi_package_id = fields.Many2one('product.packaging', string='Package')
    price_unit = fields.Float(string='Gross Selling Price',
                              help='Price for specific case size for specific trading partner.')
    edi_price = fields.Float(string='EDI Price', digits='Product Price',
                                      help='Price passed from the EDI. If the order is in Cases and the price is in units, it will be converted to case price.')
    edi_unit_price = fields.Float(string='EDI Price (Units)',
                                    digits='Product Price',
                                    compute='_compute_unit_price',
                                    help='Unit Price passed from the EDI. If the EDI price was provided per case, this field divides it by the number of units contained in the case.')
    edi_case_price = fields.Float(string='Selling Price (Cases)',
                                digits='Product Price',
                                compute='_compute_selling_price_cases',
                                help='Gross Selling Price in Cases')
    edi_qty_cases = fields.Float(string='Quantity (Cases)',
                               compute='_compute_quantity_edi',
                               help='Quantity ordered in Cases. Change the UoM from Units to Cases if you want the case size to be taken into account in the computation.')
    edi_charges_allowance_ids = fields.Text(string='Charges Allowances',
                                       help='Charges Allowances from EDI at Header and LineItem level.')
    edi_payment_terms = fields.Text(string='Payment Terms',
                                  help='Payment Terms from EDI at Header and LineItem level.')
    edi_tax_code = fields.Selection(selection=[
                                    ('GS', 'Goods and Services[GST]'),
                                    ('ST', 'State/Provincial Sales'),
                                    ('TX', 'All Taxes'),
                                    ('BE', 'Harmonized Sales[HST]'),
                                    ('PG', 'state/Provincial Goods')
                                ], string='Tax Code',
                                help='For EDI purposes. Identification of the type of duty, tax, or fee applicable to commodities or of tax applicable to services.')
    edi_tax_percent = fields.Float(string='Tax Percent', help='Tax percent passed from the EDI.')
    edi_tax_id = fields.Float(string='Tax ID EDI', help='Tax ID from the EDI at line item level')
    edi_item_status_code = fields.Selection(selection=[
                                    ('IA', 'Accept'),
                                    ('IB', 'Backordered'),
                                    ('IP', 'Accept - Price Changed'),
                                    ('IQ', 'Accept - Quantity Changed')
                                ], string='Item Status Code',
                                default='IA',
                                help='For EDI purposes. Code defining the vendor\'s status of the item.')
    edi_uom = fields.Char(string='UOM Code Recieved from EDI', help='UOM Code Recieved from EDI', store=True)

    @api.depends('edi_price', 'product_packaging_id', 'product_uom')
    def _compute_unit_price(self):
        for line in self:
            if line.product_packaging_id and line.product_uom.name == 'Cases' and line.product_packaging_id.qty:
                line.edi_unit_price = line.edi_price / line.product_packaging_id.qty
            else:
                line.edi_unit_price = line.edi_price

    @api.depends('product_uom_qty', 'product_packaging_id', 'product_uom')
    def _compute_quantity_edi(self):
        for line in self:
            if line.product_packaging_id and line.product_uom.name == 'Cases' and line.product_packaging_id.qty:
                line.edi_qty_cases = line.product_uom_qty / line.product_packaging_id.qty
            elif line.edi_pack_size:
                line.edi_qty_cases = line.product_uom_qty / line.edi_pack_size
            else:
                line.edi_qty_cases = line.product_uom_qty

    @api.depends('price_unit', 'order_id.partner_id', 'product_packaging_id', 'product_uom')
    def _compute_selling_price_cases(self):
        for line in self:
            if line.product_packaging_id and line.product_uom.name == 'Cases' and line.product_packaging_id.qty:
                line.edi_case_price = line.price_unit * line.product_packaging_id.qty
            else:
                line.edi_case_price = line.price_unit

    @api.model
    def get_payment_terms(self, payment_terms_node, additional_fields, nsmap=None):
        if not payment_terms_node:
            return ''
        terms_type = self.default_text(payment_terms_node.find('TermsType', namespaces=nsmap))
        basis_date_code = self.default_text(payment_terms_node.find('TermsBasisDateCode', namespaces=nsmap))
        discount_percentage = self.default_text(payment_terms_node.find('TermsDiscountPercentage', namespaces=nsmap))
        discount_date = self.default_text(payment_terms_node.find('TermsDiscountDate', namespaces=nsmap))
        discount_due_days = self.default_text(payment_terms_node.find('TermsDiscountDueDays', namespaces=nsmap))
        net_due_date = self.default_text(payment_terms_node.find('TermsNetDueDate', namespaces=nsmap))
        net_due_days = self.default_text(payment_terms_node.find('TermsNetDueDays', namespaces=nsmap))
        terms_description = self.default_text(payment_terms_node.find('TermsDescription', namespaces=nsmap))

        customer_payment_terms = 'Terms Type: %s\nBasis Date Code: %s\nDiscount Percentage: %s\nDiscount Date: %s\nDiscount Due Days: %s\nNet Due Date: %s\nNet Due Days: %s\nTerms Description: %s\n' \
            % (terms_type, basis_date_code, discount_percentage, discount_date, discount_due_days, net_due_date,
               net_due_days, terms_description)

        return customer_payment_terms
