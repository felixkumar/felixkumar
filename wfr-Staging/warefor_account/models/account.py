# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class Account(models.Model):
    _inherit = "account.account"

    detail_type = fields.Many2one(comodel_name="account.quickbooks.type", string="Detail Type")
    parent_account_id = fields.Many2one(comodel_name="account.account", string="Parent Account")
    detail_description = fields.Char(string="Description", required=False, )


class AccountMove(models.Model):
    _inherit = "account.move"

    is_imported = fields.Boolean(string="Is Imported", default=False)
    imported_type = fields.Char(string="Imported Type", default=False)

    # def update_account_move_name_seq(self):
    #     for i in self.search([]):
    #         print("1111111111")
    #         if i.move_type == 'in_invoice':
    #             print(" i.highest_name.rspilt('/') i.highest_name.rspilt('/')",
    #                   '%04d' % (int(i.highest_name.rsplit('/')[-1]) + 1))
    #             i._compute_highest_name()
    #             new_name = "/".join(i.highest_name.rsplit('/')[:-1]) + '/' + '%04d' % (
    #                         int(i.highest_name.rsplit('/')[-1]) + 1)
    #             print("new_namenew_namenew_namenew_namenew_namenew_name", new_name)
    #             i.write({'name': new_name})
    #             # i.name = ''
    #         # if not i.name:
    #         #     i.date = fields.Date.today()
    #         #     i.write({'date': date,'invoice_date':date})


class AccountMoveLineInherit(models.Model):
    _inherit = "account.move.line"

    @api.model_create_multi
    def create(self, vals_list):
        records = super(AccountMoveLineInherit, self).create(vals_list)
        for rec in records:
            analytic_account_id = rec.move_id.partner_id.analytic_account_id
            if rec.product_id.is_add_analytic_account and analytic_account_id:
                rec.analytic_distribution = {analytic_account_id.id: 100}
        return records

    # For create unbalanced journal entries (at script time)
    # @api.model_create_multi
    # def create(self, vals_list):
    #     self.env.context = dict(self.env.context)
    #     self.env.context.update({
    #         'check_move_validity': False,
    #     })
    #     res = super(AccountMoveLineInherit, self).create(vals_list)
    #     return res


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse")
    logistic_source = fields.Selection([("inbound", "Inbound"), ("outbound", "Outbound")], string="Logistic Source")

    def _select(self):
        return super()._select() + ", move.warehouse_id as warehouse_id , move.logistic_source as logistic_source"
