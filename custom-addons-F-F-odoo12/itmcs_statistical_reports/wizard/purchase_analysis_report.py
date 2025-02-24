from odoo import models, fields, api
from datetime import datetime as date
from odoo.exceptions import UserError
import calendar
from odoo import tools
import odoo.addons.decimal_precision as dp

# wizard model for purchase analysis report:
class ReportPurchaseAnalysisWizard(models.TransientModel):
    _name = 'purchase.analysis.report'
    _description = "Purchase Analysis Report"
    _rec_name = 'partner_id'

    partner_id = fields.Many2one(
        'res.partner', string='Vendor')
    product_id = fields.Many2one(
        'product.product', string="Product")
    start_date = fields.Date(
        string="Start Date", required=True, default=date.today().replace(day=1))
    end_date = fields.Date(string="End Date", required=True, default=date.today(
    ).replace(day=calendar.monthrange(date.today().year, date.today().month)[1]))
    select_report = fields.Selection([('vendor', 'by vendor'), ('product', 'by product')],
                                     string='Select Report', required=True, default="product")
    
    # submit button for purchase analysis report:
    @api.multi
    def submit_information(self):
        if  self.product_id.id or self.select_report =='product':
            context = {'group_by_no_leaf': 1,
                       'group_by': ['product_id','name'],
                       'start_date': self.start_date, 'end_date': self.end_date

                       }
            domain = ['|', 
                      ('product_id', '=', self.product_id.id),
                      ('date_order', '>=', self.start_date),
                      ('date_order', '<=', self.end_date),
                      ]
        elif self.partner_id.id or self.select_report =='vendor':
            context = {'group_by_no_leaf': 1,
                       'group_by': ['partner_id','product_id','name'],
                       'start_date': self.start_date, 'end_date': self.end_date

                       }
            domain = ['|', ('partner_id', '=', self.partner_id.id),
                      ('date_order', '>=', self.start_date),
                      ('date_order', '<=', self.end_date),
                      ]

        return {
            'name': 'Purchase Analysis Reports',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'pivot',
            'res_model': 'purchase.report',
            'view_id': '',
            'help': '''This report performs analysis on your quotations and sales orders. Analysis check your sales revenues and sort it by different group criteria (salesman, partner, product, etc.) Use this report to perform analysis on sales not having invoiced yet. If you want to analyse your turnover, you should use the Invoice Analysis report in the Accounting application.''',
            'context': context,
            'domain': domain
        }
        
    def submit_graph(self):
        if self.select_report == "vendor" :
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
            'name': 'Purchase Analysis Reports',
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
        order_line_obj = self.env['purchase.order.line']
        if self.select_report == "vendor":
            if self.partner_id:
                report_data = []
                product_data = []
                purchase_ids = self.env['purchase.report'].search(
                    [('partner_id', '=', self.partner_id.id),
                     ('date_order', '>=', self.start_date),
                     ('date_order', '<=', self.end_date)])
                if not purchase_ids:
                    raise UserError(
                        'There is no data to display for this partner.')
                for r in purchase_ids:
                    order_line = order_line_obj.browse(r.id)
                    product_data.append({'product_name': r.product_id.name,
                                         'code':r.product_id.default_code or '' ,
                                         'price_unit':r.price_unit ,
                                         'qty':r.unit_quantity,
                                         'bill_amount':r.unit_quantity * r.price_unit,
                                         'ref': order_line.order_id.name
                                         })
                if product_data:
                    report_data.append({'vendor':self.partner_id.name , 'product_data' :product_data})
            else:
                report_data = []
                
                partner_ids = self.env['res.partner'].search([])
                for partner in partner_ids:
                    product_data = []
                    purchase_ids = self.env['purchase.report'].search(
                    [('partner_id', '=', partner.id),
                     ('date_order', '>=', self.start_date),
                     ('date_order', '<=', self.end_date)])
                    for r in purchase_ids:
                        order_line = order_line_obj.browse(r.id)
                        product_data.append({'product_name': r.product_id.name,
                                         'code':r.product_id.default_code or '' ,
                                         'price_unit':r.price_unit ,
                                         'qty':r.unit_quantity,
                                         'bill_amount':r.unit_quantity * r.price_unit,
                                         'ref': order_line.order_id.name
                                         })
                    if product_data:
                        report_data.append({'vendor':partner.name , 'product_data' :product_data})
        elif self.select_report == "product":
            data['form'] = self.read(
                ['start_date', 'end_date', 'product_id', 'select_report'])[0]
            
            if self.product_id:
                report_data = []
                product_data = []
                purchase_ids = self.env['purchase.report'].search(
                    [('product_id', '=', self.product_id.id),
                     ('date_order', '>=', self.start_date),
                     ('date_order', '<=', self.end_date)])
                if purchase_ids:
                    for p in purchase_ids:
                        order_reference = order_line_obj.browse(p.id).order_id.name
                        product_data.append({'product_name': p.product_id.name,
                                             'code':p.product_id.default_code or '' ,
                                             'ref' : order_reference,
                                             'price_unit':p.price_unit,
                                             'qty':p.unit_quantity,
                                             'bill_amount':p.unit_quantity * p.price_unit,
                                             })
                    if product_data:
                        report_data.append({'product':self.product_id.name , 'product_data' :product_data})
                    
            else:
                product_ids = self.env['product.product'].search([])
                report_data = []
                for product in product_ids:
                    product_data = []
                    purchase_ids = self.env['purchase.report'].search(
                        [('product_id', '=', product.id),
                         ('date_order', '>=', self.start_date),
                            ('date_order', '<=', self.end_date)
                         ])
                    if purchase_ids:
                        for p in purchase_ids:
                            order_reference = order_line_obj.browse(p.id).order_id.name
                            product_data.append({
                                              'product_name': p.product_id.name,
                                             'code':p.product_id.default_code or '',
                                             'ref' : order_reference,
                                             'price_unit':p.price_unit,
                                             'qty':p.unit_quantity,
                                             'bill_amount':p.unit_quantity * p.price_unit,
                                            })
                    if product_data:
                        report_data.append({'product':product.name , 'product_data' :product_data})
        return report_data
    
    #  method for pdf print button
    def print_report(self):
        data = {}
        data['form'] = self.read(
            ['start_date', 'end_date', 'select_report'])[0]
        data['form']['reports'] = self.report_data()
        return self.env['report'].get_action(self, 'itmcs_statistical_reports.report_purchaseanalysisreport', data=data)
    
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
            ['start_date', 'end_date', 'select_report'])[0]
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
                    'report_name': 'itmcs_statistical_reports.purchase_analysis.xlsx',
                    'datas': datas,
                    'name': 'purchase reports'
                    }


