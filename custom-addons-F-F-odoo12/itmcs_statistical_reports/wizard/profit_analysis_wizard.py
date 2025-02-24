from odoo import models, fields, api
from datetime import datetime as date
from odoo.exceptions import UserError
import calendar
import odoo.addons.decimal_precision as dp
from odoo.tools import float_round


# wizard model for purchase analysis report:
class ReportProfitAnalysisWizard(models.TransientModel):
    _name = 'profit.analysis.report'
    _description = "Profit Analysis Report"
    _rec_name = 'partner_id'

    partner_id = fields.Many2one(
        'res.partner', string='Customer')
    product_id = fields.Many2one(
        'product.product', string="Product")
    start_date = fields.Date(
        string="Start Date", required=True, default=date.today().replace(day=1))
    end_date = fields.Date(string="End Date", required=True, default=date.today(
    ).replace(day=calendar.monthrange(date.today().year, date.today().month)[1]))
    select_report = fields.Selection([('customer', 'by customer'), ('product', 'by product')],
                                     string='Select Report', required=True, default="product")
    
    # submit button for profit analysis report:
    @api.multi
    def submit_information(self):
        
        if self.select_report == "customer" :
            if self.partner_id.id :
                domain = [('partner_id', '=', self.partner_id.id),
                          ('date', '>=', self.start_date),
                          ('date', '<=', self.end_date),
                          ]
                context = { 'group_by_no_leaf': 1,
                           'group_by': ['partner_id',  'product_id','name'],
                           'start_date': self.start_date, 'end_date': self.end_date
                           }
            else:
                domain = ['|',
                      ('date', '>=', self.start_date),
                      ('date', '<=', self.end_date),
                      ]
                context = { 'group_by_no_leaf': 1,
                       'group_by': ['partner_id', 'product_id','name']
                       }
        elif self.select_report == "product" :
            if self.product_id.id:
                domain = [('product_id', '=', self.product_id.id),
                          ('date', '>=', self.start_date),
                          ('date', '<=', self.end_date),
                          ]
                context = { 'group_by_no_leaf': 1,
                           'group_by': ['product_id', 'name'],
                           'start_date': self.start_date, 'end_date': self.end_date
                           }
            else:
                domain = ['|',
                          ('date', '>=', self.start_date),
                          ('date', '<=', self.end_date),
                          ]
                context = { 'group_by_no_leaf': 1,
                           'group_by': ['product_id','name']
                           }

        return {
            'name': 'Profit Analysis Reports',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'pivot',
            'res_model': 'sale.report',
            'view_id': '',
            'help': '''This report performs analysis on your quotations and sales orders. Analysis check your sales revenues and sort it by different group criteria (salesman, partner, product, etc.) Use this report to perform analysis on sales not having invoiced yet. If you want to analyse your turnover, you should use the Invoice Analysis report in the Accounting application.''',
            'context': context,
            'domain': domain
        }

 # submit button for profit graph report:
    @api.multi
    def submit_graph(self):
        
        if self.select_report == "customer" :
            if self.partner_id.id :
                domain = [('partner_id', '=', self.partner_id.id),
                          ('date', '>=', self.start_date),
                          ('date', '<=', self.end_date),
                          ]
                context = { 'group_by_no_leaf': 1,
                           'group_by': ['partner_id',  'product_id','name'],
                           'start_date': self.start_date, 'end_date': self.end_date
                           }
            else:
                domain = ['|',
                      ('date', '>=', self.start_date),
                      ('date', '<=', self.end_date),
                      ]
                context = { 'group_by_no_leaf': 1,
                       'group_by': ['partner_id', 'product_id','name']
                       }
        elif self.select_report == "product" :
            if self.product_id.id:
                domain = [('product_id', '=', self.product_id.id),
                          ('date', '>=', self.start_date),
                          ('date', '<=', self.end_date),
                          ]
                context = { 'group_by_no_leaf': 1,
                           'group_by': ['product_id', 'name'],
                           'start_date': self.start_date, 'end_date': self.end_date
                           }
            else:
                domain = ['|',
                          ('date', '>=', self.start_date),
                          ('date', '<=', self.end_date),
                          ]
                context = { 'group_by_no_leaf': 1,
                           'group_by': ['product_id','name']
                           }

        return {
            'name': 'Profit Analysis Reports',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'graph',
            'res_model': 'sale.report',
            'view_id': '',
            'help': '''This report performs analysis on your quotations and sales orders. Analysis check your sales revenues and sort it by different group criteria (salesman, partner, product, etc.) Use this report to perform analysis on sales not having invoiced yet. If you want to analyse your turnover, you should use the Invoice Analysis report in the Accounting application.''',
            'context': context,
            'domain': domain
        }
                

    # common method for print pdf or xls file
    def report_data(self):
        data = {}
        precision = self.env.user.company_id.currency_id.decimal_places
        if self.select_report == "customer":
            if self.partner_id:
                report_data = []
                product_data = []
                self.env.cr.execute(''' select sr.product_id ,sr.price_unit ,sum(product_uom_qty) as qty,
                    pt.name as product_name,
                    coalesce(sr.purchase_price,0) as cost_price,
                    ((sr.price_unit - coalesce(sr.purchase_price ,0) ) * sum(product_uom_qty)) as gross_profit,
                    coalesce((100 * ( (sr.price_unit - coalesce(sr.purchase_price,0) ) / sr.price_unit )),0) as margin
                    from sale_report sr
                    join product_product pp on sr.product_id = pp.id
                    join product_template pt on  pp.product_tmpl_id =pt.id
                    join uom_uom po on pt.uom_id=po.id
                    where sr.partner_id = %s and  (date_trunc('day', date) between %s and 
                    %s) group by sr.product_id ,sr.price_unit ,pt.name,sr.purchase_price''', (self.partner_id.id, self.start_date, self.end_date))
                results = self.env.cr.dictfetchall()
                for r in results:
                    if r.get('cost_price') == None :
                        r['cost_price'] = 0.0
                    if r.get('gross_profit') == None :
                        r['gross_profit'] = 0.0
                    if r.get('margin') == None :
                        r['margin'] = 0.0
                    if r.get('sale_price') == None :
                        r['sale_price'] = 0.0
                        
                    product_data.append({
                                         'product_name': r.get('product_name') ,
                                          'qty': r.get('qty'),
                                         'cost_price':float_round(r.get('cost_price') , precision_digits=precision),
                                        'gross_profit':float_round(r.get('gross_profit'), precision_digits=precision) ,
                                         'margin': float_round(r.get('margin'), precision_digits=precision),
                                         'sale_price': r.get('price_unit') })
                if product_data:
                    report_data.append({'customer' : self.partner_id.name , 'product_data': product_data})
                if not results:
                    raise UserError(
                        'There is no data to display for this product.')
                    

            else:
                report_data = []
                partner_ids = self.env['res.partner'].search([])
                for partner in partner_ids:
                    product_data =[]
                    self.env.cr.execute(''' select sr.product_id ,sr.price_unit ,sum(product_uom_qty) as qty,
                    pt.name as product_name,
                    coalesce(sr.purchase_price,0) as cost_price,
                    ((sr.price_unit - coalesce(sr.purchase_price ,0) ) * sum(product_uom_qty)) as gross_profit,
                    coalesce((100 * ( (sr.price_unit - coalesce(sr.purchase_price,0) ) / sr.price_unit )),0) as margin
                    from sale_report sr
                    join product_product pp on sr.product_id = pp.id
                    join product_template pt on  pp.product_tmpl_id =pt.id
                    join uom_uom po on pt.uom_id=po.id
                    where sr.partner_id = %s and  (date_trunc('day', date) between %s and 
                    %s) group by sr.product_id ,sr.price_unit ,pt.name,sr.purchase_price''', (partner.id, self.start_date, self.end_date))
                    results = self.env.cr.dictfetchall()
                    for r in results:
                        if r.get('cost_price') == None :
                            r['cost_price'] = 0.0
                        if r.get('gross_profit') == None :
                            r['gross_profit'] = 0.0
                        if r.get('margin') == None :
                            r['margin'] = 0.0
                        if r.get('sale_price') == None :
                            r['sale_price'] = 0.0
                            
                        product_data.append({ 'product_name': r.get('product_name') ,
                                          'qty': r.get('qty'),
                                         'cost_price':float_round(r.get('cost_price') , precision_digits=precision),
                                        'gross_profit':float_round(r.get('gross_profit'), precision_digits=precision) ,
                                         'margin': float_round(r.get('margin'), precision_digits=precision),
                                         'sale_price': r.get('price_unit') })
                    if product_data:
                        report_data.append({'customer': partner.name,'product_data':product_data })

        elif self.select_report == "product":
            data['form'] = self.read(
                ['start_date', 'end_date', 'product_id', 'select_report'])[0]
            if self.product_id:
                report_data = []
                product_data = []
                self.env.cr.execute(''' select sr.product_id ,sr.price_unit ,sum(product_uom_qty) as qty,
                    pt.name as product_name,
                    coalesce(sr.purchase_price,0) as cost_price,
                    ((sr.price_unit - coalesce(sr.purchase_price ,0) ) * sum(product_uom_qty)) as gross_profit,
                    coalesce((100 * ( (sr.price_unit - coalesce(sr.purchase_price,0) ) / sr.price_unit )),0) as margin
                    from sale_report sr
                    join product_product pp on sr.product_id = pp.id
                    join product_template pt on  pp.product_tmpl_id =pt.id
                    join uom_uom po on pt.uom_id=po.id
                    where sr.product_id = %s and  (date_trunc('day', date) between %s and 
                    %s) group by sr.product_id ,sr.price_unit ,pt.name,po.name,sr.purchase_price''', (self.product_id.id, self.start_date, self.end_date))
                results = self.env.cr.dictfetchall()
                for r in results:
                    if r.get('cost_price') == None :
                        r['cost_price'] = 0.0
                    if r.get('gross_profit') == None :
                        r['gross_profit'] = 0.0
                    if r.get('margin') == None :
                        r['margin'] = 0.0
                    if r.get('sale_price') == None :
                        r['sale_price'] = 0.0
                        
                    product_data.append({
                                         'product_name': r.get('product_name') ,
                                          'qty': r.get('qty'),
                                         'cost_price':float_round(r.get('cost_price') , precision_digits=precision),
                                        'gross_profit':float_round(r.get('gross_profit'), precision_digits=precision) ,
                                         'margin': float_round(r.get('margin'), precision_digits=precision),
                                         'sale_price': r.get('price_unit') })
                if product_data:
                    report_data.append({'product' : self.product_id.name , 'product_data': product_data})
                if not results:
                    raise UserError(
                        'There is no data to display for this product.')
            
            else:
                report_data = []
                product_ids = self.env['product.product'].search([])
                for product in product_ids:
                    product_data = []
                    self.env.cr.execute(''' select sr.product_id ,sr.price_unit,sum(product_uom_qty) as qty,
                        pt.name as product_name,
                        coalesce(sr.purchase_price,0) as cost_price,
                        ((sr.price_unit - coalesce(sr.purchase_price ,0) ) * sum(product_uom_qty)) as gross_profit,
                        coalesce((100 * ( (sr.price_unit - coalesce(sr.purchase_price,0) ) / sr.price_unit )),0) as margin
                        from sale_report sr
                        join product_product pp on sr.product_id = pp.id
                        join product_template pt on  pp.product_tmpl_id =pt.id
                        join uom_uom po on pt.uom_id=po.id
                        where sr.product_id = %s and  (date_trunc('day', date) between %s and 
                        %s) group by sr.product_id ,sr.price_unit ,pt.name,po.name,sr.purchase_price''', (product.id,self.start_date,self.end_date))
                    results = self.env.cr.dictfetchall()
                    for r in results:
                        if r.get('cost_price') == None :
                            r['cost_price']  = 0.0
                        if r.get('gross_profit') == None :
                            r['gross_profit']  = 0.0
                        if r.get('margin') == None :
                            r['margin']  = 0.0
                        if r.get('sale_price') == None :
                            r['sale_price']  = 0.0
                        product_data.append({
                                             'product_name': r.get('product_name') ,
                                              'qty': r.get('qty'),
                                            'cost_price':float_round(r.get('cost_price') ,precision_digits=precision),
                                            'gross_profit':float_round(r.get('gross_profit'),precision_digits=precision) ,
                                             'margin': float_round( r.get('margin'), precision_digits=precision),
                                             'sale_price': r.get('price_unit') })
                    if product_data:
                        report_data.append({'product' : product.name , 'product_data': product_data})
        return report_data
            
#  method for pdf print button
    def print_report(self):
        data = {}
        data['form'] = self.read(
            ['start_date', 'end_date', 'select_report'])[0]
        data['form']['reports'] = self.report_data()
        return self.env['report'].get_action(self, 'itmcs_statistical_reports.report_profitanalysisreport', data=data)
    
    #  method for xls download button
    @api.multi
    def export_xls(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        ctx = self.report_data()
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
        datas['model'] = 'purchase.analysis.report'
        datas['form'] = self.read(
                ['start_date', 'end_date', 'product_id', 'select_report'])[0]
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
                    'report_name': 'itmcs_statistical_reports.profit_analysis.xlsx',
                    'datas': datas,
                    'name': 'profit reports'
                    }
