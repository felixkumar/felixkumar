# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
import io
import pandas as pd
from datetime import datetime, timedelta
import pytz

from odoo import _, api, fields, models
import logging

_logger = logging.getLogger("Warehouse Stock Inventory")


class WarehouseInventoryStock(models.Model):
    _name = "warehouse.stock.inventory"
    _description = "Warehouse Inventory"
    _order = "report_date desc, id desc"
    _rec_name = 'report_date'

    report_date = fields.Date('Report Date', default=fields.Date.today, readonly=True)
    report_line_ids = fields.One2many("warehouse.stock.inventory.line", "stock_report_id", string="Warehouse Lines")

    def _generate_warehouse_report(self):
        _logger.info("******* STARTED REPORT GENERATION PROCESS *********")
        # Step 1: Fetch product and stock data by warehouse
        report_line_obj = self.env['warehouse.stock.inventory.line']
        logistic_company = self.env['res.company'].sudo().search([('is_logistics', '=', True)])
        # car_company = self.env['res.company'].sudo().search([('company_code', '=', 'CAR')])

        # OLD
        # products = self.env['product.product'].search([('company_ids', 'in', car_company.ids)])

        # NEW
        warehouses = self.env['stock.warehouse'].sudo().search([('is_use_on_report', '=', True)])
        categ_ids = self.env['product.category'].search([('is_used_on_report', '=', True)])

        self = self.with_company(logistic_company).sudo()

        current_datetime_utc = self._context.get('from_wizard_date')
        if not current_datetime_utc:
            current_time = datetime.now().astimezone(pytz.timezone(self.env.user.tz))
            if not (1 <= current_time.hour < 3):
                _logger.info("Warehouse Daily Report cron cannot be run during work hours")
                return True
            current_datetime_utc = fields.Date.today() - timedelta(days=1)
            user_timezone = pytz.timezone(self.env.user.tz)
            utc_timezone = pytz.timezone('UTC')
            s_date_min = datetime.combine(current_datetime_utc, datetime.min.time())
            s_date_max = datetime.combine(current_datetime_utc, datetime.max.time())
            date_min = user_timezone.localize(s_date_min)
            date_max = user_timezone.localize(s_date_max)
            # Convert the localized Asia/Kolkata time to UTC
            from_date = date_min.astimezone(utc_timezone)
            to_date = date_max.astimezone(utc_timezone)
        else:
            user_timezone = pytz.timezone(self.env.user.tz)
            utc_timezone = pytz.timezone('UTC')
            s_date_min = datetime.combine(current_datetime_utc, datetime.min.time())
            s_date_max = datetime.combine(current_datetime_utc, datetime.max.time())
            date_min = user_timezone.localize(s_date_min)
            date_max = user_timezone.localize(s_date_max)
            # Convert the localized Asia/Kolkata time to UTC
            from_date = date_min.astimezone(utc_timezone)
            to_date = date_max.astimezone(utc_timezone)

        report_id = self.env['warehouse.stock.inventory'].search([('report_date', '=', from_date)])
        if not report_id:
            report_id = self.env['warehouse.stock.inventory'].create({'report_date': from_date})
        for categ_id in categ_ids:
            daily_cost = categ_id.daily_cost or 0.02
            _logger.info("******* CATEGORY {} *********".format(categ_id.name))
            for warehouse in warehouses:
                _logger.info("******* WAREHOUSE {} *********".format(warehouse.name))
                total_free_to_use_qty = 0
                total_volume_qbft = 0
                total_daily_fee = 0
                warehouse_data = []
                temp_p_ids = report_id.report_line_ids.line_report_ids.product_id
                if temp_p_ids:
                    products = self.env['product.product'].search(
                        [('categ_id', '=', categ_id.id), ('id', 'not in', temp_p_ids.ids)], limit=20, order='id asc')
                else:
                    products = self.env['product.product'].search([('categ_id', '=', categ_id.id)], limit=20, order='id desc')
                for product in products:
                    # if not self._context.get('from_wizard_date'):
                    #     move_ids = self.env['stock.move.line'].search([('date', '>=', from_date), ('date', '<=', to_date),
                    #                                                   ('state', '=', 'done'), ('product_id', '=', product.id),
                    #                                                   ('company_id.is_logistics', '=', True)])
                    #     outgoing_move_ids = move_ids.filtered(lambda m: m.picking_id.picking_type_id.code == 'outgoing' and m.location_id.warehouse_id.id == warehouse.id)
                    #     incoming_move_ids = move_ids.filtered(lambda m: m.picking_id.picking_type_id.code == 'incoming' and m.location_dest_id.warehouse_id.id == warehouse.id)
                    #     adjust_i_move_ids = move_ids.filtered(lambda m: m.location_dest_usage == 'internal' and m.location_usage == 'inventory' and m.location_dest_id.warehouse_id.id == warehouse.id)
                    #     adjust_o_move_ids = move_ids.filtered(lambda m: m.location_usage == 'internal' and m.location_dest_usage == 'inventory' and m.location_id.warehouse_id.id == warehouse.id)
                    #     outgoing_qty = sum(outgoing_move_ids.mapped('qty_done'))
                    #     incoming_qty = sum(incoming_move_ids.mapped('qty_done'))
                    #     outgoing_qty += sum(adjust_o_move_ids.mapped('qty_done'))
                    #     incoming_qty += sum(adjust_i_move_ids.mapped('qty_done'))
                    #     qty_on_hand = self.env['stock.quant']._get_available_quantity(product, warehouse.lot_stock_id)
                    # elif self._context.get('from_wizard_date'):
                    _logger.info("Product Code - {}".format(product.default_code))
                    move_ids = self.env['stock.move.line'].search(
                        [('date', '<', from_date),
                         ('state', '=', 'done'), ('product_id', '=', product.id),
                         ('company_id.is_logistics', '=', True)])
                    o_o_move_ids = move_ids.filtered(lambda m: m.picking_id.picking_type_id.code == 'outgoing' and m.location_id.warehouse_id.id == warehouse.id)
                    o_i_move_ids = move_ids.filtered(lambda m: m.picking_id.picking_type_id.code == 'incoming' and m.location_dest_id.warehouse_id.id == warehouse.id)
                    adjust_i_move_ids = move_ids.filtered(lambda m: m.location_dest_usage == 'internal' and m.location_usage == 'inventory' and m.location_dest_id.warehouse_id.id == warehouse.id)
                    adjust_o_move_ids = move_ids.filtered(lambda m: m.location_usage == 'internal' and m.location_dest_usage == 'inventory' and m.location_id.warehouse_id.id == warehouse.id)

                    moved_lines_stock_in = move_ids.filtered(lambda
                                                                 m: m.location_usage == 'internal' and m.location_dest_usage == 'internal' and m.location_id.warehouse_id.id != warehouse.id and m.location_dest_id.warehouse_id.id == warehouse.id)

                    # declare outgoing_qty and incoming_qty vairables


                    o_outgoing_qty = sum(o_o_move_ids.mapped('qty_done'))
                    o_incoming_qty = sum(o_i_move_ids.mapped('qty_done'))
                    o_outgoing_qty += sum(adjust_o_move_ids.mapped('qty_done'))
                    o_incoming_qty += sum(moved_lines_stock_in.mapped('qty_done'))
                    o_incoming_qty += sum(adjust_i_move_ids.mapped('qty_done'))
                    qty_on_hand = o_incoming_qty - o_outgoing_qty

                    move_ids_on_date = self.env['stock.move.line'].search(
                        [('date', '>=', from_date), ('date', '<=', to_date),
                         ('state', '=', 'done'), ('product_id', '=', product.id),
                         ('company_id.is_logistics', '=', True)])

                    o_o_move_ids_on_date = move_ids_on_date.filtered(lambda m: m.picking_id.picking_type_id.code == 'outgoing' and m.location_id.warehouse_id.id == warehouse.id)
                    o_i_move_ids_on_date = move_ids_on_date.filtered(lambda m: m.picking_id.picking_type_id.code == 'incoming' and m.location_dest_id.warehouse_id.id == warehouse.id)
                    adjust_i_move_ids_on_date = move_ids_on_date.filtered(lambda m: m.location_dest_usage == 'internal' and m.location_usage == 'inventory' and m.location_dest_id.warehouse_id.id == warehouse.id)
                    adjust_o_move_ids_on_date = move_ids_on_date.filtered(lambda m: m.location_usage == 'internal' and m.location_dest_usage == 'inventory' and m.location_id.warehouse_id.id == warehouse.id)
                    moved_lines_stock_on_date = move_ids_on_date.filtered(lambda m: m.location_usage == 'internal' and m.location_dest_usage == 'internal' and m.location_id.warehouse_id.id != warehouse.id and m.location_dest_id.warehouse_id.id == warehouse.id)

                    outgoing_qty = sum(o_o_move_ids_on_date.mapped('qty_done'))
                    incoming_qty = sum(o_i_move_ids_on_date.mapped('qty_done'))
                    outgoing_qty += sum(adjust_o_move_ids_on_date.mapped('qty_done'))
                    incoming_qty += sum(moved_lines_stock_on_date.mapped('qty_done'))
                    incoming_qty += sum(adjust_i_move_ids_on_date.mapped('qty_done'))

                    if qty_on_hand:
                        volume_qbft = (((qty_on_hand - outgoing_qty + incoming_qty) or 0) / float(product.units_per_case or 1)) * product.volume
                        # Assuming fields are aligned with the required report structure; fetch or calculate each field as necessary
                        total_free_to_use_qty += (qty_on_hand - outgoing_qty + incoming_qty)
                        total_volume_qbft += round(volume_qbft, 2)
                        total_daily_fee += round(volume_qbft * daily_cost, 2)
                        warehouse_data.append({
                            'internal_reference': product.default_code,  # or specify as a string, e.g., 'PROD123'
                            'name': product.name,  # or specify as a string, e.g., 'Sample Product'
                            'product_id': product.id,
                            'product_category': categ_id.id,  # or specify as a string
                            'pallet_count': round(product.pallet_count, 2),  # replace with actual value, e.g., 10.5
                            'uom_id': product.uom_id.id,  # specify the Unit of Measure ID
                            'qty_on_hand': qty_on_hand,  # replace with actual quantity on hand, e.g., 100
                            'incoming_qty': incoming_qty,  # replace with actual incoming quantity, e.g., 20
                            'outgoing_qty': outgoing_qty,  # replace with actual outgoing quantity, e.g., 15
                            'free_to_use_qty': qty_on_hand - outgoing_qty,  # calculation based on above values
                            'forecasted_qty': qty_on_hand - outgoing_qty + incoming_qty,
                            'units_per_case': product.units_per_case or 0,  # replace with units per case, e.g., 6
                            'volume': product.volume,  # replace with product volume, e.g., 1.5
                            'cases_per_carton': product.cases_per_carton or 0,  # replace with cases per carton, e.g., 10
                            'cartons_per_pallet': product.cartons_per_pallet or 1,
                            'pallet_stacking': product.pallet_stacking or 0,  # replace with pallet stacking, e.g., 2
                            'product_per_pallet': product.product_per_pallet or 0,
                            'total_volume_cuft': round(volume_qbft, 2),
                            'daily_fee': round(volume_qbft * daily_cost, 2),  # replace with calculated daily fee, e.g., 0.32
                        })
                    else:
                        warehouse_data.append({
                            'internal_reference': product.default_code,  # or specify as a string, e.g., 'PROD123'
                            'name': product.name,  # or specify as a string, e.g., 'Sample Product'
                            'product_id': product.id,
                            'product_category': categ_id.id,  # or specify as a string
                        })
                report_record = report_id.report_line_ids.filtered(lambda l: l.warehouse_id.id == warehouse.id and l.category_id.id == categ_id.id)
                if report_record and warehouse_data:
                    _logger.info("******* 1 warehouse_data {} *********".format(warehouse_data))
                    # Step 4: Create or update record in this model with the generated report
                    report_record.write({'line_report_ids': [(0, 0, val) for val in warehouse_data]})
                elif warehouse_data:
                    _logger.info("******* 2 warehouse_data {} *********".format(warehouse_data))
                    # Step 4: Create or update record in this model with the generated report
                    report_record = report_line_obj.create({
                        'warehouse_id': warehouse.id,
                        'category_id': categ_id.id,
                        'stock_report_id': report_id.id,
                        'line_report_ids': [(0, 0, val) for val in warehouse_data]
                    })

                if total_free_to_use_qty or total_volume_qbft or total_daily_fee:
                    start_date = from_date.replace(day=1)
                    billing_record = self.env['stock.fee.billing'].search(
                        [('stock_fee_date', '=', start_date)], limit=1)
                    if not billing_record:
                        _logger.info("******* CREATING NEW BILLING RECORD *********")
                        name = "{} - {}".format(start_date.strftime("%B"), start_date.year)
                        billing_record = self.env['stock.fee.billing'].create(
                            {"name": name, "stock_fee_date": start_date})
                    if billing_record:
                        _logger.info("******* CREATING NEW BILLING LINE *********")
                        bill_line_id = self.env['stock.fee.billing.line'].search(
                            [('date', '=', from_date), ('warehouse_id', '=', warehouse.id),
                             ('category_id', '=', categ_id.id), ('stock_fee_billing_id', '=', billing_record.id)],
                            limit=1, order='id desc')
                        if not bill_line_id:
                            data_vals = {
                                "day": from_date.day,
                                "date": from_date,
                                "stock_qty_free_to_use": total_free_to_use_qty,
                                "volume_cuft": total_volume_qbft,
                                "storage_fee": daily_cost,
                                "storage_fee_daily_amount": total_daily_fee,
                                "stock_fee_billing_id": billing_record.id,
                                "warehouse_id": warehouse.id,
                                "category_id": categ_id.id
                            }
                            bill_line_id = self.env['stock.fee.billing.line'].create(data_vals)
                        else:
                            bill_line_id.write({
                                "stock_qty_free_to_use": bill_line_id.stock_qty_free_to_use + total_free_to_use_qty,
                                "volume_cuft": bill_line_id.volume_cuft + total_volume_qbft,
                                "storage_fee": daily_cost,
                                "storage_fee_daily_amount": bill_line_id.storage_fee_daily_amount + total_daily_fee,
                            })
                        if report_record:
                            report_record.stock_fee_billing_line_id = bill_line_id.id
        _logger.info("******* REPORT PROCESS DONE *********")
        return True

    def _update_warehouse_report(self):
        current_datetime_utc = datetime.now()
        # current_datetime_utc = datetime.now() - timedelta(days=10)
        return True
        # Get the user's timezone (default to UTC if not set)
        user_tz = self.env.user.tz or 'America/Chicago'
        timezone = pytz.timezone(user_tz)

        # Convert current datetime to the user's timezone
        current_datetime_user_tz = pytz.utc.localize(current_datetime_utc).astimezone(timezone)

        # Extract the date from the timezone-adjusted datetime
        current_date_user_tz = current_datetime_user_tz.date()
        current_date_user_tz = current_date_user_tz.replace(day=1)

        existing_report_ids = self.search([('report_date', '>=', current_date_user_tz)], order='id asc')

        for report_id in existing_report_ids:
            for w_line in report_id.report_line_ids.filtered(lambda r: r.line_report_ids):
                from_date = datetime.combine(report_id.report_date, datetime.min.time())
                to_date = datetime.combine(report_id.report_date, datetime.max.time())
                total_free_to_use_qty = 0
                total_volume_qbft = 0
                total_daily_fee = 0
                warehouse = w_line.warehouse_id
                for r_line in w_line.line_report_ids:
                    product = r_line.product_id
                    move_ids = self.env['stock.move.line'].search([('date', '>=', from_date), ('date', '<=', to_date),
                                                                  ('state', '=', 'done'), ('product_id', '=', product.id),
                                                                  ('company_id.is_logistics', '=', True)])
                    outgoing_move_ids = move_ids.filtered(lambda
                                                              m: m.picking_type_id.code == 'outgoing' and m.location_id.warehouse_id.id == warehouse.id)
                    incoming_move_ids = move_ids.filtered(lambda
                                                              m: m.picking_type_id.code == 'incoming' and m.location_dest_id.warehouse_id.id == warehouse.id)
                    outgoing_qty = sum(outgoing_move_ids.mapped('qty_done'))
                    incoming_qty = sum(incoming_move_ids.mapped('qty_done'))
                    qty_on_hand = r_line.qty_on_hand
                    if qty_on_hand:
                        volume_qbft = (qty_on_hand - outgoing_qty or 0) / (
                                float(product.units_per_case or 1) * (product.volume or 1))
                        total_free_to_use_qty += (qty_on_hand - outgoing_qty)
                        total_volume_qbft += round(volume_qbft, 2)
                        total_daily_fee += round(volume_qbft * 0.02, 2)
                        vals = {
                            'qty_on_hand': qty_on_hand,  # replace with actual quantity on hand, e.g., 100
                            'incoming_qty': incoming_qty,  # replace with actual incoming quantity, e.g., 20
                            'outgoing_qty': outgoing_qty,  # replace with actual outgoing quantity, e.g., 15
                            'free_to_use_qty': qty_on_hand - outgoing_qty,  # calculation based on above values
                            'forecasted_qty': qty_on_hand - outgoing_qty + incoming_qty,
                            'total_volume_cuft': round(volume_qbft, 2),
                            'daily_fee': round(volume_qbft * 0.02, 2),  # replace with calculated daily fee, e.g., 0.32
                        }
                        r_line.write(vals)
                data_vals = {
                    "stock_qty_free_to_use": total_free_to_use_qty,
                    "volume_cuft": total_volume_qbft,
                    "storage_fee_daily_amount": total_daily_fee,
                }
                w_line.stock_fee_billing_line_id.write(data_vals)
        return True


