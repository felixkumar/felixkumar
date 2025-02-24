# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _upsell_context(self):
        context = super()._upsell_context()
        context["skip_procurement"] = True
        return context

    def _handle_post_invoice_hook_exception(self):
        super()._handle_post_invoice_hook_exception()
        for order in self:
            post_invoice_fail_summary = _("Delivery creation failed")
            post_invoice_fail_note = _(
                "A system error prevented the automatic creation of delivery orders for this subscription."
                " To ensure your delivery is processed, please trigger it manually by using the"
                " \"Subscription: Generate delivery\" action."
            )
            order.activity_schedule(
                activity_type_id=self.env.ref('mail.mail_activity_data_warning').id,
                summary=post_invoice_fail_summary,
                note=post_invoice_fail_note,
                user_id=order.subscription_id.user_id.id
            )
