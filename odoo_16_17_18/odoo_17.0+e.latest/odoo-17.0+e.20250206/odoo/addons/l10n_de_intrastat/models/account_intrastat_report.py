from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import _, models, fields, api
from odoo.exceptions import UserError


class IntrastatReportCustomHandler(models.AbstractModel):
    _inherit = 'account.intrastat.report.handler'

    def _custom_options_initializer(self, report, options, previous_options):
        super()._custom_options_initializer(report, options, previous_options)

        if self.env.company.partner_id.country_id.code != 'DE':
            return

        xml_button = {
            'name': _('XML'),
            'sequence': 30,
            'action': 'export_file',
            'action_param': 'de_intrastat_export_to_xml',
            'file_export_type': _('XML'),
        }
        options['buttons'].append(xml_button)

    def de_intrastat_export_to_xml(self, options):
        date_from = fields.Date.to_date(options['date']['date_from'])
        date_to = fields.Date.to_date(options['date']['date_to'])
        final_day_month = date_from + relativedelta(day=31)
        if date_from.day != 1 or date_to != final_day_month:
            raise UserError(_('Wrong date range selected. The intrastat declaration export has to be done monthly.'))
        date = date_from.strftime('%Y-%m')

        query_res = self._get_query_res(options)

        in_vals = [elem for elem in query_res if elem['type'] == 'Arrival']
        out_vals = [elem for elem in query_res if elem['type'] == 'Dispatch']

        today = datetime.today()

        file_content = self.env['ir.qweb']._render('l10n_de_intrastat.intrastat_report_export_xml', {
            'company': self.env.company,
            'envelopeId': f"XGT-{date_from.strftime('%Y%m')}-{today.strftime('%Y%m%d')}-{today.strftime('%H%M')}",
            'user': self.env.user,
            'in_vals': in_vals,
            'out_vals': out_vals,
            'in_vals_total_weight': round(sum(float(elem['weight']) for elem in in_vals), 3),
            'out_vals_total_weight': round(sum(float(elem['weight']) for elem in out_vals), 3),
            'in_vals_total_amount': round(sum(elem['value'] for elem in in_vals), 3),
            'out_vals_total_amount': round(sum(elem['value'] for elem in out_vals), 3),
            'date': date,
            'sending_date': today,
            'is_test': False,
            'version': f'Odoo {self.sudo().env.ref("base.module_base").latest_version}',
            'number_of_declarations': bool(in_vals) + bool(out_vals),
        })

        return {
            'file_name': self.env['account.report'].browse(options['report_id']).get_default_report_filename(options, 'xml'),
            'file_content': file_content,
            'file_type': 'xml',
        }

    def _get_query_res(self, options):
        query, params = self._prepare_query(options)
        self._cr.execute(query, params)
        query_res = self._cr.dictfetchall()
        query_res = self._fill_missing_values(query_res)
        query_res = self._prepare_values_for_de_export(query_res)
        return query_res

    @api.model
    def _prepare_values_for_de_export(self, vals_list):
        for count, vals in enumerate(vals_list, start=1):
            vals['value'] = round(vals['value'], 3)
            vals['itemNumber'] = count
            vals['quantity'] = round(vals['quantity'] * float(vals['supplementary_units']) if vals['supplementary_units'] else vals['quantity'], 2)
        return vals_list
