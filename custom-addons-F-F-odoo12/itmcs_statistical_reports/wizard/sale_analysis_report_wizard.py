from odoo import models, fields, api
from datetime import datetime as date
from odoo.exceptions import UserError
import calendar
import odoo.addons.decimal_precision as dp
from odoo.tools import float_round

# wizard model for customer or warehouse report
class custom_wizard(models.TransientModel):
    _name = 'custom.wizard'
    _description = "custom Wizard"


    partner_ids = fields.Many2many(
        'res.partner', string='Customer')
    stock_warehouse_ids = fields.Many2many(
        'stock.warehouse', string="Stock Warehouses")
    company_ids = fields.Many2many('res.company',string="Company")
    product_ids = fields.Many2many('product.product',string="Product")
    team_ids = fields.Many2many('crm.team',string="Sales Team")
    salesperson_ids = fields.Many2many('res.users',string="Salesperson")
    start_date = fields.Date(
        string="Start Date", required=True, default=date.today().date().replace(day=1))
    end_date = fields.Date(string="End Date", required=True, default=date.today(
    ).date().replace(day=calendar.monthrange(date.today().date().year, date.today().date().month)[1]))
    select_report = fields.Selection([('customer', 'product by customer'), ('warehouse', 'product by warehouse')],
                                     string='Select Report')

    # set the select_report selection field
    # @api.model
    # def default_get(self, vals):
    #     default_get_res = super(custom_wizard, self).default_get(vals)
    #     for i in vals:
    #         if i == 'partner_id':
    #             default_get_res.update({'select_report': 'customer'})
    #         else:
    #             default_get_res.update({'select_report': 'warehouse'})
    #     return default_get_res

    # submit button for warehouse or customer report
    # @api.multi
    # def submit_information(self):
    #     if self.partner_id.id :
    #         context = {'group_by_no_leaf': 1,
    #                    'search_default_partner_id': self.partner_id.id,
    #                    'group_by': ['partner_id', 'product_id','name' ],
    #                    'start_date': self.start_date, 'end_date': self.end_date
    #                    }
    #         domain = [('partner_id', 'in', [self.partner_id.id] + [i.id for i in self.partner_id.child_ids]),
    #                   ('date', '>=', self.start_date),
    #                   ('date', '<=', self.end_date)
    #                   ]
    #     elif  self.stock_warehouse_id.id:
    #         context = {'group_by_no_leaf': 1,
    #                     'search_default_warehouse_id': self.stock_warehouse_id.id,
    #                    'group_by': ['warehouse_id', 'product_id','name' ],
    #                    'start_date': self.start_date, 'end_date': self.end_date
    #                    }
    #         domain = [('warehouse_id', '=', self.stock_warehouse_id.ids),
    #                   ('date', '>=', self.start_date),
    #                   ('date', '<=', self.end_date)
    #                   ]
    #     elif self.select_report == 'customer' :
    #         domain = ['|',
    #                   ('date', '>=', self.start_date),
    #                   ('date', '<=', self.end_date),
    #                   ]
    #         context = {'group_by_no_leaf': 1,
    #                    'group_by': ['partner_id', 'product_id','name']
    #                    }
    #     elif self.select_report == 'warehouse':
    #         domain = ['|',
    #                   ('date', '>=', self.start_date),
    #                   ('date', '<=', self.end_date),
    #                   ]
    #         context = {'group_by_no_leaf': 1,
    #                    'group_by': ['warehouse_id','product_id','name']
    #                    }
    #     return {
    #         'name': 'custom reports',
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'pivot',
    #         'res_model': 'sale.report',
    #         'view_id': '',
    #         'help': '''This report performs analysis on your quotations and sales orders. Analysis check your sales revenues and sort it by different group criteria (salesman, partner, product, etc.) Use this report to perform analysis on sales not having invoiced yet. If you want to analyse your turnover, you should use the Invoice Analysis report in the Accounting application.''',
    #         'context': context,
    #         'domain': domain
    #     }

    @api.multi
    def submit_information_list(self):
        domain = [
                  ('date', '>=', self.start_date),
                  ('date', '<=', self.end_date)
                  ]
        if self.partner_ids:
            domain.append(('partner_id', 'in', [p.id for p in self.partner_ids]))
        if self.product_ids:
            domain.append(('product_id', 'in', [x.id for x in self.product_ids]))
        if self.stock_warehouse_ids:
            domain.append(('warehouse_id', 'in', [w.id for w in self.stock_warehouse_ids]))
        if self.team_ids:
            domain.append(('team_id', 'in', [t.id for t in self.team_ids]))
        if self.salesperson_ids:
            domain.append(('team_id', 'in', [s.id for s in self.salesperson_ids]))

        return {
            'name': 'Sale Margin Report',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'sale.report',
            'view_id': self.env.ref('itmcs_statistical_reports.custom_view_order_product_tree').id,
            'help': '''This report performs analysis on your quotations and sales orders. Analysis check your sales revenues and sort it by different group criteria (salesman, partner, product, etc.) Use this report to perform analysis on sales not having invoiced yet. If you want to analyse your turnover, you should use the Invoice Analysis report in the Accounting application.''',
            # 'context': context,
            'domain': domain
        }
