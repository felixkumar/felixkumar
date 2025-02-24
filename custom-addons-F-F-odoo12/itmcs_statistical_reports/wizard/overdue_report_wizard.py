from odoo import models, fields, api
from odoo.exceptions import UserError
import calendar
from datetime import date


# wizard model for overdue report
class Overdue_wizard(models.TransientModel):
    _name = 'overdue.wizard'
    _description = "Overdue Wizard"
    _rec_name = 'start_date'

    partner_id = fields.Many2one('res.partner', string='Customer')
    start_date = fields.Date(
        string=" start date", required=True, default=date.today().replace(day=1))
    select_report = fields.Selection([('general', 'General Due sales'), ('pos', 'POS Due sales'), ('total', 'Total Due Sales')], string='Select Report Type', required=True)
    end_date = fields.Date(string=" end date", required=True, default=date.today(
    ).replace(day=calendar.monthrange(date.today().year, date.today().month)[1]))

    
    # submit button for overdue report
    @api.multi
    def submit_overdue(self):
        if self.partner_id.id:
            if self.select_report == "general":
                context = {'search_default_Sales': 1, 'group_by_no_leaf': 1,
                           'group_by': ['partner_id',  'date:day','ref'],
                           }
                domain = [('partner_id', '=', self.partner_id.id),
                          ('date', '>=', self.start_date),
                          ('date', '<=', self.end_date),
                          ('name', '=', '')
                          ]
            elif self.select_report == "pos":
                context = {'search_default_Sales': 1, 'group_by_no_leaf': 1,
                           'group_by': ['partner_id',  'date:day','ref'],
                           }
                domain = [('partner_id', '=', self.partner_id.id),
                          ('date', '>=', self.start_date),
                          ('date', '<=', self.end_date),
                          ('name', '!=', '')
                          ]
            elif self.select_report == "total":
                context = {'search_default_Sales': 1, 'group_by_no_leaf': 1,
                           'group_by': ['partner_id',  'date:day','ref'],
                           }
                domain = [('partner_id', '=', self.partner_id.id),
                          ('date', '>=', self.start_date),
                          ('date', '<=', self.end_date),
                          ]
        elif self.partner_id.id == False:
            if self.select_report == "general":
                domain = [
                          ('date', '>=', self.start_date),
                          ('date', '<=', self.end_date),
                          ('name', '=', '')
                          ]
                context = {'search_default_Sales': 1, 'group_by_no_leaf': 1,
                           'group_by': ['partner_id', 'date:day','ref']
                           }
            elif self.select_report == "pos":
                domain = [
                          ('date', '>=', self.start_date),
                          ('date', '<=', self.end_date),
                          ('name', '!=', '')
                          ]
                context = {'search_default_Sales': 1, 'group_by_no_leaf': 1,
                           'group_by': ['partner_id', 'date:day','ref']
                           }
            elif self.select_report == "total":
                domain = [
                          ('date', '>=', self.start_date),
                          ('date', '<=', self.end_date),
    
                          ]
                context = {'search_default_Sales': 1, 'group_by_no_leaf': 1,
                           'group_by': ['partner_id', 'date:day','ref']
                           }
        return {
            'name': 'Overdue Report',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'pivot',
            'res_model': 'overdue.report',
            'view_id': '',
            'help': '''This report performs analysis on your quotations and sales orders. Analysis check your sales revenues and sort it by different group criteria (salesman, partner, product, etc.) Use this report to perform analysis on sales not having invoiced yet. If you want to analyse your turnover, you should use the Invoice Analysis report in the Accounting application.''',
            'context': context,
            'domain': domain
        }
    
    @api.multi
    def submit_graph(self):
        if self.partner_id.id:
            if self.select_report == "general":
                context = {'search_default_Sales': 1, 'group_by_no_leaf': 1,
                           'group_by': ['partner_id',  'date:day','ref'],
                           }
                domain = [('partner_id', '=', self.partner_id.id),
                          ('date', '>=', self.start_date),
                          ('date', '<=', self.end_date),
                          ('name', '=', '')
                          ]
            elif self.select_report == "pos":
                context = {'search_default_Sales': 1, 'group_by_no_leaf': 1,
                           'group_by': ['partner_id',  'date:day','ref'],
                           }
                domain = [('partner_id', '=', self.partner_id.id),
                          ('date', '>=', self.start_date),
                          ('date', '<=', self.end_date),
                          ('name', '!=', '')
                          ]
            elif self.select_report == "total":
                context = {'search_default_Sales': 1, 'group_by_no_leaf': 1,
                           'group_by': ['partner_id',  'date:day','ref'],
                           }
                domain = [('partner_id', '=', self.partner_id.id),
                          ('date', '>=', self.start_date),
                          ('date', '<=', self.end_date),
                          ]
        elif self.partner_id.id == False:
            if self.select_report == "general":
                domain = [
                          ('date', '>=', self.start_date),
                          ('date', '<=', self.end_date),
                          ('name', '=', '')
                          ]
                context = {'search_default_Sales': 1, 'group_by_no_leaf': 1,
                           'group_by': ['partner_id', 'date:day','ref']
                           }
            elif self.select_report == "pos":
                domain = [
                          ('date', '>=', self.start_date),
                          ('date', '<=', self.end_date),
                          ('name', '!=', '')
                          ]
                context = {'search_default_Sales': 1, 'group_by_no_leaf': 1,
                           'group_by': ['partner_id', 'date:day','ref']
                           }
            elif self.select_report == "total":
                domain = [
                          ('date', '>=', self.start_date),
                          ('date', '<=', self.end_date),
    
                          ]
                context = {'search_default_Sales': 1, 'group_by_no_leaf': 1,
                           'group_by': ['partner_id', 'date:day','ref']
                           }
        return {
            'name': 'Overdue Report',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'graph',
            'res_model': 'overdue.report',
            'view_id': '',
            'help': '''This report performs analysis on your quotations and sales orders. Analysis check your sales revenues and sort it by different group criteria (salesman, partner, product, etc.) Use this report to perform analysis on sales not having invoiced yet. If you want to analyse your turnover, you should use the Invoice Analysis report in the Accounting application.''',
            'context': context,
            'domain': domain
        }

    # common method for print pdf or xls file
    def report_data(self):
        data = {}
        
        data['form'] = self.read(['partner_id', 'start_date', 'end_date', 'select_report'])[0]
        if self.select_report == "general":
            ctx ={'overdues' :[]}
            if self.partner_id:
                    
                    overdue_ids = self.env['overdue.report'].search(
                        [('partner_id', '=', self.partner_id.id),
                            ('date', '>=', self.start_date),
                            ('date', '<=', self.end_date),
                            ('name', '=', '')])
                    if overdue_ids:
                        ctx = {
                            'overdues': [(self.partner_id.id, [x.id for x in overdue_ids])]}
                    else:
                        raise UserError(
                                'There is no data to display for this partner.')
            else:
                partner_ids = self.env['res.partner'].search([])
                ctx = {'overdues': []}
                for partner in partner_ids:
                    overdue_ids = self.env['overdue.report'].search(
                        [('partner_id', '=', partner.id),
                         ('date', '>=', self.start_date),
                         ('date', '<=', self.end_date),
                         ('name', '=', '')])

                    if overdue_ids:
                        ctx['overdues'].append(
                            (partner.id, [x.id for x in overdue_ids]))
        
        elif self.select_report == "pos":
            ctx ={'overdues' :[]}
            if self.partner_id:
                overdue_ids = self.env['overdue.report'].search(
                    [('partner_id', '=', self.partner_id.id),
                     ('date', '>=', self.start_date),
                     ('date', '<=', self.end_date),
                     ('name', '!=', '')])
                if overdue_ids:
                    ctx = {
                        'overdues': [(self.partner_id.id, [x.id for x in overdue_ids])]}
                else:
                    raise UserError(
                        'There is no data to display for this partner.')
            else:
                partner_ids = self.env['res.partner'].search([])
                for partner in partner_ids:
                    domain = [('partner_id', '=', partner.id),
                         ('date', '>=', self.start_date),
                         ('date', '<=', self.end_date),
                         ('name', '!=', '')]
                    overdue_ids = self.env['overdue.report'].search(domain)
                    if overdue_ids:
                        ctx['overdues'].append(
                            (partner.id, [x.id for x in overdue_ids]))
                        
        elif self.select_report == "total":
            ctx ={'overdues' :[]}
            if self.partner_id:
                overdue_ids = self.env['overdue.report'].search(
                    [('partner_id', '=', self.partner_id.id),
                     ('date', '>=', self.start_date),
                     ('date', '<=', self.end_date)])
                if overdue_ids:
                    ctx = {
                        'overdues': [(self.partner_id.id, [x.id for x in overdue_ids])]}
                else:
                    raise UserError(
                        'There is no data to display for this partner.')
            else:
                partner_ids = self.env['res.partner'].search([])
                ctx = {'overdues': []}
                for partner in partner_ids:
                    overdue_ids = self.env['overdue.report'].search(
                        [('partner_id', '=', partner.id),
                         ('date', '>=', self.start_date),
                         ('date', '<=', self.end_date)])
                    if overdue_ids:
                        ctx['overdues'].append(
                            (partner.id, [x.id for x in overdue_ids]))
        return ctx


    #  method for pdf print button
    def print_overdue(self):
        data = {}
        data['form'] = self.read(['partner_id', 'start_date', 'end_date', 'select_report'])[0]
        ctx = self.report_data()['overdues']
        data['form']['context'] = ctx
        return self.env.ref('itmcs_statistical_reports.report_overdue').report_action(self, data=data)
    #  method for xls download button
    @api.multi
    def export_xls(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        ctx = self.report_data()['overdues']
        user = self.env["res.users"].browse(self._uid)
        company_name = user.company_id.name
        company_logo = user.company_id.logo
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
        datas['model'] = 'overdue.wizard'
        datas['form'] = self.read(['partner_id', 'start_date', 'end_date', 'select_report'])[0]
        datas['form']['context'] = ctx
        datas['form']['company'] = company_name
        # datas['form']['company_logo'] = company_logo
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
        return self.env.ref('itmcs_statistical_reports.overdue_xlsx').report_action(self, data=data)