class WarehouseInventoryStockLine(models.Model):
    _name = "warehouse.stock.inventory.line"
    _description = "Warehouse Inventory Line"
    _rec_name = 'report_filename'

    warehouse_id = fields.Many2one('stock.warehouse', "Warehouse")
    attached_report = fields.Binary("Stock Report")
    report_filename = fields.Char("File Name")
    stock_report_id = fields.Many2one("warehouse.stock.inventory", "Report ID", ondelete='cascade')
    category_id = fields.Many2one("product.category", "Category")
    stock_fee_billing_line_id = fields.Many2one("stock.fee.billing.line", "Fee Billing Line")
    line_report_ids = fields.One2many("warehouse.stock.inventory.line.report", "report_line_id")

    def download_daily_report(self):
        warehouse_data = []
        for line in self.line_report_ids:
            if line.qty_on_hand > 0:
                warehouse_data.append({
                    'Internal Reference': line.internal_reference,
                    'Name': line.name,
                    'Product Category': line.product_category.complete_name,
                    'Pallet Count': line.pallet_count,  # Example field; adjust as needed
                    'Unit of Measure': line.uom_id.name,
                    'Quantity On Hand': line.qty_on_hand,
                    'Incoming': line.incoming_qty,
                    'Outgoing': line.outgoing_qty,
                    'Free To Use Quantity': line.free_to_use_qty,
                    'Forecasted Quantity': line.forecasted_qty,
                    'Units per Case': line.units_per_case,
                    'Volume': line.volume,
                    'Cases per Carton': line.cases_per_carton,
                    'Cartons per Pallet': line.cartons_per_pallet,
                    'Pallet Stacking': line.pallet_stacking,
                    'Product Per Pallet': line.product_per_pallet,
                })
        if warehouse_data:
            # Step 2: Convert data to DataFrame
            df = pd.DataFrame(warehouse_data)

            # Step 3: Save DataFrame to Excel with 18 columns
            with io.BytesIO() as output:
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    def highlight_columns(col):
                        color = 'yellow' if col.name in ['Total Volume CuFt', 'Daily Fee'] else 'white'
                        return ['background-color: {}'.format(color) for _ in col]

                    # calling method using apply()
                    df = df.style.apply(highlight_columns)
                    df.to_excel(writer, sheet_name='Report', index=False)

                    workbook = writer.book
                    worksheet = writer.sheets['Report']

                    worksheet.set_column(0, 0, 25)
                    worksheet.set_column(1, 1, 25)
                    worksheet.set_column(2, 2, 25)

                    # adjust the column widths based on the content
                    for i in range(3, 18):
                        worksheet.set_column(i, i, 15)

                output.seek(0)
                file_data = output.read()

            # Encode file to base64 for Binary field in Odoo
            file_data = base64.b64encode(file_data)
            file_name = "Stock Report {}.xlsx".format(self.warehouse_id.name)

            attachment_id = self.env['ir.attachment'].create({
                'name': file_name,
                'type': 'binary',
                'datas': file_data,
                'store_fname': file_name,
                'res_model': 'stock.fee.billing',  # replace with your model name if necessary
                'res_id': self.id,
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            })
            download_url = '/web/content/?model=ir.attachment&id={}&filename_field=name&field=datas&download=true&name={}'.format(
                attachment_id.id, attachment_id.name)
            action = {
                'type': 'ir.actions.act_url',
                'url': download_url,
                'target': 'new',
            }
            return action

    def write(self, vals):
        res = super(WarehouseInventoryStockLine, self).write(vals)
        for rec in self:
            total_free_to_use_qty = sum(rec.line_report_ids.mapped('forecasted_qty'))
            total_volume_qbft = sum(rec.line_report_ids.mapped('total_volume_cuft'))
            total_daily_fee = sum(rec.line_report_ids.mapped('daily_fee'))
            data_vals = {
                "stock_qty_free_to_use": total_free_to_use_qty,
                "volume_cuft": total_volume_qbft,
                "storage_fee_daily_amount": total_daily_fee
            }
            if rec.stock_fee_billing_line_id:
                rec.stock_fee_billing_line_id.write(data_vals)
        return res


