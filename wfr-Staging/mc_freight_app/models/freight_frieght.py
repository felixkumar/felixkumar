# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import ValidationError,UserError

class FreightStages(models.Model):
    _name = 'freight.stage'
    _description = 'Stages for Freight in shipment and delivers'
    _order = 'sequence'

    is_fold = fields.Boolean(string="Folded in Pipeline", )
    name = fields.Char(string="Name", )
    sequence = fields.Integer(string="Sequence", )
    is_shipment_confirmation = fields.Boolean(string="Is Shipment Confirmation Stage?")

class FreightStagesOut(models.Model):
    _name = 'freight.outbound.stage'
    _description = 'Stages for Freight in shipment and delivers'
    _order = 'sequence'

    is_fold = fields.Boolean(string="Folded in Pipeline", )
    name = fields.Char(string="Name", )
    sequence = fields.Integer(string="Sequence", )
    is_shipment_confirmation = fields.Boolean(string="Is Shipment Confirmation Stage?")


class FreightPort(models.Model):
    _name = 'freight.port'
    _description = 'Ports for shipment and delivers'

    name = fields.Char(string="Name")
    country_id = fields.Many2one('res.country', string="Country")
    land = fields.Boolean(string="Land")
    ocean = fields.Boolean(string="Ocean")
    air = fields.Boolean(string="Air")
    code = fields.Char(string="Code")
    active = fields.Boolean(string="Active", default=True)
    state_id = fields.Many2one('res.country.state', string="State")


class FreightTransport(models.Model):
    _name = 'freight.transport'
    _description = 'Transports for shipment and delivers'

    name = fields.Char(string="Name", )


class FreightImport(models.Model):
    _name = 'freight.import'
    _description = 'Imports for shipment and delivers'

    name = fields.Char(string="Name")


class FreightRoutes(models.Model):
    _name = 'freight.routes'
    _description = 'Routes for shipment and delivers'

    route_operation = fields.Char(string="Name")
    source_location = fields.Many2one('freight.port', string="Source Location")
    destination_location = fields.Many2one('freight.port', string="Destination Location")
    transportation = fields.Selection([('air', 'Air'),
                                       ('water', 'Water'),
                                       ('other', 'Water')], string="Transport")
    freight_transport_id = fields.Many2one("freight.transport", string="Transport", ondelete='cascade')
    cost = fields.Float(string="Cost")
    sale = fields.Float(string="Sale")
    freight_id = fields.Many2one('freight.freight', string="Freight Id")


class FreightOrderLine(models.Model):
    _name = 'freight.order.line'
    _description = 'Order line for Transit'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    goods = fields.Many2one("product.product", string="Parts")
    gross_weight = fields.Float(string="Gross Weight")
    net_weight = fields.Float(string="Net Weight")
    box_quantity = fields.Integer(string="Box Quantity")
    num_box = fields.Integer(string="Number Of Boxes")
    value = fields.Float(string="Total Cost")
    base_cost = fields.Float(string="Cost")
    base_sale_price = fields.Float(string="Sale Price")
    sale_price = fields.Float(string="Total Sale Price")
    total_quantity = fields.Integer(string="Total Qty", tracking=True)
    container_id = fields.Many2one('container.container', string="Container Id", copy=False)
    freight_id = fields.Many2one('freight.freight', invisible=True)
    total_kg = fields.Float(string="Net Weight", invisible=True)
    is_outbound = fields.Boolean(string="Is Outbound", related='freight_id.is_outbound')
    volume_by_ft = fields.Float(string="Volume (Ft)", store=True)

    @api.onchange('goods', 'total_quantity', 'base_cost')
    def total_value(self):
        if self.goods and self.total_quantity:
            self.value = self.base_cost * self.total_quantity
            self.sale_price = self.goods.lst_price * self.total_quantity
            self.volume_by_ft = self.goods.volume * self.total_quantity

    @api.onchange('box_quantity', 'num_box')
    def cal_total_quantity(self):
        if self.box_quantity and self.num_box:
            self.total_quantity = self.box_quantity * self.num_box

    @api.onchange('goods', 'total_quantity')
    def set_gross_weight(self):
        goods = self.goods
        if goods and self.total_quantity:
            self.gross_weight = goods.weight
            uom_name = goods.weight_uom_name
            if uom_name == 'kg':
                self.total_kg = goods.weight * self.total_quantity
                self.net_weight = (goods.weight * 2.20462) * self.total_quantity
            else:
                self.total_kg = (goods.weight * 0.453592) * self.total_quantity
                self.net_weight = goods.weight * self.total_quantity

    def write(self, vals):
        if vals.get('total_quantity'):
            display_msg = "Freight Order Line" + \
                          '<br>' + "Total QTY : " + str(self.total_quantity)
            res = super(FreightOrderLine, self).write(vals)
            display_msg += " <span class='fa fa-long-arrow-right'/> " + str(self.total_quantity)
            self.env['mail.message'].create({
                'body': display_msg,
                'model': 'freight.freight',
                'res_id': self.freight_id.id,
                'subtype_id': '2',
            })
            return res
        else:
            return super(FreightOrderLine, self).write(vals)


