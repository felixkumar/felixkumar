from odoo import models, fields, api
from datetime import datetime as date
import calendar


#  stock wizard model
class stock_wizard(models.TransientModel):
    _name = 'stock.wizard'
    _description = "stock Wizard"
    _rec_name = 'warehouse_id'
    
    
    warehouse_id = fields.Many2one(
        'stock.warehouse', string="Stock Warehouse")
    location_id = fields.Many2one(
        'stock.location', string="Stock Location")
    
    
    start_date = fields.Date(
        string="Start Date", required=True, default=date.today().replace(day=1))
    end_date = fields.Date(string="End Date", default=date.today(
    ).replace(day=calendar.monthrange(date.today().year, date.today().month)[1]))
    choose_report = fields.Boolean(string='Choose Report', required=True)
    filter_date = fields.Selection([('duration', 'Date duration'), ('datewise', 'Select Date')],
                                     string='Select Date filter', required=True)


    # submit button for stock report
    @api.multi
    def submit_stock(self):
        report_records = self.report_stock_data()
        ctx = self._context
        self.env.cr.execute("""delete from stock_report""")
        self.env.cr.execute("""delete from stock_report_custom""")
        
        if ctx.get('default_choose_report') == True:
            for report in report_records:    
                for p in  report.get('product_data'):
                    value = {'product_id': p.get('product_id') ,
                            'cost':p.get('avg_cost'),
                            'qty_opening':p.get('open_qty'),
                            'qty_in': p.get('in_qty'),
                            'qty_out':p.get('out_qty'),
                            'qty_closing':p.get('close_qty'),
                            'warehouse_id': p.get('warehouse_id'),
                            'stock_value': p.get('stock_value'),
                            }
                    self.env['stock.report'].create(value)
            return {
            'name': 'Stock Sales Reports',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'pivot',
            'res_model': 'stock.report',
            'view_id': '',
            'help': '''This report performs analysis on your quotations and sales orders. Analysis check your sales revenues and sort it by different group criteria (salesman, partner, product, etc.) Use this report to perform analysis on sales not having invoiced yet. If you want to analyse your turnover, you should use the Invoice Analysis report in the Accounting application.''',
            }
        else:
            for report in report_records:
                for p in  report.get('product_data'):
                    value = {'product_id': p.get('product_id') ,
                            'cost':p.get('avg_cost'),
                            'warehouse_id': p.get('warehouse_id'),
                            'stock_value': p.get('stock_value'),
                            'qty_closing':p.get('close_qty'),
                            }
                    a = self.env['stock.report.custom'].create(value)
            return {
                'name': 'Stock Reports',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'pivot',
                'res_model': 'stock.report.custom',
                'view_id': '',
                'help': '''This report performs analysis on your quotations and sales orders. Analysis check your sales revenues and sort it by different group criteria (salesman, partner, product, etc.) Use this report to perform analysis on sales not having invoiced yet. If you want to analyse your turnover, you should use the Invoice Analysis report in the Accounting application.''',
            }        

   # submit button for stock graph report
    @api.multi
    def submit_graph(self):
        report_records = self.report_stock_data()
        ctx = self._context
        self.env.cr.execute("""delete from stock_report""")
        self.env.cr.execute("""delete from stock_report_custom""")
        
        if ctx.get('default_choose_report') == True:
            for report in report_records:    
                for p in  report.get('product_data'):
                    value = {'product_id': p.get('product_id') ,
                            'cost':p.get('avg_cost'),
                            'qty_opening':p.get('open_qty'),
                            'qty_in': p.get('in_qty'),
                            'qty_out':p.get('out_qty'),
                            'qty_closing':p.get('close_qty'),
                            'warehouse_id': p.get('warehouse_id'),
                            'stock_value': p.get('stock_value'),
                            }
                    self.env['stock.report'].create(value)
            return {
            'name': 'Stock Sales Reports',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'graph',
            'res_model': 'stock.report',
            'view_id': '',
            'help': '''This report performs analysis on your quotations and sales orders. Analysis check your sales revenues and sort it by different group criteria (salesman, partner, product, etc.) Use this report to perform analysis on sales not having invoiced yet. If you want to analyse your turnover, you should use the Invoice Analysis report in the Accounting application.''',
            }
        else:
            for report in report_records:
                for p in  report.get('product_data'):
                    value = {'product_id': p.get('product_id') ,
                            'cost':p.get('avg_cost'),
                            'warehouse_id': p.get('warehouse_id'),
                            'stock_value': p.get('stock_value'),
                            'qty_closing':p.get('close_qty'),
                            }
                    a = self.env['stock.report.custom'].create(value)
            return {
                'name': 'Stock Reports',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'graph',
                'res_model': 'stock.report.custom',
                'view_id': '',
                'help': '''This report performs analysis on your quotations and sales orders. Analysis check your sales revenues and sort it by different group criteria (salesman, partner, product, etc.) Use this report to perform analysis on sales not having invoiced yet. If you want to analyse your turnover, you should use the Invoice Analysis report in the Accounting application.''',
            }    

    # common method for print pdf or xls file
    def report_stock_data(self):
        product_search = self.env['product.product'].search([])
        move_search = self.env['stock.move']
        
        if self.warehouse_id:
            report_data = []
            picking_type_in = self.env['stock.picking.type'].search([('code', '=', 'incoming') , ('warehouse_id', '=', self.warehouse_id.id)])
            picking_type_out = self.env['stock.picking.type'].search([('code', '=', 'outgoing') , ('warehouse_id', '=', self.warehouse_id.id)])
            product_data = []
            for product in product_search:
                opening = closing = move_in_qty = move_out_qty = move_open_in_qty = move_open_out_qty = stock_value = avg_cost = 0.0 
                if self.filter_date == 'duration':
                    move_in = [('product_id', '=' , product.id), ('date', '>=', self.start_date), ('date', '<=', self.end_date), ('state', '=', 'done'), ('picking_type_id', 'in' , [ x.id for x in picking_type_in])]
                    move_out = [('product_id', '=' , product.id), ('date', '>=', self.start_date), ('date', '<=', self.end_date), ('state', '=', 'done'), ('picking_type_id', 'in' , [ x.id for x in picking_type_out])]
                    move_open_in = [('product_id', '=' , product.id), ('date', '<=', self.start_date), ('state', '=', 'done'), ('picking_type_id', 'in' , [ x.id for x in picking_type_in])]
                    move_open_out = [('product_id', '=' , product.id), ('date', '<=', self.start_date), ('state', '=', 'done'), ('picking_type_id', 'in' , [ x.id for x in picking_type_out])]
                else:
                    move_in = [('product_id', '=' , product.id), ('date', '>=', self.start_date), ('date', '<=', self.start_date), ('state', '=', 'done'), ('picking_type_id', 'in' , [ x.id for x in picking_type_in])]
                    move_out = [('product_id', '=' , product.id), ('date', '>=', self.start_date), ('date', '<=', self.start_date), ('state', '=', 'done'), ('picking_type_id', 'in' , [ x.id for x in picking_type_out])]
                    move_open_in = [('product_id', '=' , product.id), ('date', '>=', self.start_date), ('date', '<=', self.start_date), ('state', '=', 'done'), ('picking_type_id', 'in' , [ x.id for x in picking_type_in])]
                    move_open_out = [('product_id', '=' , product.id), ('date', '>=', self.start_date), ('date', '<=', self.start_date), ('state', '=', 'done'), ('picking_type_id', 'in' , [ x.id for x in picking_type_out])]
                moves_in_res_past = [ item['product_qty'] for item in move_search.read_group(move_in, [ 'product_id', 'product_qty'], ['product_id'])]
                moves_out_res_past = [ item['product_qty'] for item in move_search.read_group(move_out, [ 'product_id', 'product_qty'], ['product_id'])]
                moves_open_in = [ item['product_qty'] for item in move_search.read_group(move_open_in, [ 'product_id', 'product_qty'], ['product_id'])]
                moves_open_out = [ item['product_qty'] for item in move_search.read_group(move_open_out, [ 'product_id', 'product_qty'], ['product_id'])]
                if moves_in_res_past:
                    move_in_qty = moves_in_res_past[0]
                if moves_out_res_past:
                    move_out_qty = moves_out_res_past[0]
                if moves_open_in:
                    move_open_in_qty = moves_open_in[0]
                if moves_open_out:
                    move_open_out_qty = moves_open_out[0]
                opening = move_open_in_qty - move_open_out_qty
                closing = opening + move_in_qty - move_out_qty
                stock_value = closing * product.standard_price
                avg_cost = product.standard_price
                if closing or opening or move_out_qty or move_in_qty:
                    product_data.append({'warehouse_id':self.warehouse_id.id, 'product' : product.name , 'product_id':product.id, 'avg_cost':avg_cost , 'stock_value':stock_value, 'product_code': product.default_code, 'unit':product.uom_id.name, 'in_qty': move_in_qty , 'out_qty': move_out_qty, 'open_qty':opening , 'close_qty' :closing })
            if product_data:
                report_data = [{'warehouse' : self.warehouse_id.name, 'product_data': product_data}]
            return report_data
        else:
            report_data = []
            warehouse_search = self.env['stock.warehouse'].search([])
            for warehouse in warehouse_search:
                picking_type_in = self.env['stock.picking.type'].search([('code', '=', 'incoming') , ('warehouse_id', '=', warehouse.id)])
                picking_type_out = self.env['stock.picking.type'].search([('code', '=', 'outgoing') , ('warehouse_id', '=', warehouse.id)])
                product_data = []
                for product in product_search:
                    opening = closing = move_in_qty = move_out_qty = move_open_in_qty = move_open_out_qty = stock_value = avg_cost = 0.0 
                    if self.start_date and  self.end_date:
                        move_in = [('product_id', '=' , product.id), ('date', '>=', self.start_date), ('date', '<=', self.end_date), ('state', '=', 'done'), ('picking_type_id', 'in' , [ x.id for x in picking_type_in])]
                        move_out = [('product_id', '=' , product.id), ('date', '>=', self.start_date), ('date', '<=', self.end_date), ('state', '=', 'done'), ('picking_type_id', 'in' , [ x.id for x in picking_type_out])]
                        move_open_in = [('product_id', '=' , product.id), ('date', '<=', self.start_date), ('state', '=', 'done'), ('picking_type_id', 'in' , [ x.id for x in picking_type_in])]
                        move_open_out = [('product_id', '=' , product.id), ('date', '<=', self.start_date), ('state', '=', 'done'), ('picking_type_id', 'in' , [ x.id for x in picking_type_out])]
                    else:
                        move_in = [('product_id', '=' , product.id), ('date', '>=', self.start_date), ('date', '<=', self.start_date), ('state', '=', 'done'), ('picking_type_id', 'in' , [ x.id for x in picking_type_in])]
                        move_out = [('product_id', '=' , product.id), ('date', '>=', self.start_date), ('date', '<=', self.start_date), ('state', '=', 'done'), ('picking_type_id', 'in' , [ x.id for x in picking_type_out])]
                        move_open_in = [('product_id', '=' , product.id), ('date', '>=', self.start_date), ('date', '<=', self.start_date), ('state', '=', 'done'), ('picking_type_id', 'in' , [ x.id for x in picking_type_in])]
                        move_open_out = [('product_id', '=' , product.id), ('date', '>=', self.start_date), ('date', '<=', self.start_date), ('state', '=', 'done'), ('picking_type_id', 'in' , [ x.id for x in picking_type_out])]
                    moves_in_res_past = [ item['product_qty'] for item in move_search.read_group(move_in, [ 'product_id', 'product_qty'], ['product_id'])]
                    moves_out_res_past = [ item['product_qty'] for item in move_search.read_group(move_out, [ 'product_id', 'product_qty'], ['product_id'])]
                    moves_open_in = [ item['product_qty'] for item in move_search.read_group(move_open_in, [ 'product_id', 'product_qty'], ['product_id'])]
                    moves_open_out = [ item['product_qty'] for item in move_search.read_group(move_open_out, [ 'product_id', 'product_qty'], ['product_id'])]
                    if moves_in_res_past:
                        move_in_qty = moves_in_res_past[0]
                    if moves_out_res_past:
                        move_out_qty = moves_out_res_past[0]
                    if moves_open_in:
                        move_open_in_qty = moves_open_in[0]
                    if moves_open_out:
                        move_open_out_qty = moves_open_out[0]
                    opening = move_open_in_qty - move_open_out_qty
                    closing = opening + move_in_qty - move_out_qty
                    stock_value = closing * product.standard_price
                    avg_cost = product.standard_price
                    if closing or opening or move_out_qty or move_in_qty:
                        product_data.append({'warehouse_id':warehouse.id, 'product' : product.name , 'product_id':product.id, 'avg_cost':avg_cost , 'stock_value': stock_value, 'product_code': product.default_code, 'unit':product.uom_id.name, 'in_qty': move_in_qty , 'out_qty': move_out_qty, 'open_qty':opening , 'close_qty' :closing })
                if product_data:
                    report_data.append({'warehouse' : warehouse.name , 'product_data' : product_data})
            
            return report_data

    def print_stock_report(self):
        data = {}
        data['form'] = self.read(
            ['start_date', 'end_date', 'choose_report' , 'location_id' , 'filter_date', 'warehouse_id'])[0]
        data['form']['reports'] = self.report_stock_data()
        return self.env['report'].get_action(self, 'itmcs_statistical_reports.report_stockreport', data=data)


    #  method for xls download button
    @api.multi
    def export_xls(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        ctx = self.report_stock_data()
        user = self.env["res.users"].browse(self._uid)
        company_name = user.company_id.name
        header_bgcolor = user.company_id.company_header_bgcolor
        header_fontcolor = user.company_id.company_header_fontcolor
        report_header_bgcolor = user.company_id.report_header_bgcolor
        report_header_fontcolor = user.company_id.report_header_fontcolor
        title_bgcolor = user.company_id.title_bgcolor
        title_fontcolor = user.company_id.title_fontcolor
        subtitle_bgcolor = user.company_id.subtitle_bgcolor
        subtitle_fontcolor = user.company_id.subtitle_fontcolor
        text_bgcolor = user.company_id.text_bgcolor
        text_fontcolor = user.company_id.text_fontcolor
        datas['model'] = 'stock.wizard'
        datas['form'] = self.read(
            ['start_date', 'end_date', 'choose_report' , 'location_id' , 'filter_date', 'warehouse_id'])[0]
        datas['form']['context'] = ctx
        datas['form']['company'] = company_name
        datas['form']['company_header_bgcolor'] = header_bgcolor
        datas['form']['company_header_fontcolor'] = header_fontcolor
        datas['form']['report_header_bgcolor'] = report_header_bgcolor
        datas['form']['report_header_fontcolor'] = report_header_fontcolor
        datas['form']['title_bgcolor'] = title_bgcolor
        datas['form']['title_fontcolor'] = title_fontcolor
        datas['form']['subtitle_bgcolor'] = subtitle_bgcolor
        datas['form']['subtitle_fontcolor'] = subtitle_fontcolor
        datas['form']['text_bgcolor'] = text_bgcolor
        datas['form']['text_fontcolor'] = text_fontcolor
        if context.get('xls_export'):
            return {'type': 'ir.actions.report.xml',
                    'report_name': 'itmcs_statistical_reports.stock_analysis.xlsx',
                    'datas': datas,
                    'name': 'stock reports'
                    }