class WarehouseInventoryStockLineReport(models.Model):
    _name = "warehouse.stock.inventory.line.report"
    _description = "Warehouse Inventory Line Report"

    name = fields.Char(string='Name')
    internal_reference = fields.Char(string='Internal Reference')
    product_category = fields.Many2one('product.category', string='Product Category')
    product_id = fields.Many2one('product.product', string='Product')
    pallet_count = fields.Float(string='Pallet Count', digits=(16, 2))
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    qty_on_hand = fields.Float(string='Quantity On Hand')
    incoming_qty = fields.Float(string='Incoming Quantity')
    outgoing_qty = fields.Float(string='Outgoing Quantity')
    free_to_use_qty = fields.Float(string='Free To Use Quantity')
    forecasted_qty = fields.Float(string='Forecasted Quantity')
    units_per_case = fields.Char(string='Units per Case', default=0)
    volume = fields.Float(string='Volume')
    cases_per_carton = fields.Char(string='Cases per Carton')
    cartons_per_pallet = fields.Char(string='Cartons per Pallet')
    pallet_stacking = fields.Char(string='Pallet Stacking')
    product_per_pallet = fields.Float(string='Product Per Pallet')
    total_volume_cuft = fields.Float(string='Total Volume CuFt', digits=(16, 4))
    daily_fee = fields.Float(string='Daily Fee', digits=(16, 4))
    report_line_id = fields.Many2one("warehouse.stock.inventory.line", "Report Line", ondelete='cascade')