class FreightTracking(models.Model):
    _name = 'freight.tracking'
    _description = 'Tracking for Transit'

    location_id = fields.Many2one("freight.port", string="Location")
    description = fields.Char(string="Description")
    Date = fields.Date(string="Date")
    freight_id = fields.Many2one('freight.freight', string="Freight Id")


class FreightFreight(models.Model):
    _name = 'freight.freight'
    _description = 'Transit for shipment and deliveries'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(string="Shipment", copy=False)
    voyage_no = fields.Char(string="House BOL (HBL)", )
    vessel = fields.Char(string="Container Number")
    # land_shipping = fields.Char(string="Land Shipping")
    description = fields.Char(string="Shipment Description")
    date_order = fields.Datetime(string="Date of Pick-up")
    stuffing_date = fields.Date(string="Stuffing Date")
    date_shipping = fields.Date(string="Sail Date")
    date_landing = fields.Date(string="Actual Port Arrival Date")
    operation_payment = fields.Float(string="Operation Payment", )
    price_per_pound = fields.Float(string="Cost Per Lb")
    # partner_id = fields.Many2many("res.partner", copy=False, relation="res_partner_partner_id")
    partner_id = fields.Many2one("res.partner", copy=False, string="Customer / Consignee")
    outbound_partner_id = fields.Many2one("res.partner", string="Ship To")
    signature = fields.Char("Signature")
    consignee_id = fields.Many2one("res.partner", string="In Care Of",
                                   default=lambda self: self.env.company.partner_id.id)
    forwarder_id = fields.Many2one("res.partner", string="Freight Forwarder", )
    agent_id = fields.Many2one("res.partner", string="Customs Agent", )
    port_shipping_id = fields.Many2one("freight.port", string="Shipping Port", )
    port_discharge_id = fields.Many2one("freight.port", string="Discharging Port", )
    port_loading_id = fields.Many2one("freight.port", string="Loading Port", )
    transport_id = fields.Selection([('air', 'Air'),
                                     ('water', 'Water'),
                                     ('other', 'Other')], string="Transport")
    freight_transport_id = fields.Many2one("freight.transport", string="Transport", ondelete='cascade')
    # import_id = fields.Many2many('res.partner', copy=False, relation="res_partner_import_id", string="Supplier")
    import_id = fields.Many2one('res.partner', copy=False, string="SUPPLIER")
    stage_id = fields.Many2one("freight.stage", string="Inbound", group_expand='_read_group_stage_ids')
    delivery_status = fields.Selection(string="Delivery Status",
                                       selection=[('received', 'Received')])
    supplier_id = fields.Many2one("res.partner", string="Supplier", )
    freight_routes_ids = fields.One2many('freight.routes', 'freight_id', string="Routes")
    freight_tracking_ids = fields.One2many('freight.tracking', 'freight_id', string="Tracking")
    other_info = fields.Text(string="Other Information")
    notes = fields.Text(string="Notes")
    document_upload = fields.Binary(string="Document")
    document_file = fields.Char(string="Document File")
    container_line_ids = fields.One2many('container.container', 'freight_id', 'Containers', copy=False)
    freight_order_line_ids = fields.One2many('freight.order.line', 'freight_id', string="Supplier")
    # purchase_orders_ids = fields.Many2many('purchase.order', 'freight_po_rel', 'freight_id', 'order_id',
    #                                        string='Purchase Orders')
    purchase_orders_ids = fields.Many2one('purchase.order', string='Purchase Orders')
    # product_id = fields.Many2many('product.product', string="Product")
    cost = fields.Char(string="Cost")
    initial_freight_charge = fields.Float(string="Initial Freight Charges")
    final_freight_charge = fields.Float(string="Final Freight Charges")
    freight_invoice = fields.Many2one('ir.attachment', string="Freight Quote/Invoice")
    estimated_arrival_date = fields.Date(string="Estimated Port Arrival Date")
    user_id = fields.Many2one('res.users', string="Responsible")
    commercial_invoice = fields.Binary(string="Commercial Invoice")
    commercial_invoice_file = fields.Char(string="Commercial Invoice File")
    commercial_packing_list = fields.Binary(string="Commercial Packing List")
    commercial_packing_list_file = fields.Char(string="Commercial Packing List File")
    price_per_kg = fields.Float(string="Cost Per Kg")
    sku_names = fields.Char("SKU", compute="_compute_sku_names")
    sku_total_qty = fields.Char("TOTAL QTY", compute="_compute_sku_total_qty")
    sku_total_number_of_pallets = fields.Char("# OF PALLETS", compute="_compute_sku_total_number_of_pallets")
    is_outbound = fields.Boolean(string="Is Outbound", copy=False)
    outbound_stage_id = fields.Many2one("freight.outbound.stage", string="Outbound", group_expand='_read_group_stage_ids', copy=False, tracking=True)
    reference = fields.Char(string="Reference", required=False, copy=False)
    carrier_flight = fields.Many2one("res.partner", string="Carrier", tracking=True)
    bol_number = fields.Char(string="BOL #")
    # seal_number = fields.Integer(string="Seal Number")
    weight = fields.Float(string="Weight", digits=(16, 2))
    is_shipped = fields.Boolean(string="Is Shipped?", default=False, copy=False)
    is_master = fields.Boolean(string="Master Record", default=False, copy=False)
    color = fields.Integer(string="Color", required=False, copy=False)
    is_outbound_color = fields.Integer(string="is_outbound_color", required=False, copy=False, compute="_compute_is_oubound_color")
    seal_number_inbound = fields.Char("Seal #", tracking=True)
    # departure_date = fields.Datetime(string="Departure Date")
    # bol_date = fields.Date(string="BOL Date")
    ibl_remarks = fields.Many2one('freight.remarks.ibl', string="Remarks")
    obl_remarks = fields.Many2one('freight.remarks.obl', string="Remarks")
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", tracking=True)

    weight_kg = fields.Float(string="Weight (kg)", compute="_compute_weight_volume", store=True)

    volume_cuft = fields.Float(string="Volume (Cu Ft)", compute="_compute_weight_volume", store=True)
    volume_cbm = fields.Float(string="Volume (CBM)", compute="_compute_weight_volume", store=True)

    cost_per_cuft = fields.Float(string="Cost per Cu Ft", compute="_compute_weight_volume", store=True)
    cost_per_cbm = fields.Float(string="Cost per CBM", compute="_compute_weight_volume", store=True)

    # def unlink(self):
    #     if self.env.user.has_group('base.group_system'):
    #         return super(FreightFreight, self).unlink()
    #     else:
    #         raise UserError("Sorry, You can't delete this Record.")

    @api.onchange('reference','partner_id','import_id')
    def onchange_reference(self):
        for res in self:
            if res.partner_id or res.import_id:
                vendor_identifier = res.partner_id and res.partner_id.vendor_identifier
                if not res.is_outbound:
                    vendor_identifier = res.import_id and res.import_id.vendor_identifier or ''
                if not vendor_identifier:
                    res.name = "{}".format(res.reference)
                else:
                    res.name = "{}-{}".format(vendor_identifier, res.reference)

    def write(self, vals):
        if vals.get('is_master'):
            vals['color'] = 7
        elif 'is_master' in vals.keys():
            vals['color'] = 0
        res = super(FreightFreight, self).write(vals)
        return res

    def _compute_is_oubound_color(self):
        for rec in self:
            if rec.is_outbound:
                rec.is_outbound_color = 10
            else:
                rec.is_outbound_color = 1

    @api.model
    def default_get(self, fields):
        is_outbound = self.env.context.get('is_outbound')
        vals = super(FreightFreight, self).default_get(fields)
        vals['is_outbound'] = is_outbound
        return vals

    @api.depends('sku_names')
    def _compute_sku_names(self):
        for record in self:
            goods = record.freight_order_line_ids.mapped('goods').filtered(lambda p: p.default_code).mapped('default_code')
            record.sku_names = goods and " | ".join(goods) or ""

    @api.onchange('freight_order_line_ids')
    def _compute_sku_total_qty(self):
        for rec in self:
            total_qty = rec.freight_order_line_ids.mapped('total_quantity')
            rec.sku_total_qty = total_qty and int(sum(total_qty)) or ""

    @api.onchange('freight_order_line_ids')
    def _compute_sku_total_number_of_pallets(self):
        for rec in self:
            pallets = rec.freight_order_line_ids.mapped('required_pallet')
            rec.sku_total_number_of_pallets = pallets and int(sum(pallets)) or ""

    @api.onchange('purchase_orders_ids')
    def onchange_product_cost(self):
        total = 0
        for rec in self.purchase_orders_ids:
            if rec:
                total += rec.amount_total
        self.cost = total

    @api.onchange('date_shipping', 'date_order')
    def onchange_date_shipping(self):
        for rec in self:
            if rec.is_outbound:
                rec.outbound_stage_id = self.env.ref('mc_freight_app.scheduled_outbound').id


    def create_po_lines(self):
        for order in self.purchase_orders_ids:
            if order:
                for rec in order.order_line:
                    freight_line = self.freight_order_line_ids.create({
                        'goods': rec.product_id.id,
                        'freight_id': self.id,
                        'value': rec.price_unit,
                        'total_quantity': rec.product_qty,
                        'sale_price': rec.product_id.lst_price,
                    })
                    if rec.product_id.standard_price == 0.00:
                        freight_line.base_cost = rec.price_unit
                    else:
                        freight_line.base_cost = rec.product_id.standard_price
                for lines in self.freight_order_line_ids:
                    lines.set_gross_weight()
                    lines.total_value()

    # @api.depends('weight_kg')
    # def sum_price_per_kg(self):
    #     for r in self:
    #         price_per_kg = 0.0
    #         if r.weight_kg and r.initial_freight_charge:
    #             r.price_per_kg = r.initial_freight_charge / r.weight_kg
    #         else:
    #             r.price_per_kg = price_per_kg

    # @api.depends('weight')
    # def sum_price_per_pound(self):
    #     for r in self:
    #         price_per_kg = 0.0
    #         if r.weight and r.initial_freight_charge:
    #             r.price_per_pound = r.initial_freight_charge / r.weight
    #         else:
    #             r.price_per_pound = price_per_kg

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """
        retrieve team_id from the context and write the domain
        ('id', 'in', stages.ids): add columns that should be present
        """
        stage_ids = stages._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    # @api.constrains('name')
    # def _check_record_name(self):
    #     freight_rec = self.env['freight.freight'].search([('name', '=', self.name), ('active', 'in', [False, True])])
    #     if freight_rec.__len__() > 1:
    #         raise UserError(_('Record already exists with this name'))

    @api.model
    def create(self, vals):
        """
        Inherited Created method to prepare the name of the shipment using the sequence
        :param vals: type dict, values for creating the record for shipment
        :return: Object of created record
        """
        if self._context.get('uid', False):
            vals.update({'user_id': self._context.get('uid', False)})

        if vals.get('is_master'):
            vals['color'] = 7

        res = super(FreightFreight, self).create(vals)
        oxford_company_id = self.env['res.company'].sudo().search([('name', 'like', 'Oxford')], limit=1)
        if res.warehouse_id.company_id:
            name = self.env['ir.sequence'].with_company(res.warehouse_id.company_id).next_by_code('freight.freight.sequence')
        else:
            name = self.env['ir.sequence'].next_by_code('freight.freight.sequence')
        vendor_identifier = res.import_id and res.import_id.vendor_identifier or res.partner_id.vendor_identifier or ''
        if res.is_outbound:
            vendor_identifier = res.partner_id and res.partner_id.vendor_identifier
            if not vendor_identifier and not res.reference:
                if res.warehouse_id.company_id.is_oxford:
                    res.name = "SHIP/{}".format(name)
                elif self.env.company.is_oxford:
                    res.name = "OXF-{}".format(self._context.get('so_number'))
                elif res.warehouse_id and not res.warehouse_id.company_id.is_oxford:
                    res.name = "SHIP00000{}".format(name.split('P')[-1].lstrip('0'))
                else:
                    res.name = "SHIP00000{}".format(name.split('P')[-1].lstrip('0'))
            elif not vendor_identifier:
                res.name = "{}".format(res.reference or "")
            else:
                res.name = "{}-{}".format(vendor_identifier, res.reference)
            res.outbound_stage_id = self.env.ref('mc_freight_app.dock_audit_approved_outbound').id
        elif vendor_identifier:
            if self.env.company.is_oxford and self.env.company.id == oxford_company_id.id:
                res.name = "OXF-{}-{}".format(vendor_identifier, res.reference or name or "")
            else:
                res.name = "{}-{}".format(vendor_identifier, res.reference or name or "")
            res.stage_id = self.env.ref('mc_freight_app.dock_audit_approved').id
        else:
            if not res.reference:
                if self.env.company.is_oxford:
                    po_number = False
                    if self._context.get('po_number'):
                        po_number = self._context.get('po_number').split('OXF')[-1]
                    res.name = "OXF{}".format(po_number or '-',name)
                elif res.warehouse_id and not res.warehouse_id.company_id.is_oxford:
                    res.name = "SHIP00000{}".format(name.split('P')[-1].lstrip('0'))
                else:
                    res.name = "SHIP00000{}".format(name.split('P')[-1].lstrip('0'))
            else:
                if self.env.company.is_oxford:
                    res.name = "OXF-{}".format(res.reference)
                else:
                    res.name = "{}".format(res.reference)
            res.stage_id = self.env.ref('mc_freight_app.dock_audit_approved').id

        # if self.env.company.company_code == 'WFL':
        #     bol_number = self.env['ir.sequence'].next_by_code('sequ.bol.wfl')
        #     res['bol_number'] = bol_number
        # elif self.env.company.company_code == 'WFS':
        #     bol_number = self.env['ir.sequence'].next_by_code('sequ.bol.wfs')
        #     res['bol_number'] = bol_number

        return res


class ContainerContainer(models.Model):
    _name = 'container.container'
    _description = 'Container For the Transit'

    freight_id = fields.Many2one('freight.freight', invisible=True)
    name = fields.Many2one('res.partner', string='Supplier Name')
    container_size = fields.Char('Lot Number')
    gross_weight = fields.Char('Gross Weight')
    container_no = fields.Char(string="Container #")
    seal_no = fields.Char(string="Seal #", required=False, )

    @api.model
    def create(self, vals):
        res = super(ContainerContainer, self).create(vals)
        res.seal_no = res.freight_id.seal_number_inbound
        if not self._context.get('is_done_record') and res.freight_id.is_master:
            copied_record = res.freight_id.with_context(is_done_record=True).copy()
            copied_record.reference = vals.get('container_no')
            copied_record.onchange_reference()
            res.freight_id.write({"inbound_logistics_id": [(4, copied_record.id, 0)]})
        return res

class FreightRemarks(models.Model):
    _name = 'freight.remarks.ibl'
    _description = 'Remarks For the logistic Records'

    name = fields.Char(string="Name")

class FreightRemarksOBL(models.Model):
    _name = 'freight.remarks.obl'
    _description = 'OBL Remarks For the logistic Records'

    name = fields.Char(string="Name")