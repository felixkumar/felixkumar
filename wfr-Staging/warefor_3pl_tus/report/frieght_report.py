# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo import tools


class FreightReport(models.Model):
    """ CRM Lead Analysis """

    _name = 'freight.report'
    _auto = False
    _description = "Freight Report"

    id = fields.Integer("Id")
    name = fields.Char("Name")
    reference = fields.Char("Reference")
    date_order = fields.Datetime(string="Date")
    arrival_at_warefor = fields.Datetime(string="Arrival @ Warefor")
    transfers_count = fields.Integer(string='Transfers Count')
    goods = fields.Many2one("product.product", string="Product")
    gross_weight = fields.Float(string="Gross Weight")
    net_weight = fields.Float(string="Net Weight")
    box_quantity = fields.Integer(string="Box Quantity")
    num_box = fields.Integer(string="Number Of Boxes")
    value = fields.Float(string="Total Cost")
    base_cost = fields.Float(string="Cost")
    base_sale_price = fields.Float(string="Sale Price")
    sale_price = fields.Float(string="Total Sale Price")
    total_quantity = fields.Integer(string="Total Qty")
    container_id = fields.Many2one('container.container', string="Container Id")
    freight_id = fields.Many2one('freight.freight', 'Logistic Record')
    total_kg = fields.Float(string="Net Weight")
    is_outbound = fields.Boolean(string="Is Outbound")
    active = fields.Boolean(string="Active")

    def _select(self):
        return """
            SELECT
                l.id,
                m.name,
                m.reference,
                m.date_order,
                m.arrival_at_warefor,
                m.transfers_count,
                l.goods,
                l.gross_weight,
                l.net_weight,
                l.box_quantity,
                l.num_box,
                l.value,
                l.base_cost,
                l.base_sale_price,
                l.sale_price,
                l.total_quantity,
                l.container_id,
                l.freight_id,
                l.total_kg,
                m.is_outbound,
                m.active
        """

    def _from(self):
        return """
            FROM freight_order_line AS l
        """

    def _join(self):
        return """
            JOIN freight_freight AS m ON l.freight_id = m.id
        """

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(), self._join()))
