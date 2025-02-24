import time
from odoo import api, models


#  reports for stock
class ReportStockreport(models.AbstractModel):
    _name = 'report.itmcs_statistical_reports.report_stockreport'

    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        user = self.env["res.users"].browse(self._uid)
        color = {'company_header_bgcolor1' : user.company_id.company_header_bgcolor1,
        'company_header_fontcolor1' : user.company_id.company_header_fontcolor1,
        'report_header_bgcolor1' : user.company_id.report_header_bgcolor1,
        'report_header_fontcolor1' : user.company_id.report_header_fontcolor1,
        'title_bgcolor1' : user.company_id.title_bgcolor1,
        'title_fontcolor1' : user.company_id.title_fontcolor1,
        'subtitle_bgcolor1' : user.company_id.subtitle_bgcolor1,
        'subtitle_fontcolor1' : user.company_id.subtitle_fontcolor1,
        'text_bgcolor1' : user.company_id.text_bgcolor1,
        'text_fontcolor1' : user.company_id.text_fontcolor1,
            
            }
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': user,
            'time': time,
            'data': data,
            'color' : color,
        }
        return self.env['report'].render('itmcs_statistical_reports.report_stockreport', values=docargs)