#graph view details
    # @api.multi
    # def submit_graph(self):
    #     if self.partner_id.id :
    #         context = {'group_by_no_leaf': 1,
    #                    'search_default_partner_id': self.partner_id.id,
    #                    'group_by': ['partner_id', 'product_id','name' ],
    #                    'start_date': self.start_date, 'end_date': self.end_date
    #                    }
    #         domain = [('partner_id', 'in', [self.partner_id.id] + [i.id for i in self.partner_id.child_ids]),
    #                   ('date', '>=', self.start_date),
    #                   ('date', '<=', self.end_date)
    #                   ]
    #     elif  self.stock_warehouse_id.id:
    #         context = {'group_by_no_leaf': 1,
    #                     'search_default_warehouse_id': self.stock_warehouse_id.id,
    #                    'group_by': ['warehouse_id', 'product_id','name' ],
    #                    'start_date': self.start_date, 'end_date': self.end_date
    #                    }
    #         domain = [('warehouse_id', '=', self.stock_warehouse_id.ids),
    #                   ('date', '>=', self.start_date),
    #                   ('date', '<=', self.end_date)
    #                   ]
    #     elif self.select_report == 'customer' :
    #         domain = ['|',
    #                   ('date', '>=', self.start_date),
    #                   ('date', '<=', self.end_date),
    #                   ]
    #         context = {'group_by_no_leaf': 1,
    #                    'group_by': ['partner_id', 'product_id','name']
    #                    }
    #     elif self.select_report == 'warehouse':
    #         domain = ['|',
    #                   ('date', '>=', self.start_date),
    #                   ('date', '<=', self.end_date),
    #                   ]
    #         context = {'group_by_no_leaf': 1,
    #                    'group_by': ['warehouse_id','product_id','name']
    #                    }
    #     return {
    #         'name': 'custom reports',
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'graph',
    #         'res_model': 'sale.report',
    #         'view_id': '',
    #         'help': '''This report performs analysis on your quotations and sales orders. Analysis check your sales revenues and sort it by different group criteria (salesman, partner, product, etc.) Use this report to perform analysis on sales not having invoiced yet. If you want to analyse your turnover, you should use the Invoice Analysis report in the Accounting application.''',
    #         'context': context,
    #         'domain': domain
    #     }

    # common method for print pdf or xls file
    def report_data(self):
        data = {}
        precision = self.env.user.company_id.currency_id.decimal_places
        data['form'] = self.read(
            ['start_date', 'end_date', 'stock_warehouse_ids', 'select_report'])[0]
        report_data = []
        product_data = []
        query_str = '''
            select
            so.name as order,
            pt.name as product,
            so.confirmation_date as order_date,
            rp.name as partner_name,
            sw.name as warehouse_name,
            ct.name as saleteam,
            srp.name as salesperson,
            sum(sol.product_uom_qty*sol.purchase_price) as cost_price,
            sum(sol.price_subtotal) as bill_amount,
            sum(sol.discount) as discount,
            sum(sol.margin) as margin_amnt,
            case when sol.price_unit > 0 then
                                ((sol.price_unit - coalesce(sol.purchase_price ,0)) * sum(sol.product_uom_qty))/ (sol.price_unit * sum(sol.product_uom_qty))* 100 end as margin
            from sale_order_line sol
            LEFT Join sale_order so on so.id = sol.order_id
            LEFT JOIN product_product pp on pp.id = sol.product_id
            LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
            LEFT JOIN res_partner rp on rp.id = so.partner_id
            LEFT JOIN stock_warehouse sw on sw.id = so.warehouse_id
            LEFT JOIN crm_team ct on ct.id = so.team_id
            LEFT JOIN res_users ru on ru.id = so.user_id
            LEFT JOIN res_partner srp on srp.id = ru.partner_id
            
        '''
        where_str = '''
            so.confirmation_date >= '%s' and so.confirmation_date <= '%s'
            and so.state in ('done','sale')
        '''%(self.start_date,self.end_date)
        if self.stock_warehouse_ids:
            where_str += '''
                    and so.warehouse_id %s %s 
            '''%('=' if len(self.stock_warehouse_ids) == 1 else 'in',tuple(s.id for s in self.stock_warehouse_ids) if len(self.stock_warehouse_ids) > 1 else self.stock_warehouse_ids.id)
        if self.partner_ids:
            where_str += '''
                and so.partner_id %s %s
            '''%('=' if len(self.partner_ids) == 1 else 'in',tuple(p.id for p in self.partner_ids) if len(self.partner_ids) > 1 else self.partner_ids.id)

        if self.salesperson_ids:
            where_str += '''
                and so.user_id %s %s
            '''%('=' if len(self.salesperson_ids) == 1 else 'in',tuple(s.id for s in self.salesperson_ids.ids) if len(self.salesperson_ids) > 1 else self.salesperson_ids.id)
        if self.product_ids:
            where_str += '''
                and sol.product_id %s %s
            '''%('=' if len(self.product_ids) == 1 else 'in',tuple(p.id for p in self.product_ids) if len(self.product_ids) > 1 else self.product_ids.id)
        if self.team_ids:
            where_str += '''
                and so.team_id %s %s
            '''%('=' if len(self.team_ids) == 1 else 'in',tuple(t.id for t in self.team_ids.ids) if len(self.team_ids) > 1 else self.team_ids.id)

        group_by_str = '''
          so.name,
            pt.name,
            rp.name,
            so.confirmation_date,
            sw.name,
            ct.name,
            srp.name,
            sol.price_unit,
            sol.purchase_price
        '''
        execute_str = '(%s  WHERE %s GROUP BY %s)' % (query_str, where_str, group_by_str)
        self.env.cr.execute(execute_str)
        results = self.env.cr.dictfetchall()
        self.env.cr.commit()
        for r in results:
            if r.get('code') == None :
                r['code']  = ''
            if r.get('bill_amount') == None :
                r['bill_amount']  = 0.0
            if r.get('cost_price') == None :
                r['cost_price']  = 0.0
            if r.get('gross_profit') == None :
                r['gross_profit']  = 0.0
            if r.get('margin') == None :
                r['margin']  = 0.0
            if r.get('sale_price') == None :
                    r['sale_price']  = 0.0

            product_data.append({
                                 'product_name': r.get('product') ,
                                  'qty': r.get('qty'),
                                  'bill_amount':  float_round(r.get('bill_amount'),precision_digits=precision),
                                 'cost_price':float_round(r.get('cost_price') ,precision_digits=precision),
                                 'gross_profit':float_round(r.get('gross_profit'),precision_digits=precision) ,
                                 'margin': float_round( r.get('margin'), precision_digits=precision),
                                 'uom':r.get('uom'),
                                 'sale_price': r.get('price_unit'),
                                 'warehouse': r.get('warehouse_name'),
                                 'partner':r.get('partner_name'),
                                 'company':r.get('company'),
                                 'salesperson':r.get('salesperson'),
                                 'salesteam':r.get('saleteam'),
                                 'order':r.get('order'),
                                 'margin_amnt':float_round(r.get('margin_amnt'),precision_digits=precision),
                                 'date_order':r.get('order_date'),
                                 'discount':float_round(r.get('discount'),precision_digits=precision)})
        if product_data:
            report_data.append({'product_data': product_data})
        if not results:
            raise UserError(
                'There is no data to display for this warehouse.')
        return report_data
    
    #  method for pdf print button
    def print_report(self):
        data = {}
        data['form'] = self.read(
            ['start_date', 'end_date', 'select_report'])[0]
            
        data['form']['reports'] = self.report_data()
        return self.env.ref('itmcs_statistical_reports.report_sale').report_action(self, data=data)

    #  method for xls download button
    
    @api.multi
    def export_xls(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        ctx =self.report_data()
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
        datas['model'] = 'custom.wizard'
        datas['form'] =self.read(
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
        data = {
            'ids': self.ids,
            'model': self._name,
            'record': datas,
        }
        return self.env.ref('itmcs_statistical_reports.sale_xlsx').report_action(self, data=data)
