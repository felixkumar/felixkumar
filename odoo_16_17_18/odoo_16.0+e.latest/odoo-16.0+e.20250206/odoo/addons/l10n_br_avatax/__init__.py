# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, SUPERUSER_ID
from odoo.exceptions import UserError
from . import models
from . import controllers


def pre_init(cr):
    """ Existing databases won't have the taxes being updated in data/account.tax.template.csv, ask them to update that module first. """
    env = api.Environment(cr, SUPERUSER_ID, {})

    if not env.ref('l10n_br.tax_template_out_aproxtrib_fed_incl_goods', raise_if_not_found=False):
        raise UserError('Please upgrade the Brazilian localization (l10n_br) before installing this module.')


def post_init(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    chart_template = env.ref('l10n_br.l10n_br_account_chart_template', raise_if_not_found=False)
    if chart_template:
        companies = env['res.company'].search([('chart_template_id', '=', chart_template.id)])
        tax_templates = env['account.tax.template'].with_context(active_test=False).search([
            ('chart_template_id', '=', chart_template.id),
            ('l10n_br_avatax_code', '!=', False)
        ])
        xml_ids = tax_templates.get_external_id()
        for company in companies:
            for tax_template in tax_templates:
                module, xml_id = xml_ids.get(tax_template.id).split('.')
                tax = env.ref('%s.%s_%s' % (module, company.id, xml_id), raise_if_not_found=False)
                if tax:
                    tax.l10n_br_avatax_code = tax_template.l10n_br_avatax_code

        fp_template = env.ref('l10n_br_avatax.account_fiscal_position_avatax_br', raise_if_not_found=False)
        if fp_template:
            for company in companies.filtered(lambda company: company.chart_template_id == chart_template):
                template_vals = ((fp_template, chart_template._get_fp_vals(company, fp_template)),)
                chart_template._create_records_with_xmlid('account.fiscal.position', template_vals, company)
