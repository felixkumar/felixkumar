# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, SUPERUSER_ID

def migrate(cr, version):
    # For new VAT taxes in 2024
    # Migrate the tax support configuration for new VAT taxes in 2024
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env['res.company'].search([('account_fiscal_country_id.code', '=', 'EC')])
    env['account.chart.template']._l10n_ec_copy_taxsupport_codes_from_templates(companies)
