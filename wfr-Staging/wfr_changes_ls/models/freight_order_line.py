from odoo import fields, models, api


class FreightOrderLineInherit(models.Model):
    _inherit = 'freight.order.line'

    freight_stage_id = fields.Many2one(comodel_name="freight.stage", string="Freight Stage",
                                       related="freight_id.stage_id", store=True)
    freight_etd = fields.Date(string="ETD", related="freight_id.shipping_info_etd", store=True)
    freight_sail = fields.Date(string="Departure Date", related="freight_id.date_shipping", store=True)
    freight_eta_entry = fields.Date(string="ETA", related="freight_id.estimated_arrival_date", store=True)
    freight_port_arrival = fields.Date(string="Arrival Date", related="freight_id.date_landing", store=True)
    freight_eta_warehouse = fields.Datetime(string="DC ETA", related="freight_id.pickup_schedule_date", store=True)
    freight_available = fields.Date(string="Available to Order", related="freight_id.available_to_order", store=True)

    freight_po_date = fields.Date(string="PO Date", related="freight_id.po_date", store=True)
    freight_plan_expected_completion_date = fields.Datetime(string="PO-ECD",
                                                            related="freight_id.plan_expected_completion_date",
                                                            store=True)
    freight_plan_actual_completion_date = fields.Datetime(string="PO-ACD",
                                                          related="freight_id.plan_actual_completion_date", store=True)
    freight_vessel = fields.Char(string="Container #", related="freight_id.vessel", store=True)
    freight_stuffing_date = fields.Date(string="Loading Date", related="freight_id.stuffing_date", store=True)
    freight_vessel_name = fields.Char(string="Vessel Name", related="freight_id.vessel_name", store=True)
    freight_vessel_voyage = fields.Char(string="Voyage #", related="freight_id.vessel_voyage", store=True)
    freight_port_shipping_id = fields.Many2one(comodel_name="freight.port", string="Port of Export",
                                               related="freight_id.port_shipping_id", store=True)
    freight_port_discharge_id = fields.Many2one(comodel_name="freight.port", string="Port of Entry",
                                                related="freight_id.port_discharge_id", store=True)

    product_volume_per_item = fields.Float(string="Volume Per Item", related="goods.volume")
    product_volume_per_case = fields.Float(string="Volume Per Case", related="goods.volume")
    product_items_per_case = fields.Text(string="Items Per Case", related="goods.units_per_case")
    product_length = fields.Float(string="Case Length", related="goods.product_length")
    product_width = fields.Float(string="Case Width", related="goods.product_width")
    product_height = fields.Float(string="Case Height", related="goods.product_height")

    product_customer_item_number = fields.Char(string="Customer Item Number", related="goods.item_customer_number",
                                               store=True)
    product_category_id = fields.Many2one(comodel_name="product.category", related="goods.categ_id", store=True)
    product_partner_id = fields.Many2one(comodel_name="res.partner", related="freight_id.partner_id", store=True)

    product_description = fields.Char(related="goods.name", string="Product Description", store=True)
    goods = fields.Many2one("product.product", string="Item #")
    total_quantity = fields.Integer(string="Quantity", tracking=True)
    freight_id = fields.Many2one('freight.freight', invisible=True, string="Record Reference")

    @api.depends('total_quantity', 'goods.volume')
    def _compute_product_volume(self):
        for rec in self:
            rec.product_volume = rec.qty_carton * rec.goods.volume
