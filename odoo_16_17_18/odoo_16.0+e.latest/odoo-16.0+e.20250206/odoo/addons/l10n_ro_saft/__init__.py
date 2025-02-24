# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from . import models

from odoo import api, SUPERUSER_ID


def _update_saft_fields_on_taxes(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    chart_template = env.ref('l10n_ro.ro_chart_template', raise_if_not_found=False)
    if chart_template:
        companies = env['res.company'].search([('chart_template_id', '=', chart_template.id)])
        tax_templates = env['account.tax.template'].search([
            ('chart_template_id', '=', chart_template.id),
            ('l10n_ro_saft_tax_type_id', '!=', False),
        ])
        xml_ids = tax_templates.get_external_id()
        for company in companies:
            for tax_template in tax_templates:
                module, xml_id = xml_ids[tax_template.id].split('.')
                tax = env.ref(f'{module}.{company.id}_{xml_id}', raise_if_not_found=False)
                if tax:
                    tax.write({
                        'l10n_ro_saft_tax_type_id': tax_template.l10n_ro_saft_tax_type_id.id,
                        'l10n_ro_saft_tax_code': tax_template.l10n_ro_saft_tax_code,
                    })
