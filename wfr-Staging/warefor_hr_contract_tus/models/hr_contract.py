# -*- coding: utf-8 -*-

from odoo import api, models, fields


class HrContract(models.Model):
    _inherit = 'hr.contract'

    # NEW FIELDS
    overhead_markup = fields.Float(string="Overhead/Markup")
    hourly_cost = fields.Monetary(string="Hourly Cost", compute="_compute_hourly_cost_", readonly=True)
    # OVERRIDING FIElD
    hourly_wage = fields.Monetary('Hourly Wage', default=0, required=True, tracking=True, store=True, readonly=False, help="Employee's hourly gross wage.", compute="_compute_hourly_cost_")

    @api.depends('hourly_wage', 'wage', 'overhead_markup')
    def _compute_hourly_cost_(self):
        """
        - Compute the Hourly Cost based on hourly_wage , overhead_markup.
            Note : overhead_markup has been applied Widget="percentage"
            Formula : hourly_wage + hourly_wage * overhead_markup(Percent Value)
            Example : hourly_wage = 20
                      overhead_markup = 30% so the value will be 0.3
                      hourly_cost = (20 + 20 * 0.3) = 26
        - Compute the Hourly Wage based on Monthly wage.
            Formula : wage * 12 / 2080
        - Compute the Hourly Cost for wage type Monthly.
            Formula : hourly_wage + hourly_wage * overhead_markup(Percent Value)
        """
        for rec in self:
            if rec.wage_type == 'hourly':
                rec.hourly_cost = rec.hourly_wage + rec.hourly_wage * rec.overhead_markup
            elif rec.wage_type == 'monthly':
                rec.hourly_wage = rec.wage * 12 / 2080
                rec.hourly_cost = rec.hourly_wage + rec.hourly_wage * rec.overhead_markup