class StockFeeBilling(models.Model):
    _name = "stock.fee.billing"
    _description = "Stock Fee Billing"

    name = fields.Char('Name', readonly=True)
    stock_fee_date = fields.Date('Report Date')
    warehouse_id = fields.Many2one("stock.warehouse", 'Warehouse')
    # warehouse_ids = fields.Many2many("stock.warehouse", 'Warehouse')
    # category_ids = fields.Many2many("product.category", 'Category')
    billing_line_ids = fields.One2many("stock.fee.billing.line", "stock_fee_billing_id", string="Billing Lines")

    def open_m_report_list_view(self):
        action = self.env['ir.actions.act_window']._for_xml_id('warehouse_inventory_report.stock_fee_billing_line_action')
        ids = self.billing_line_ids.ids
        action['domain'] = [('id', 'in', ids)]
        return action

    def generate_excel_file(self):
        # Create an in-memory bytes buffer to store the Excel file
        output = io.BytesIO()

        # Create an Excel writer object and add a worksheet
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Initialize workbook and worksheet
            workbook = writer.book
            for rec in self:
                storage_fee_daily_amount = 0
                worksheet = workbook.add_worksheet("{}".format(rec.warehouse_id.name))

                # Set title row for the sheet
                title = "Warefor Logistics\nCarote - Storage Fee - {} {}".format(rec.stock_fee_date.strftime("%B"),
                                                                                 rec.stock_fee_date.year)
                title_format = workbook.add_format({
                    'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'
                })
                worksheet.set_row(0, 45)
                worksheet.merge_range('A1:E1', title, title_format)

                header_format = workbook.add_format({
                    'bold': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True,
                    'border': 1, 'bg_color': '#D3D3D3'
                })

                # Write headers in row 1, starting from column A
                headers = [
                    "Day", "Date", "Stock Quantity\nFree to Use",
                    "Volume\n(CuFt)", "Storage Fee\nDaily Amount"
                ]
                worksheet.set_row(1, 30)
                for col_num, header in enumerate(headers):
                    worksheet.write(1, col_num, header, header_format)

                worksheet.set_column('A:A', 5)  # Day column
                worksheet.set_column('B:B', 15)  # Date column
                worksheet.set_column('C:C', 25)  # Stock Quantity
                worksheet.set_column('D:D', 15)  # Volume
                worksheet.set_column('E:E', 20)  # Storage Fee per Day
                # worksheet.set_column('F:F', 20)  # Daily Amount

                currency_symbol = self.env.company.currency_id.symbol

                row_num = 2
                for row in rec.billing_line_ids:
                    d_row = [row.day, str(row.date), "{:,.2f}".format(row.stock_qty_free_to_use),
                             "{:,.2f}".format(row.volume_cuft),
                             "{}{:,.2f}".format(currency_symbol, row.storage_fee_daily_amount)]
                    storage_fee_daily_amount += row.storage_fee_daily_amount
                    for col_num, value in enumerate(d_row):
                        worksheet.write(row_num, col_num, value)
                    row_num += 1
                row_num += 1
                worksheet.write(row_num, 3, "Total")
                worksheet.write(row_num, 4, "{}{:,.2f}".format(currency_symbol, storage_fee_daily_amount))

        # Create a base64-encoded file attachment in Odoo
        file_data = base64.b64encode(output.getvalue()).decode('utf-8')
        rec = self
        if len(self) > 1:
            rec = self[0]
        file_name = "Carote_Storage_Fee_{}_{}.xlsx".format(rec.warehouse_id.name, rec.name)

        # Create an attachment in Odoo for the generated file
        attachment_id = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': file_data,
            'store_fname': file_name,
            'res_model': 'stock.fee.billing',  # replace with your model name if necessary
            'res_id': rec.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })
        download_url = '/web/content/?model=ir.attachment&id={}&filename_field=name&field=datas&download=true&name={}'.format(
            attachment_id.id, attachment_id.name)
        action = {
            'type': 'ir.actions.act_url',
            'url': download_url,
            'target': 'new',
        }
        return action


class StockFeeBillingLine(models.Model):
    _name = "stock.fee.billing.line"
    _description = "Stock Fee Billing Line"
    _rec_name = "day"

    day = fields.Integer('Day', readonly=True)
    date = fields.Date('Date')
    stock_qty_free_to_use = fields.Float('Stock Quantity Free to Use')
    volume_cuft = fields.Float('Volume (CuFt)')
    storage_fee = fields.Float('Storage Fee (CuFt/Day)', digits=(16, 4))
    storage_fee_daily_amount = fields.Float('Storage Fee Daily Amount')
    stock_fee_billing_id = fields.Many2one("stock.fee.billing", "Billing Fee Record")
    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse")
    category_id = fields.Many2one("product.category", "Category")

    def open_stock_report_list_view(self):
        action = self.env['ir.actions.act_window']._for_xml_id('stock.action_product_stock_view')
        action['context'] = {'search_default_categ_id': self.category_id.id,
                             'search_default_warehouse_id': self.warehouse_id.id,
                             'report_date': self.date
                             }
        return action
