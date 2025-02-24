# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
import logging
from odoo.exceptions import UserError
_logger = logging.getLogger("Warehouse Stock Inventory")


class ProductCategory(models.Model):
    _inherit = "product.category"

    is_used_on_report = fields.Boolean(string="Is Used On Daily Report?")
    daily_cost = fields.Float("Daily Cost", digits=(16, 4))


class ProductProduct(models.Model):
    _inherit = "product.product"

    def open_daily_report_action(self):
        warehouse_id = self._context.get('default_warehouse_id')
        categ_id = self._context.get('default_categ_id')
        report_date = self._context.get('report_date')
        report_line = False
        if warehouse_id and categ_id and report_date:
            report_line = self.env['warehouse.stock.inventory.line'].search(
                [('stock_report_id.report_date', '=', report_date), ('category_id', '=', categ_id),
                 ('warehouse_id', '=', warehouse_id)])
        if not report_line:
            raise UserError(_("Unable to found report data!"))

        if len(report_line) != 1:
            raise UserError(_("Found multiple data for same filter!"))

        action = self.env['ir.actions.act_window']._for_xml_id(
            'warehouse_inventory_report.action_warehouse_stock_inventory_line_view')
        action['res_id'] = report_line.id
        return action
