# -*- coding: utf-8 -*-

from odoo import api, fields, models


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', store=True)
    alias_name = fields.Char(string="Alias")


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # OVERRIDING FIElDS
    hourly_cost = fields.Monetary('Hourly Cost', currency_field='currency_id', groups="hr.group_hr_user", default=0.0,
                                  compute='_compute_hourly_cost', store=True)
    hourly_wage = fields.Monetary('Hourly Wage', currency_field='currency_id', groups="hr.group_hr_user", default=0.0,
                                  compute='_compute_hourly_wage', store=True)
    # warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', store=True) Added field on base model

    @api.depends('contract_id', 'contract_id.hourly_cost', 'contract_id.state')
    def _compute_hourly_cost(self):
        """ Compute the Hourly Cost based on contract_id , contract_id.state and contract_id.hourly_cost """
        for rec in self:
            if rec.contract_id and rec.contract_id.state == 'open':
                rec.hourly_cost = rec.contract_id.hourly_cost
            else:
                rec.hourly_cost = 0.0

    @api.depends('contract_id', 'contract_id.hourly_wage', 'contract_id.state')
    def _compute_hourly_wage(self):
        """ Compute the Hourly wage based on contract_id , contract_id.state and contract_id.hourly_wage """
        for rec in self:
            if rec.contract_id and rec.contract_id.state == 'open':
                rec.hourly_wage = rec.contract_id.hourly_wage
            else:
                rec.hourly_cost = 0.0
