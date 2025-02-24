# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    _description = 'Analytic Line'

    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", store=True)
    hour_type_id = fields.Many2one('hour.types', string="Hour Types", copy=False)
    hourly_cost = fields.Float(string="Hourly Cost", compute='_compute_timesheet_hourly_cost', store=True)
    hourly_wage = fields.Float(string="Hourly Wage", compute='_compute_timesheet_hourly_cost', store=True)
    cost = fields.Float(string="Cost", readonly=False)
    nominal_wage = fields.Float(string="Nominal Wage", readonly=False)
    alias_name = fields.Char(string="Employee Alias", related="employee_id.alias_name")

    @api.onchange('employee_id')
    def _onchange_warehouse_id(self):
        if self.employee_id and self.employee_id.warehouse_id:
            self.warehouse_id = self.employee_id.warehouse_id

    @api.depends('employee_id', 'hour_type_id')
    def _compute_timesheet_hourly_cost(self):
        """
            Compute Hourly cost for the employee timesheet, hourly cost from employee Multiplied by multiplier in hour type
        """
        for rec in self:
            date = rec.date
            for contract in rec.employee_id.contract_ids:
                if date >= contract.date_start and date <= (contract.date_end or fields.date.today()):
                    rec.hourly_cost = contract.hourly_cost and (contract.hourly_cost * rec.hour_type_id.multiplier) or 0.00
                    rec.hourly_wage = contract.hourly_wage and (contract.hourly_wage * rec.hour_type_id.multiplier) or 0.00
            # rec.hourly_cost = rec.employee_id.hourly_cost and (rec.employee_id.hourly_cost * rec.hour_type_id.multiplier) or 0.00
            # rec.hourly_wage = rec.employee_id.hourly_wage and (rec.employee_id.hourly_wage * rec.hour_type_id.multiplier) or 0.00

    @api.onchange('unit_amount', 'hourly_cost', 'hour_type_id', 'hourly_wage')
    def onchange_unit_amount_cost(self):
        for rec in self:
            if not rec.hourly_cost:
                rec.hourly_cost = rec.employee_id.hourly_cost and (
                            rec.employee_id.hourly_cost * rec.hour_type_id.multiplier) or 0.00
            rec.cost = -abs(rec.unit_amount * rec.hourly_cost)
            rec.nominal_wage = -abs(rec.unit_amount * rec.hourly_wage)

    @api.model
    def create(self, vals):
        res = super(AccountAnalyticLine, self).create(vals)
        if self.env['ir.config_parameter'].sudo().get_param('update_timesheet_cost'):
            res.onchange_unit_amount_cost()
        if not res.warehouse_id and res.employee_id.warehouse_id:
            res.warehouse_id = res.employee_id.warehouse_id.id
        return res
