# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    l10n_ke_food_allowance = fields.Monetary("Food Allowance")
    l10n_ke_airtime_allowance = fields.Monetary("Airtime Allowance")
    l10n_ke_pension_allowance = fields.Monetary("Pension Allowance")

    l10n_ke_volontary_medical_insurance = fields.Monetary("Voluntary medical Insurance")
    l10n_ke_life_insurance = fields.Monetary("Life Insurance")
    l10n_ke_education = fields.Monetary("Education")
