from odoo import models, fields, api, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    walmart_instance_id = fields.Many2one('walmart.marketplace.ept', string="Walmart Marketplace",
                                          help="Walmart Marketplace")

    is_refund_in_walmart = fields.Boolean("Refund In Walmart", default=False,
                                          help="True: Refunded credit note amount in walmart store.\n False: "
                                               "Remaining to refund in Walmart Store")
    walmart_refund_id = fields.Char(help="Id of walmart refund.", copy=False)

    def get_instance_invoice(self, instance):
        invoice = self.search(
            [('state', 'in', ['posted']), ('move_type', '=', 'out_invoice'),
             ('is_move_sent', '=', False), ('walmart_instance_id', '=', instance.id)])
        for account_invoice in invoice:
            email_template = self.env.ref('account.email_template_edi_invoice', False)
            email_template.send_mail(account_invoice.id)
            account_invoice.write({'is_move_sent': True})
        return True

    def get_instance_refund_invoice(self, instance):
        invoice = self.search(
            [('state', 'in', ['posted']), ('move_type', '=', 'out_refund'),
             ('is_move_sent', '=', False), ('walmart_instance_id', '=', instance.id)])
        for account_invoice in invoice:
            email_template = self.env.ref('account.email_template_edi_invoice', False)
            email_template.send_mail(account_invoice.id)
            account_invoice.write({'is_move_sent': True})

        return True

    def action_open_refund_wizard(self):
        """This method used to open a wizard for Refund order in Walmart.
            @param : self
            @return: action
            @author: Nikul Alagiya @Emipro Technologies Pvt. Ltd on date 27/01/2022.
        """
        form_view = self.env.ref('walmart_ept.view_walmart_refund_wizard')
        context = dict(self._context)
        context.update({'active_model': 'account.invoice', 'active_id': self.id, 'active_ids': self.ids})
        return {
            'name': _('Refund order In Walmart'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'walmart.refund.order.wizard',
            'views': [(form_view.id, 'form')],
            'view_id': form_view.id,
            'target': 'new',
            'context': context
        }
