# -*- coding: utf-8 -*-

from odoo import fields, models, api


class SaleOrderExtend(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(selection_add=[('to_approve', 'To Approve')])

    service_invoice_ids = fields.Many2many("account.move", string='Invoices', readonly=True, copy=False)
    service_invoice_count = fields.Integer('Service invoice count', compute="_service_get_invoiced")

    @api.depends('service_invoice_ids')
    def _service_get_invoiced(self):
        # The invoice_ids are obtained thanks to the invoice lines of the SO
        # lines, and we also search for possible refunds created directly from
        # existing invoices. This is necessary since such a refund is not
        # directly linked to the SO.
        for order in self:
            invoices = order.service_invoice_ids
            # order.service_invoice_ids = invoices
            order.service_invoice_count = len(invoices)

    def action_view_service_invoice(self):
        service_invoices = self.mapped('service_invoice_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['domain'] = [('id', 'in', service_invoices.ids)]
        # action = {'type': 'ir.actions.act_window_close'}
        # action['context'] = context
        return action

    def button_approve(self):
        return self.with_context().action_confirm()

    def action_confirm(self):
        if self.company_id.so_double_validation == 'two_step' and self.state == 'to_approve':
            return super(SaleOrderExtend, self).action_confirm()
        elif self.company_id.so_double_validation == 'two_step':
            self.write({'state': 'to_approve'})
        else:
            return super(SaleOrderExtend, self).action_confirm()

    # def action_confirm_check_approval(self):
    #     """ Check with double validation process """
    #     for order in self:
    #         if order.so_approval_allowed():
    #             print("Check ", order.so_approval_allowed())
    #             # order.action_confirm()
    #         else:
    #             order.write({'state': 'to approve'})

    # def so_approval_allowed(self):
    #     """Returns: check whether the order qualifies to be approved by the current user"""
    #     self.ensure_one()
    #     return (
    #             self.company_id.so_double_validation == 'one_step'
    #             or (self.company_id.so_double_validation == 'two_step')
    #             or self.user_has_groups('sales_team.group_sale_manager'))