class PurchaseReport(models.Model):
    _inherit = "purchase.report"
     
    price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Product Price'))
    amount_total = fields.Float(string='Bill Amount')
    name = fields.Char('Order reference')
 
    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'purchase_report')
        self._cr.execute("""
            create view purchase_report as (
                WITH currency_rate as (%s)
                select
                    min(l.id) as id,
                    s.date_order as date_order,
                    s.state,
                    s.amount_total,
                    s.date_approve,
                    s.dest_address_id,
                    spt.warehouse_id as picking_type_id,
                    s.partner_id as partner_id,
                    s.create_uid as user_id,
                    s.company_id as company_id,
                    s.fiscal_position_id as fiscal_position_id,
                    l.product_id,
                    s.name as name,
                    p.product_tmpl_id,
                    t.categ_id as category_id,
                    s.currency_id,
                    t.uom_id as product_uom,
                    sum(l.product_qty/u.factor*u2.factor) as unit_quantity,
                    extract(epoch from age(s.date_approve,s.date_order))/(24*60*60)::decimal(16,2) as delay,
                    extract(epoch from age(l.date_planned,s.date_order))/(24*60*60)::decimal(16,2) as delay_pass,
                    count(*) as nbr_lines,
                    sum(l.price_unit) as price_unit,
                    sum(l.price_unit / COALESCE(cr.rate, 1.0) * l.product_qty)::decimal(16,2) as price_total,
                    avg(100.0 * (l.price_unit / COALESCE(cr.rate,1.0) * l.product_qty) / NULLIF(ip.value_float*l.product_qty/u.factor*u2.factor, 0.0))::decimal(16,2) as negociation,
                    sum(ip.value_float*l.product_qty/u.factor*u2.factor)::decimal(16,2) as price_standard,
                    (sum(l.product_qty * l.price_unit / COALESCE(cr.rate, 1.0))/NULLIF(sum(l.product_qty/u.factor*u2.factor),0.0))::decimal(16,2) as price_average,
                    partner.country_id as country_id,
                    partner.commercial_partner_id as commercial_partner_id,
                    analytic_account.id as account_analytic_id,
                    sum(p.weight * l.product_qty/u.factor*u2.factor) as weight,
                    sum(p.volume * l.product_qty/u.factor*u2.factor) as volume
                from purchase_order_line l
                    join purchase_order s on (l.order_id=s.id)
                    join res_partner partner on s.partner_id = partner.id
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                            LEFT JOIN ir_property ip ON (ip.name='standard_price' AND ip.res_id=CONCAT('product.template,',t.id) AND ip.company_id=s.company_id)
                    left join uom_uom u on (u.id=l.product_uom)
                    left join uom_uom u2 on (u2.id=t.uom_id)
                    left join stock_picking_type spt on (spt.id=s.picking_type_id)
                    left join account_analytic_account analytic_account on (l.account_analytic_id = analytic_account.id)
                    left join currency_rate cr on (cr.currency_id = s.currency_id and
                        cr.company_id = s.company_id and
                        cr.date_start <= coalesce(s.date_order, now()) and
                        (cr.date_end is null or cr.date_end > coalesce(s.date_order, now())))
                group by
                    s.company_id,
                    s.create_uid,
                    s.name,
                    s.partner_id,
                    s.amount_total,
                    u.factor,
                    s.currency_id,
                    l.price_unit,
                    s.date_approve,
                    l.date_planned,
                    l.product_uom,
                    s.dest_address_id,
                    s.fiscal_position_id,
                    l.product_id,
                    p.product_tmpl_id,
                    t.categ_id,
                    s.date_order,
                    s.state,
                    spt.warehouse_id,
                    u.uom_type,
                    u.category_id,
                    t.uom_id,
                    u.id,
                    u2.factor,
                    partner.country_id,
                    partner.commercial_partner_id,
                    analytic_account.id
            )
        """ % self.env['res.currency']._select_companies_rates())     
