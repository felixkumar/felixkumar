# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class AccountChartTemplate(models.Model):
    _inherit = 'account.chart.template'

    def generate_journals(self, acc_template_ref, company, journals_dict=None):
        # EXTENDS account, creates journals for purchase liquidation, sale withholds, purchase withhold
        res = super(AccountChartTemplate, self).generate_journals(acc_template_ref, company, journals_dict=journals_dict)
        self._l10n_ec_configure_ecuadorian_journals(company)
        return res

    def _l10n_ec_configure_ecuadorian_journals(self, companies):
        for company in companies.filtered(lambda r: r.account_fiscal_country_id.code == 'EC'):
            new_journals_values = [
                {'name': "Retenciones de Clientes",
                 'code': 'RVNTA',
                 'type': 'general',
                 'l10n_ec_withhold_type': 'out_withhold',
                 'l10n_ec_entity': False,
                 'l10n_ec_is_purchase_liquidation': False,
                 'l10n_ec_emission': False,
                 'l10n_ec_emission_address_id': False},
                {'name': "001-001 Retenciones",
                 'code': 'RCMPR',
                 'type': 'general',
                 'l10n_ec_withhold_type': 'in_withhold',
                 'l10n_ec_entity': '001',
                 'l10n_ec_emission': '001',
                 'l10n_ec_is_purchase_liquidation': False,
                 'l10n_ec_emission_address_id': company.partner_id.id},
                {'name': "001-001 Liquidaciones de Compra",
                 'code': 'LIQCO',
                 'type': 'purchase',
                 'l10n_ec_withhold_type': False,
                 'l10n_ec_entity': '001',
                 'l10n_ec_emission': '001',
                 'l10n_ec_is_purchase_liquidation': True,
                 'l10n_latam_use_documents': True,
                 'l10n_ec_emission_address_id': company.partner_id.id},
            ]
            for new_values in new_journals_values:
                journal = self.env['account.journal'].search([
                    ('code', '=', new_values['code']),
                    ('company_id', '=', company.id)])
                if not journal:
                    self.env['account.journal'].create({
                        **new_values,
                        'company_id': company.id,
                        'show_on_dashboard': True,
                    })

    def _load(self, company):
        # EXTENDS account to setup withhold taxes in company configuration
        res = super()._load(company)
        self._l10n_ec_configure_ecuadorian_withhold_taxpayer_type(company)
        self._l10n_ec_setup_profit_withhold_taxes(company)
        self._l10n_ec_copy_taxsupport_codes_from_templates(company)
        self._l10n_ec_setup_edi_purchase_journal_account(company)
        return res

    def _l10n_ec_configure_ecuadorian_withhold_taxpayer_type(self, companies):
        # Set proper profit withhold tax on RIMPE on taxpayer type
        for company in companies.filtered(lambda r: r.account_fiscal_country_id.code == 'EC'):
            tax_rimpe_entrepreneur = self.env['account.tax'].search([
                ('l10n_ec_code_base', '=', '343'),
                ('company_id', '=', company.id)
            ], limit=1)
            tax_rimpe_popular_business = self.env['account.tax'].search([
                ('l10n_ec_code_base', '=', '332'),
                ('company_id', '=', company.id)
            ], limit=1)
            if tax_rimpe_entrepreneur:
                rimpe_entrepreneur = self.env.ref('l10n_ec_edi.l10n_ec_taxpayer_type_13')  # RIMPE Regime Entrepreneur
                rimpe_entrepreneur.with_company(company).profit_withhold_tax_id = tax_rimpe_entrepreneur.id
            if tax_rimpe_popular_business:
                rimpe_popular_business = self.env.ref('l10n_ec_edi.l10n_ec_taxpayer_type_15') # RIMPE Regime Popular Business
                rimpe_popular_business.with_company(company).profit_withhold_tax_id = tax_rimpe_popular_business.id

    def _l10n_ec_setup_profit_withhold_taxes(self, companies):
        # Sets fallback taxes for purchase withholds
        for company in companies.filtered(lambda r: r.account_fiscal_country_id.code == 'EC'):
            company.l10n_ec_withhold_services_tax_id = self.env['account.tax'].search([
                ('l10n_ec_code_ats', '=', '3440'),
                ('tax_group_id.l10n_ec_type', '=', 'withhold_income_purchase'),
                ('company_id', '=', company.id),
            ], limit=1)
            company.l10n_ec_withhold_credit_card_tax_id = self.env['account.tax'].search([
                ('l10n_ec_code_ats', '=', '332G'),
                ('tax_group_id.l10n_ec_type', '=', 'withhold_income_purchase'),
                ('company_id', '=', company.id),
            ], limit=1)
            company.l10n_ec_withhold_goods_tax_id = self.env['account.tax'].search([
                ('l10n_ec_code_ats', '=', '312'),
                ('tax_group_id.l10n_ec_type', '=', 'withhold_income_purchase'),
                ('company_id', '=', company.id),
            ], limit=1)

    def _l10n_ec_copy_taxsupport_codes_from_templates(self, companies):
        # Copy tax support codes from tax templates onto corresponding taxes
        tax_templates = self.env['account.tax.template'].with_context(active_test=False).search([
            ('chart_template_id', '=', self.env.ref('l10n_ec.l10n_ec_ifrs').id),
            ('type_tax_use', '=', 'purchase')
        ])
        xml_ids = tax_templates.get_external_id()
        for company in companies.filtered(lambda r: r.account_fiscal_country_id.code == 'EC'):
            for tax_template in tax_templates:
                module, xml_id = xml_ids.get(tax_template.id).split('.')
                tax = self.env.ref('%s.%s_%s' % (module, company.id, xml_id), raise_if_not_found=False)
                if tax:
                    tax.l10n_ec_code_taxsupport = tax_template.l10n_ec_code_taxsupport

    def _l10n_ec_setup_edi_purchase_journal_account(self, companies):
        journals = self.env['account.journal'].search([('company_id', 'in', companies.ids), ('code', '=', 'LIQCO')])
        expense_accounts = self._get_account_from_template(companies, self.env.ref('l10n_ec.ec52022816', raise_if_not_found=False))
        for company in companies:
            journal = journals.filtered(lambda j: j.company_id == company)
            expense_account = expense_accounts.filtered(lambda a: a.company_id == company)
            if journal and expense_account:
                journal.write({'default_account_id': expense_account.id})
