# -*- coding: utf-8 -*-

from logging import getLogger

from odoo import fields, models, api

_logger = getLogger(__name__)


class LoyaltyProgramExt(models.Model):
    _inherit = 'loyalty.program'

    subscription_ok = fields.Boolean(string='Subscriptions', default=False)
    limit_per_customer = fields.Boolean(string='Limit Per Customer')
    exclude_bold_customer = fields.Boolean(string='Exclude Bold Customer')
    per_customer_usage_count = fields.Integer('Apply on order')

    def filtered_domain(self, domain):
        res = super(LoyaltyProgramExt, self).filtered_domain(domain)
        valid_subscription_coupons = res
        try:
            res = super(LoyaltyProgramExt, self).filtered_domain(domain)
            current_order = self.env['sale.order'].browse(self.env.context.get('sale_order', []))
            subscription_coupons = res.filtered(
                lambda x: x.subscription_ok and x.limit_per_customer)
            valid_subscription_coupons = res
            if current_order.id and not current_order.order_line.filtered(lambda x: x.is_reward_line).ids:
                valid_subscription_coupons = valid_subscription_coupons.filtered(
                    lambda x: x.id not in subscription_coupons.ids)
                # valid_subscription_coupons = valid_subscription_coupons.filtered(
                #     lambda x: x.id not in subscription_coupons.ids)
                is_subscription_order = (current_order.is_subscription or (
                        current_order.order_line.mapped('subscription_plan_id.id') and not current_order.is_subscription))
                if all([is_subscription_order, subscription_coupons.ids]):
                    for subscription_coupon in subscription_coupons:
                        partner_orders = current_order.partner_id.sale_order_ids.filtered(
                            lambda x: x.state != 'cancel')
                        non_subscription_orders = partner_orders.filtered(
                            lambda x: not x.is_subscription)
                        if len(non_subscription_orders) == 1 or (len(
                                partner_orders.filtered(lambda x: x.is_subscription).mapped(
                                        'web_so_id')) == 1 and all(
                                [rec.state == 'sale' for rec in non_subscription_orders])):
                            valid_subscription_coupons |= subscription_coupon
            elif current_order.id and current_order.order_line.filtered(lambda x: x.is_reward_line).ids:
                if valid_subscription_coupons:
                    valid_subscription_coupons = valid_subscription_coupons[0]
        except Exception as e:
            _logger.info("Exception while filtering coupons {}".format(e))
        return valid_subscription_coupons

# class OrderDescMailingContact(models.Model):
#     _inherit = 'mailing.contact'
#
#
#     @api.model
#     def create(self, vals):
#         res = super(OrderDescMailingContact, self).create(vals)
#         # mail = self.env['mailing.contact'].sudo().search([("email", "=", self)])
#         self.env['mail.template'].sudo().browse(
#             self.env.ref('website_order_discount_tus.mail_template_desc_tus_ext').id).send_mail(self.id, force_send=True)
#         return res
