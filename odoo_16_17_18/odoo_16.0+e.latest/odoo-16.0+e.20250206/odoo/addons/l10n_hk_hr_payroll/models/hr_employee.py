# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    # YTI TODO: move this field to hr_payroll in master
    currency_id = fields.Many2one(
        "res.currency",
        string='Currency',
        related='company_id.currency_id')
    l10n_hk_mpf_vc_option = fields.Selection(
        selection=[
            ("none", "Only Mandatory Contribution"),
            ("custom", "With Fixed %VC"),
            ("max", "Cap 5% VC")],
        string="Volunteer Contribution Option", groups="hr.group_hr_user",
        tracking=True,
        copy=False)
    l10n_hk_mpf_vc_percentage = fields.Float(
        string="Volunteer Contribution %",
        groups="hr.group_hr_user",
        tracking=True,
        copy=False)
    l10n_hk_rental_date_start = fields.Date(
        "Rental Start Date",
        groups="hr.group_hr_user",
        tracking=True,
        copy=False)
    l10n_hk_rental_amount = fields.Monetary(
        "Rental Amount",
        groups="hr.group_hr_user",
        tracking=True,
        copy=False)
    l10n_hk_years_of_service = fields.Float(
        "Years of Service",
        compute="_compute_l10n_hk_years_of_service",
        digits=(16, 2),
        groups="hr.group_hr_user")

    @api.constrains('l10n_hk_mpf_vc_percentage')
    def _check_l10n_hk_mpf_vc_percentage(self):
        for employee in self:
            if employee.l10n_hk_mpf_vc_percentage > 0.05 or employee.l10n_hk_mpf_vc_percentage < 0:
                raise ValidationError(_('Enter VC Percentage between 0% and 5%.'))

    def _compute_l10n_hk_years_of_service(self):
        for employee in self:
            contracts = employee.contract_ids.filtered(lambda c: c.state not in ['draft', 'cancel']).sorted('date_start', reverse=True)
            if contracts:
                contract_end_date = contracts[0].date_end or fields.datetime.today().date()
                employee.l10n_hk_years_of_service = ((contract_end_date - employee.first_contract_date).days + 1) / 365
