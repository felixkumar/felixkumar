# -*- coding: utf-8 -*-
import datetime
from dateutil.relativedelta import relativedelta
from freezegun import freeze_time
from markupsafe import Markup
from unittest.mock import patch

from odoo.addons.sale_subscription.tests.common_sale_subscription import TestSubscriptionCommon
from odoo.tests import Form, tagged
from odoo.tools import mute_logger
from odoo import fields, Command
from odoo.exceptions import ValidationError, UserError


@tagged('post_install', '-at_install')
class TestSubscription(TestSubscriptionCommon):

    def flush_tracking(self):
        """ Force the creation of tracking values. """
        self.env.flush_all()
        self.cr.flush()

    def setUp(self):
        super(TestSubscription, self).setUp()
        self.env.ref('base.group_user').write({"implied_ids": [(4, self.env.ref('sale_management.group_sale_order_template').id)]})
        self.flush_tracking()

    def _get_quantities(self, order_line):
        order_line = order_line.sorted('pricing_id')
        values = {
                  'delivered_qty': order_line.mapped('qty_delivered'),
                  'qty_delivered_method': order_line.mapped('qty_delivered_method'),
                  'to_invoice': order_line.mapped('qty_to_invoice'),
                  'invoiced': order_line.mapped('qty_invoiced'),
                  }
        return values

    @mute_logger('odoo.addons.base.models.ir_model', 'odoo.models')
    def test_automatic(self):
        self.assertTrue(True)
        sub = self.subscription
        context_no_mail = {'no_reset_password': True, 'mail_create_nosubscribe': True, 'mail_create_nolog': True, }
        sub_product_tmpl = self.env['product.template'].with_context(context_no_mail).create({
            'name': 'Subscription Product',
            'type': 'service',
            'recurring_invoice': True,
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'list_price': 42
        })
        product = sub_product_tmpl.product_variant_id
        template = self.env['sale.order.template'].create({
            'name': 'Subscription template without discount',
            'recurring_rule_type': 'year',
            'recurring_rule_boundary': 'limited',
            'recurring_rule_count': 2,
            'user_closable': True,
            'auto_close_limit': 3,
            'recurrence_id': self.recurrence_month.id,
            'sale_order_template_line_ids': [Command.create({
                'name': "monthly",
                'product_id': product.id,
                'product_uom_id': product.uom_id.id
            }),
                Command.create({
                    'name': "yearly",
                    'product_id': product.id,
                    'product_uom_id': product.uom_id.id,
                })
            ]

        })
        self.company = self.env.company

        self.provider = self.env['payment.provider'].create(
            {'name': 'The Wire',
             'company_id': self.company.id,
             'state': 'test',
             'redirect_form_view_id': self.env['ir.ui.view'].search([('type', '=', 'qweb')], limit=1).id})

        sub.sale_order_template_id = template.id
        sub._onchange_sale_order_template_id()
        with freeze_time("2021-01-03"):
            sub.write({'start_date': False, 'next_invoice_date': False})
            sub.action_confirm()
            self.assertEqual(sub.invoice_count, 0)
            self.assertEqual(datetime.date(2021, 1, 3), sub.start_date, 'start date should be reset at confirmation')
            self.assertEqual(datetime.date(2021, 1, 3), sub.next_invoice_date, 'next invoice date should be updated')
            self.env['sale.order']._cron_recurring_create_invoice()
            self.assertEqual(datetime.date(2021, 2, 3), sub.next_invoice_date, 'next invoice date should be updated')
            inv = sub.invoice_ids.sorted('date')[-1]
            inv_line = inv.invoice_line_ids[0].sorted('id')[0]
            invoice_periods = inv_line.name.split('\n')[1]
            self.assertEqual(invoice_periods, "01/03/2021 to 02/02/2021")
            self.assertEqual(inv_line.date, datetime.date(2021, 1, 3))

        with freeze_time("2021-02-03"):
            self.assertEqual(sub.invoice_count, 1)
            self.env['sale.order']._cron_recurring_create_invoice()
            self.assertEqual(sub.invoice_count, 2)
            self.assertEqual(datetime.date(2021, 1, 3), sub.start_date, 'start date should not changed')
            self.assertEqual(datetime.date(2021, 3, 3), sub.next_invoice_date, 'next invoice date should be in 1 month')
            inv = sub.invoice_ids.sorted('date')[-1]
            invoice_periods = inv.invoice_line_ids[1].name.split('\n')[1]
            self.assertEqual(invoice_periods, "02/03/2021 to 03/02/2021")
            self.assertEqual(inv.invoice_line_ids[1].date, datetime.date(2021, 2, 3))

        with freeze_time("2021-03-03"):
            self.env['sale.order']._cron_recurring_create_invoice()
            self.assertEqual(datetime.date(2021, 4, 3), sub.next_invoice_date, 'next invoice date should be in 1 month')
            inv = sub.invoice_ids.sorted('date')[-1]
            invoice_periods = inv.invoice_line_ids[0].name.split('\n')[1]
            self.assertEqual(invoice_periods, "03/03/2021 to 04/02/2021")
            self.assertEqual(inv.invoice_line_ids[0].date, datetime.date(2021, 3, 3))

    @mute_logger('odoo.addons.base.models.ir_model', 'odoo.models')
    def test_template(self):
        """ Test behaviour of on_change_template """
        Subscription = self.env['sale.order']
        self.assertEqual(self.subscription.note, Markup('<p>original subscription description</p>'), "Original subscription note")
        # on_change_template on cached record (NOT present in the db)
        temp = Subscription.new({'name': 'CachedSubscription',
                                 'partner_id': self.user_portal.partner_id.id})
        temp.update({'sale_order_template_id': self.subscription_tmpl.id})
        temp._onchange_sale_order_template_id()
        self.assertEqual(temp.note, Markup('<p>This is the template description</p>'), 'Override the subscription note')

    def test_template_without_selected_partner(self):
        """ Create a subscription by choosing a template before the customer """
        with Form(self.env['sale.order']) as subscription:
            subscription.sale_order_template_id = self.subscription_tmpl
            subscription.partner_id = self.partner # mandatory to have no error

    def test_invoincing_with_section(self):
        """ Test invoicing when order has section/note."""
        context_no_mail = {'no_reset_password': True, 'mail_create_nosubscribe': True, 'mail_create_nolog': True, }

        # create specific test products
        sub_product1_tmpl = self.env['product.template'].with_context(context_no_mail).create({
            'name': 'Subscription #A',
            'type': 'service',
            'recurring_invoice': True,
            'uom_id': self.env.ref('uom.product_uom_unit').id,
        })
        sub_product1 = sub_product1_tmpl.product_variant_id
        sub_product2_tmpl = self.env['product.template'].with_context(context_no_mail).create({
            'name': 'Subscription #B',
            'type': 'service',
            'recurring_invoice': True,
            'uom_id': self.env.ref('uom.product_uom_unit').id,
        })
        sub_product2 = sub_product2_tmpl.product_variant_id
        sub_product_onetime_discount_tmpl = self.env['product.template'].with_context(context_no_mail).create({
            'name': 'Initial discount',
            'type': 'service',
            'recurring_invoice': False,
            'uom_id': self.env.ref('uom.product_uom_unit').id,
        })
        sub_product_onetime_discount = sub_product_onetime_discount_tmpl.product_variant_id

        with freeze_time("2021-01-03"):
            sub = self.env["sale.order"].with_context(**context_no_mail).create({
                'name': 'TestSubscription',
                'is_subscription': True,
                'recurrence_id': self.recurrence_month.id,
                'note': "original subscription description",
                'partner_id': self.user_portal.partner_id.id,
                'pricelist_id': self.company_data['default_pricelist'].id,
                'sale_order_template_id': self.subscription_tmpl.id,
            })
            sub._onchange_sale_order_template_id()
            sub.write({
                'start_date': False,
                'end_date': False,
                'next_invoice_date': False,
            })
            sub.order_line = [
                Command.clear(),
                Command.create({
                    'display_type': 'line_section',
                    'name': 'Products',
                }),
                Command.create({
                    'product_id': sub_product1.id,
                    'name': "Subscription #A",
                    'price_unit': 42,
                    'product_uom_qty': 2,
                    'pricing_id': self.pricing_month.id,
                }),
                Command.create({
                    'product_id': sub_product2.id,
                    'name': "Subscription #B",
                    'price_unit': 42,
                    'product_uom_qty': 2,
                    'pricing_id': self.pricing_month.id,
                }),
                Command.create({
                    'product_id': sub_product_onetime_discount.id,
                    'name': 'New subscription discount (one-time)',
                    'price_unit': -10.0,
                    'product_uom_qty': 2,
                }),
                Command.create({
                    'display_type': 'line_section',
                    'name': 'Information',
                }),
                Command.create({
                    'display_type': 'line_note',
                    'name': '...',
                }),
            ]
            sub.action_confirm()
            sub._create_recurring_invoice()

        # first invoice, it should include one-time discount
        self.assertEqual(len(sub.invoice_ids), 1)
        sub.invoice_ids._post()
        invoice = sub.invoice_ids[-1]
        self.assertEqual(invoice.amount_untaxed, 148.0)
        self.assertEqual(len(invoice.invoice_line_ids), 6)
        self.assertRecordValues(invoice.invoice_line_ids, [
            {'display_type': 'line_section', 'name': 'Products', 'product_id': False},
            {
                'display_type': 'product', 'product_id': sub_product1.id,
                'name': 'Subscription #A - 1 Month\n01/03/2021 to 02/02/2021',
            },
            {
                'display_type': 'product', 'product_id': sub_product2.id,
                'name': 'Subscription #B - 1 Month\n01/03/2021 to 02/02/2021',
            },
            {
                'display_type': 'product', 'product_id': sub_product_onetime_discount.id,
                'name': 'New subscription discount (one-time)',
            },
            {'display_type': 'line_section', 'name': 'Information', 'product_id': False},
            {'display_type': 'line_note', 'name': '...', 'product_id': False},
        ])

        with freeze_time("2021-02-03"):
            inv = sub._create_recurring_invoice()
            inv._post()

        # second invoice, should NOT include one-time discount
        self.assertEqual(len(sub.invoice_ids), 2)
        invoice = sub.invoice_ids[-1]
        self.assertEqual(invoice.amount_untaxed, 168.0)
        self.assertEqual(len(invoice.invoice_line_ids), 5)
        self.assertRecordValues(invoice.invoice_line_ids, [
            {'display_type': 'line_section', 'name': 'Products', 'product_id': False},
            {
             'display_type': 'product', 'product_id': sub_product1.id,
             'name': 'Subscription #A - 1 Month\n02/03/2021 to 03/02/2021',
            },
            {
             'display_type': 'product', 'product_id': sub_product2.id,
             'name': 'Subscription #B - 1 Month\n02/03/2021 to 03/02/2021',
            },
            {'display_type': 'line_section', 'name': 'Information', 'product_id': False},
            {'display_type': 'line_note', 'name': '...', 'product_id': False},
        ])

    @mute_logger('odoo.addons.base.models.ir_model', 'odoo.models')
    def test_unlimited_sale_order(self):
        """ Test behaviour of on_change_template """
        with freeze_time("2021-01-03"):
            sub = self.subscription
            sub.order_line = [Command.clear()]
            context_no_mail = {'no_reset_password': True, 'mail_create_nosubscribe': True, 'mail_create_nolog': True, }
            sub_product_tmpl = self.env['product.template'].with_context(context_no_mail).create({
                'name': 'Subscription Product',
                'type': 'service',
                'recurring_invoice': True,
                'uom_id': self.env.ref('uom.product_uom_unit').id,
            })
            product = sub_product_tmpl.product_variant_id
            sub.order_line = [Command.create({'product_id': product.id,
                                              'name': "coucou",
                                              'price_unit': 42,
                                              'product_uom_qty': 2,
                                              'pricing_id': self.pricing_month.id,
                                              })]
            sub.write({'start_date': False, 'next_invoice_date': False})
            sub.action_confirm()
            self.assertFalse(sub.last_invoice_date)
            self.assertEqual("2021-01-03", sub.start_date.strftime("%Y-%m-%d"))
            self.assertEqual("2021-01-03", sub.next_invoice_date.strftime("%Y-%m-%d"))

            sub._create_recurring_invoice(automatic=True)
            # Next invoice date should not be bumped up because it is the first period
            self.assertEqual("2021-02-03", sub.next_invoice_date.strftime("%Y-%m-%d"))

            invoice_periods = sub.invoice_ids.invoice_line_ids.name.split('\n')[1]
            self.assertEqual(invoice_periods, "01/03/2021 to 02/02/2021")
            self.assertEqual(sub.invoice_ids.invoice_line_ids.date, datetime.date(2021, 1, 3))
        with freeze_time("2021-02-03"):
            # February
            sub._create_recurring_invoice(automatic=True)
            self.assertEqual("2021-02-03", sub.last_invoice_date.strftime("%Y-%m-%d"))
            self.assertEqual("2021-03-03", sub.next_invoice_date.strftime("%Y-%m-%d"))
            inv = sub.invoice_ids.sorted('date')[-1]
            invoice_periods = inv.invoice_line_ids.name.split('\n')[1]
            self.assertEqual(invoice_periods, "02/03/2021 to 03/02/2021")
            self.assertEqual(inv.invoice_line_ids.date, datetime.date(2021, 2, 3))
        with freeze_time("2021-03-03"):
            # March
            sub._create_recurring_invoice(automatic=True)
            self.assertEqual("2021-03-03", sub.last_invoice_date.strftime("%Y-%m-%d"))
            self.assertEqual("2021-04-03", sub.next_invoice_date.strftime("%Y-%m-%d"))
            inv = sub.invoice_ids.sorted('date')[-1]
            invoice_periods = inv.invoice_line_ids.name.split('\n')[1]
            self.assertEqual(invoice_periods, "03/03/2021 to 04/02/2021")
            self.assertEqual(inv.invoice_line_ids.date, datetime.date(2021, 3, 3))

    @mute_logger('odoo.models.unlink')
    def test_renewal(self):
        """ Test subscription renewal """
        with freeze_time("2021-11-18"):
            self.subscription.write({
                'start_date': False,
                'next_invoice_date': False,
                'partner_invoice_id': self.partner_a_invoice.id,
                'partner_shipping_id': self.partner_a_shipping.id,
            })
            # add an so line with a different uom
            uom_dozen = self.env.ref('uom.product_uom_dozen').id
            self.subscription_tmpl.recurring_rule_count = 2 # end after 2 months to adapt to the following line
            self.subscription_tmpl.recurring_rule_type = 'month'
            self.env['sale.order.line'].create({'name': self.product.name,
                                                'order_id': self.subscription.id,
                                                'product_id': self.product3.id,
                                                'product_uom_qty': 4,
                                                'product_uom': uom_dozen,
                                                'price_unit': 42})

            self.subscription.action_confirm()
            self.subscription._create_recurring_invoice(automatic=True)
            self.assertEqual(self.subscription.end_date, datetime.date(2022, 1, 17), 'The end date of the subscription should be updated according to the template')
            self.assertFalse(self.subscription.to_renew)
            self.assertEqual(self.subscription.next_invoice_date, datetime.date(2021, 12, 18))
            self.env['account.payment.register'] \
                .with_context(active_model='account.move', active_ids=self.subscription.invoice_ids.ids) \
                .create({
                'currency_id': self.subscription.currency_id.id,
                'amount': self.subscription.amount_total,
            })._create_payments()
        self.assertTrue(self.subscription.invoice_ids.payment_state in ['in_payment', 'paid'], "the invoice is considered paid, depending on the settings.")

        with freeze_time("2021-12-18"):
            self.env['sale.order'].cron_subscription_expiration()
            self.assertTrue(self.subscription.to_renew)

            action = self.subscription.prepare_renewal_order()
            renewal_so = self.env['sale.order'].browse(action['res_id'])
            self.assertEqual(renewal_so.partner_invoice_id, self.partner_a_invoice)
            self.assertEqual(renewal_so.partner_shipping_id, self.partner_a_shipping)
            # check produt_uom_qty
            self.assertEqual(renewal_so.sale_order_template_id.id, self.subscription.sale_order_template_id.id,
                             'sale_subscription: renewal so should have the same template')

            renewal_start_date = renewal_so.start_date
            with self.assertRaises(ValidationError):
                # try to start the renewal before the parent next invoice date
                renewal_so.start_date = self.subscription.next_invoice_date - relativedelta(days=1)
                renewal_so.action_confirm()
            renewal_so.start_date = renewal_start_date
            renewal_so.action_confirm()
            self.assertFalse(self.subscription.to_renew, 'sale_subscription: confirm the renewal order should remove the to_renew flag of parent')
            self.assertEqual(self.subscription.recurring_monthly, 189, '189 = 1 + 20 + 168')
            self.assertEqual(renewal_so.subscription_management, 'renew', 'so should be set to "renew" in the renewal process')
            self.assertEqual(renewal_so.date_order.date(), self.subscription.end_date, 'renewal start date should depends on the parent end date')

            self.assertEqual(renewal_so.recurrence_id, self.recurrence_month, 'the recurrence should be propagated')
            self.assertEqual(renewal_so.next_invoice_date, datetime.date(2021, 12, 18))
            self.assertEqual(renewal_so.start_date, datetime.date(2021, 12, 18))
            self.assertTrue(renewal_so.is_subscription)

        with freeze_time("2024-11-17"):
            invoice = self.subscription._create_recurring_invoice(automatic=True)
            self.assertFalse(invoice, "Locked contract should not generate invoices")
        with freeze_time("2024-11-19"):
            self.subscription._create_recurring_invoice(automatic=True)
            renew_close_reason_id = self.env.ref('sale_subscription.close_reason_renew').id
            self.assertEqual(self.subscription.stage_category, 'closed')
            self.assertEqual(self.subscription.close_reason_id.id, renew_close_reason_id)

    def test_renewal_with_auto_done(self):
        self.env.user.groups_id += self.env.ref('sale.group_auto_done_setting')
        self.test_renewal()

    def test_upsell_via_so(self):
        # Test the upsell flow using an intermediary upsell quote.
        self.sub_product_tmpl.product_pricing_ids = [(5, 0, 0)]
        self.subscription_tmpl.sale_order_template_option_ids = [Command.create({
            'name': "Option 1",
            'product_id': self.product5.id,
            'quantity': 1,
            'uom_id': self.product5.uom_id.id,
        })]
        self.product_tmpl_2.product_pricing_ids = [(5, 0, 0)]
        self.env['product.pricing'].create({'recurrence_id': self.recurrence_month.id, 'product_template_id': self.sub_product_tmpl.id, 'price': 42})
        self.env['product.pricing'].create({'recurrence_id': self.recurrence_month.id, 'product_template_id': self.product_tmpl_2.id, 'price': 420})
        with freeze_time("2021-01-01"):
            self.subscription.order_line = False
            self.subscription.start_date = False
            self.subscription.next_invoice_date = False
            self.subscription.write({
                'partner_id': self.partner.id,
                'recurrence_id': self.recurrence_month.id,
                'partner_invoice_id': self.partner_a_invoice.id,
                'partner_shipping_id': self.partner_a_shipping.id,
                'order_line': [Command.create({'product_id': self.product.id,
                                               'name': " month cheap",
                                               'price_unit': 42,
                                               'product_uom_qty': 2,
                                               }),
                               Command.create({'product_id': self.product2.id,
                                               'name': "month expensive",
                                               'price_unit': 420,
                                               'product_uom_qty': 3,
                                               }),
                               ]
            })
            self.subscription.action_confirm()
            self.env['sale.order']._cron_recurring_create_invoice()
            self.subscription.invoice_ids.filtered(lambda am: am.state == 'draft')._post()

            self.assertEqual(self.subscription.order_line.sorted('pricing_id').mapped('product_uom_qty'), [2, 3], "Quantities should be equal to 2 and 3")
        with freeze_time("2021-01-15"):
            action = self.subscription.prepare_upsell_order()
            upsell_so = self.env['sale.order'].browse(action['res_id'])
            self.assertEqual(upsell_so.partner_invoice_id, self.partner_a_invoice)
            self.assertEqual(upsell_so.partner_shipping_id, self.partner_a_shipping)
            self.assertEqual(upsell_so.order_line.mapped('product_uom_qty'), [0, 0, 0], 'The upsell order has 0 quantity')
            note = upsell_so.order_line.filtered('display_type')
            self.assertEqual(note.name, 'Recurring product are discounted according to the prorated period from 01/15/2021 to 01/31/2021')

            upsell_so.order_line.filtered(lambda l: not l.display_type).product_uom_qty = 1
            # When the upsell order is created, all quantities are equal to 0
            # add line to quote manually, it must be taken into account in the subscription after validation
            upsell_so.order_line = [(0, 0, {
                'name': self.product2.name,
                'order_id': upsell_so.id,
                'product_id': self.product2.id,
                'product_uom_qty': 2,
                'product_uom': self.product2.uom_id.id,
                'price_unit': self.product2.list_price,
            }), (0, 0, {
                'name': self.product3.name,
                'order_id': upsell_so.id,
                'product_id': self.product3.id,
                'product_uom_qty': 1,
                'product_uom': self.product3.uom_id.id,
                'price_unit': self.product3.list_price,
            })]
            upsell_so.action_confirm()
            # We make sure that two confirmation won't add twice the same quantities
            upsell_so.action_confirm()
            self.env['sale.order']._cron_recurring_create_invoice()
            self.subscription.invoice_ids.filtered(lambda am: am.state == 'draft')._post()
            discounts = [round(v, 2) for v in upsell_so.order_line.sorted('discount').mapped('discount')]
            self.assertEqual(discounts, [0.0, 45.16, 45.16, 45.16, 45.16], 'Prorated prices should be applied')
            prices = [round(v, 2) for v in upsell_so.order_line.sorted('pricing_id').mapped('price_subtotal')]
            self.assertEqual(prices, [0.0, 23.03, 23.03, 230.33, 21.94], 'Prorated prices should be applied')

        with freeze_time("2021-02-01"):
            self.env['sale.order']._cron_recurring_create_invoice()
            self.subscription.invoice_ids.filtered(lambda am: am.state == 'draft')._post()

        with freeze_time("2021-03-01"):
            self.env['sale.order']._cron_recurring_create_invoice()
            upsell_so._create_invoices()
            self.subscription.invoice_ids.filtered(lambda am: am.state == 'draft')._post()
            sorted_lines = self.subscription.order_line.sorted('pricing_id')
            self.assertEqual(sorted_lines.mapped('product_uom_qty'), [1.0, 3.0, 4.0, 2.0], "Quantities should be equal to 1.0, 3.0, 4.0, 2.0")

        with freeze_time("2021-04-01"):
            self.env['sale.order']._cron_recurring_create_invoice()
            self.subscription.invoice_ids.filtered(lambda am: am.state == 'draft')._post()
        with freeze_time("2021-05-01"):
            self.env['sale.order']._cron_recurring_create_invoice()
            self.subscription.invoice_ids.filtered(lambda am: am.state == 'draft')._post()
        with freeze_time("2021-06-01"):
            self.env['sale.order']._cron_recurring_create_invoice()
            self.subscription.invoice_ids.filtered(lambda am: am.state == 'draft')._post()
        with freeze_time("2021-07-01"):
            self.env['sale.order']._cron_recurring_create_invoice()
            self.subscription.invoice_ids.filtered(lambda am: am.state == 'draft')._post()
        with freeze_time("2021-08-01"):
            self.env['sale.order']._cron_recurring_create_invoice()
            self.subscription.invoice_ids.filtered(lambda am: am.state == 'draft')._post()
            inv = self.subscription.invoice_ids.sorted('date')[-1]
            invoice_periods = inv.invoice_line_ids.sorted('id').mapped('name')
            first_period = invoice_periods[0].split('\n')[1]
            self.assertEqual(first_period, "08/01/2021 to 08/31/2021")
            second_period = invoice_periods[1].split('\n')[1]
            self.assertEqual(second_period, "08/01/2021 to 08/31/2021")

        self.assertEqual(len(self.subscription.order_line), 4)

    def test_upsell_prorata(self):
        """ Test the prorated values obtained when creating an upsell. complementary to the previous one where new
         lines had no existing default values.
        """
        self.env['product.pricing'].create({'recurrence_id': self.recurrence_2_month.id, 'product_template_id': self.sub_product_tmpl.id, 'price': 42})
        self.env['product.pricing'].create(
            {'recurrence_id': self.recurrence_2_month.id, 'product_template_id': self.product_tmpl_2.id, 'price': 42})
        with freeze_time("2021-01-01"):
            self.subscription.order_line = False
            self.subscription.start_date = False
            self.subscription.next_invoice_date = False
            self.subscription.write({
                'partner_id': self.partner.id,
                'recurrence_id': self.recurrence_2_month.id,
                'order_line': [
                    Command.create({
                        'product_id': self.product.id,
                        'name': "month: original",
                        'price_unit': 50,
                        'product_uom_qty': 1,
                    }),
                    Command.create({
                        'product_id': self.product2.id,
                        'name': "2 month: original",
                        'price_unit': 50,
                        'product_uom_qty': 1,
                    }),
                ]
            })

            self.subscription.action_confirm()
            self.subscription._create_recurring_invoice(automatic=True)

        with freeze_time("2021-01-20"):
            action = self.subscription.prepare_upsell_order()
            upsell_so = self.env['sale.order'].browse(action['res_id'])
            # Create new lines that should be aligned with existing ones
            so_line_vals = [{
                'name': 'Upsell added: 1 month',
                'order_id': upsell_so.id,
                'product_id': self.product2.id,
                'product_uom_qty': 1,
                'product_uom': self.product2.uom_id.id,
                'price_unit': self.product.list_price,
            }, {
                'name': 'Upsell added: 2 month',
                'order_id': upsell_so.id,
                'product_id': self.product3.id,
                'product_uom_qty': 1,
                'product_uom': self.product3.uom_id.id,
                'price_unit': self.product3.list_price,
            }]
            self.env['sale.order.line'].create(so_line_vals)
            upsell_so.order_line.product_uom_qty = 1
            discounts = [round(v) for v in upsell_so.order_line.sorted('discount').mapped('discount')]
            # discounts for: 40/59 days
            self.assertEqual(discounts, [0, 32, 32, 32, 32], 'Prorated prices should be applied')
            self.assertEqual(self.subscription.order_line.ids, upsell_so.order_line.parent_line_id.ids,
                             "The parent line id should correspond to the first two lines")
            # discounts for: 12d/31d; 40d/59d; 21d/31d (shifted); 31d/41d; 59d/78d;
            self.assertEqual(discounts, [0, 32, 32, 32, 32], 'Prorated prices should be applied')
            prices = [round(v, 2) for v in upsell_so.order_line.sorted('pricing_id').mapped('price_subtotal')]
            self.assertEqual(prices, [0.0, 28.48, 28.48, 28.48, 28.48], 'Prorated prices should be applied')

    def test_recurring_revenue(self):
        """Test computation of recurring revenue"""
        # Initial subscription is $100/y
        self.subscription_tmpl.write({'recurring_rule_count': 1, 'recurring_rule_type': 'year'})
        self.subscription.write({
            'recurrence_id': self.recurrence_2_month.id,
            'start_date': False,
            'next_invoice_date': False,
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'payment_token_id': self.payment_method.id,
        })
        self.subscription.order_line[0].write({'price_unit': 1200})
        self.subscription.order_line[1].write({'price_unit': 200})
        self.subscription.action_confirm()
        self.assertAlmostEqual(self.subscription.amount_untaxed, 1400, msg="unexpected price after setup")
        self.assertAlmostEqual(self.subscription.recurring_monthly, 700, msg="Half because invoice every two months")
        # Change periodicity
        self.subscription.order_line.product_id.product_pricing_ids = [(6, 0, 0)] # remove all pricings to fallaback on list price
        self.subscription.recurrence_id = self.recurrence_year.id
        self.assertAlmostEqual(self.subscription.amount_untaxed, 70, msg='Recompute price_unit : 50 (product) + 20 (product2)')
        # 1200 over 4 year = 25/year + 100 per month
        self.assertAlmostEqual(self.subscription.recurring_monthly, 5.84, msg='70 / 12')

    def test_compute_kpi(self):
        self.subscription_tmpl.write({'good_health_domain': "[('recurring_monthly', '>=', 120.0)]",
                                      'bad_health_domain': "[('recurring_monthly', '<=', 80.0)]",
                                      })
        self.subscription.recurring_monthly = 80.0
        self.subscription.action_confirm()
        self.env['sale.order']._cron_update_kpi()
        self.assertEqual(self.subscription.health, 'bad')

        # 16 to 6 weeks: 80
        # 6 to 2 weeks: 100
        # 2weeks - today : 120
        date_log = datetime.date.today() - relativedelta(weeks=16)
        self.env['sale.order.log'].sudo().create({
            'event_type': '1_change',
            'event_date': date_log,
            'create_date': date_log,
            'order_id': self.subscription.id,
            'recurring_monthly': 80,
            'amount_signed': 80,
            'currency_id': self.subscription.currency_id.id,
            'category': self.subscription.stage_category,
            'user_id': self.subscription.user_id.id,
            'team_id': self.subscription.team_id.id,
        })

        date_log = datetime.date.today() - relativedelta(weeks=6)
        self.env['sale.order.log'].sudo().create({
            'event_type': '1_change',
            'event_date': date_log,
            'create_date': date_log,
            'order_id': self.subscription.id,
            'recurring_monthly': 100,
            'amount_signed': 20,
            'currency_id': self.subscription.currency_id.id,
            'category': self.subscription.stage_category,
            'user_id': self.subscription.user_id.id,
            'team_id': self.subscription.team_id.id,
         })

        self.subscription.recurring_monthly = 120.0
        date_log = datetime.date.today() - relativedelta(weeks=2)
        self.env['sale.order.log'].sudo().create({
            'event_type': '1_change',
            'event_date': date_log,
            'create_date': date_log,
            'order_id': self.subscription.id,
            'recurring_monthly': 120,
            'amount_signed': 20,
            'currency_id': self.subscription.currency_id.id,
            'category': self.subscription.stage_category,
            'user_id': self.subscription.user_id.id,
            'team_id': self.subscription.team_id.id,
        })
        self.subscription._cron_update_kpi()
        self.assertEqual(self.subscription.kpi_1month_mrr_delta, 20.0)
        self.assertEqual(self.subscription.kpi_1month_mrr_percentage, 0.2)
        self.assertEqual(self.subscription.kpi_3months_mrr_delta, 40.0)
        self.assertEqual(self.subscription.kpi_3months_mrr_percentage, 0.5)
        self.assertEqual(self.subscription.health, 'done')

    def test_onchange_date_start(self):
        recurring_bound_tmpl = self.env['sale.order.template'].create({
            'name': 'Recurring Bound Template',
            'recurrence_id': self.recurrence_month.id,
            'recurring_rule_boundary': 'limited',
            'recurring_rule_type': 'month',
            'recurring_rule_count': 3,
            'sale_order_template_line_ids': [Command.create({
                'name': "monthly",
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'product_uom_id': self.product.uom_id.id
            })]
        })
        sub_form = Form(self.env['sale.order'])
        sub_form.partner_id = self.user_portal.partner_id
        sub_form.sale_order_template_id = recurring_bound_tmpl
        sub = sub_form.save()
        sub._onchange_sale_order_template_id()
        # The end date is set upon confirmation
        sub.action_confirm()
        self.assertEqual(sub.sale_order_template_id.recurring_rule_boundary, 'limited')
        self.assertIsInstance(sub.end_date, datetime.date)

    def test_changed_next_invoice_date(self):
        # Test wizard to change next_invoice_date manually
        with freeze_time("2022-01-01"):
            self.subscription.write({'start_date': False, 'next_invoice_date': False})
            self.env['sale.order.line'].create({
                'name': self.product2.name,
                'order_id': self.subscription.id,
                'product_id': self.product2.id,
                'product_uom_qty': 3,
                'product_uom': self.product2.uom_id.id,
                'price_unit': 42})

            self.subscription.action_confirm()
            self.subscription._create_recurring_invoice(automatic=True)
            today = fields.Date.today()
            self.assertEqual(self.subscription.start_date, today, "start date should be set to today")
            self.assertEqual(self.subscription.next_invoice_date, datetime.date(2022, 2, 1))
            # We decide to invoice the monthly subscription on the 5 of february
            self.subscription.next_invoice_date = fields.Date.from_string('2022-02-05')

        with freeze_time("2022-02-01"):
            # Nothing should be invoiced
            self.subscription._cron_recurring_create_invoice()
            # next_invoice_date : 2022-02-5 but the previous invoice subscription_end_date was set on the 2022-02-01
            # We can't prevent it to be re-invoiced.
            inv = self.subscription.invoice_ids.sorted('date')
            # Nothing was invoiced
            self.assertEqual(inv.date, datetime.date(2022, 1, 1))

        with freeze_time("2022-02-05"):
            self.subscription._cron_recurring_create_invoice()
            inv = self.subscription.invoice_ids.sorted('date')
            self.assertEqual(inv[-1].date, datetime.date(2022, 2, 5))

    def test_product_change(self):
        """Check behaviour of the product onchange (taxes mostly)."""
        # check default tax
        self.sub_product_tmpl.product_pricing_ids = [(6, 0, self.pricing_month.ids)]
        self.pricing_month.price = 50

        self.subscription.order_line.unlink()
        sub_form = Form(self.subscription)
        sub_form.recurrence_id = self.recurrence_month
        with sub_form.order_line.new() as line:
            line.product_id = self.product
        sub = sub_form.save()
        self.assertEqual(sub.order_line.product_id.taxes_id, self.tax_10, 'Default tax for product should have been applied.')
        self.assertEqual(sub.amount_tax, 5.0,
                         'Default tax for product should have been applied.')
        self.assertEqual(sub.amount_total, 55.0,
                         'Default tax for product should have been applied.')
        # Change the product
        line_id = sub.order_line.ids
        sub.write({
            'order_line': [(1, line_id[0], {'product_id': self.product4.id})]
        })
        self.assertEqual(sub.order_line.product_id.taxes_id, self.tax_20,
                         'Default tax for product should have been applied.')
        self.assertEqual(sub.amount_tax, 3,
                         'Default tax for product should have been applied.')
        self.assertEqual(sub.amount_total, 18,
                         'Default tax for product should have been applied.')

    def test_log_change_pricing(self):
        """ Test subscription log generation when template_id is changed """
        self.sub_product_tmpl.product_pricing_ids.price = 120 # 120 for monthly and yearly
        # Create a subscription and add a line, should have logs with MMR 120
        subscription = self.env['sale.order'].create({
            'name': 'TestSubscription',
            'start_date': False,
            'next_invoice_date': False,
            'recurrence_id': self.recurrence_month.id,
            'partner_id': self.user_portal.partner_id.id,
            'pricelist_id': self.env.ref('product.list0').id,
            'sale_order_template_id': self.subscription_tmpl.id,
        })
        self.cr.precommit.clear()
        subscription.write({'order_line': [(0, 0, {
            'name': 'TestRecurringLine',
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'product_uom': self.product.uom_id.id})]})
        subscription.action_confirm()
        self.flush_tracking()
        init_nb_log = len(subscription.order_log_ids)
        self.assertEqual(subscription.order_line.recurring_monthly, 120)
        subscription.recurrence_id = self.recurrence_year.id
        self.assertEqual(subscription.order_line.recurring_monthly, 10)
        self.flush_tracking()
        # Should get one more log with MRR 10 (so change is -110)
        self.assertEqual(len(subscription.order_log_ids), init_nb_log + 1,
                         "Subscription log not generated after change of the subscription template")
        self.assertRecordValues(subscription.order_log_ids[-1],
                                [{'recurring_monthly': 10.0, 'amount_signed': -110}])

    def test_fiscal_position(self):
        # Test that the fiscal postion FP is applied on recurring invoice.
        # FP must mapped an included tax of 21% to an excluded one of 0%
        tax_include_id = self.env['account.tax'].create({'name': "Include tax",
                                                         'amount': 21.0,
                                                         'price_include': True,
                                                         'type_tax_use': 'sale'})
        tax_exclude_id = self.env['account.tax'].create({'name': "Exclude tax",
                                                         'amount': 0.0,
                                                         'type_tax_use': 'sale'})

        product_tmpl = self.env['product.template'].create(dict(name="Voiture",
                                                                list_price=121,
                                                                taxes_id=[(6, 0, [tax_include_id.id])]))

        fp = self.env['account.fiscal.position'].create({'name': "fiscal position",
                                                         'sequence': 1,
                                                         'auto_apply': True,
                                                         'tax_ids': [(0, 0, {'tax_src_id': tax_include_id.id,
                                                                             'tax_dest_id': tax_exclude_id.id})]})
        self.subscription.fiscal_position_id = fp.id
        self.subscription.partner_id.property_account_position_id = fp
        sale_order = self.env['sale.order'].create({
            'name': 'TestSubscription',
            'fiscal_position_id': fp.id,
            'partner_id': self.user_portal.partner_id.id,
            'pricelist_id': self.company_data['default_pricelist'].id,
            'order_line': [Command.create({
                'product_id': product_tmpl.product_variant_id.id,
                'product_uom': self.env.ref('uom.product_uom_unit').id,
                'product_uom_qty': 1
            })]
        })
        sale_order.action_confirm()
        inv = sale_order._create_invoices()
        self.assertEqual(100, inv.invoice_line_ids[0].price_unit, "The included tax must be subtracted to the price")

    def test_quantity_on_product_invoice_ordered_qty(self):
        # This test checks that the invoiced qty and to_invoice qty have the right behavior
        # Service product
        self.product.write({
            'detailed_type': 'service'
        })
        with freeze_time("2021-01-01"):
            self.subscription.order_line = False
            self.subscription.write({
                'start_date': False,
                'next_invoice_date': False,
                'recurrence_id': self.recurrence_month.id,
                'partner_id': self.partner.id,
                'order_line': [Command.create({'product_id': self.product.id,
                                               'price_unit': 42,
                                               'product_uom_qty': 1,
                                               }),
                               Command.create({'product_id': self.product2.id,
                                               'price_unit': 420,
                                               'product_uom_qty': 3,
                                               }),
                               ]
            })
            self.subscription.action_confirm()
            val_confirm = self._get_quantities(self.subscription.order_line)
            self.assertEqual(val_confirm['to_invoice'], [3, 1], "To invoice should be equal to quantity")
            self.assertEqual(val_confirm['invoiced'], [0, 0], "To invoice should be equal to quantity")
            self.assertEqual(val_confirm['delivered_qty'], [0, 0], "Delivered qty not should be set")
            self.env['sale.order']._cron_recurring_create_invoice()
            self.subscription.order_line[0].write({'qty_delivered': 1})
            self.subscription.order_line[1].write({'qty_delivered': 3})
            val_invoice = self._get_quantities(self.subscription.order_line.sorted('id'))
            self.assertEqual(val_invoice['to_invoice'], [0, 0], "To invoice should be 0")
            self.assertEqual(val_invoice['invoiced'], [3, 1], "To invoice should be equal to quantity")
            self.assertEqual(val_invoice['delivered_qty'], [3, 1], "Delivered qty should be set")

        with freeze_time("2021-02-02"):
            self.env['sale.order']._cron_recurring_create_invoice()
            val_invoice = self._get_quantities(self.subscription.order_line)
            self.assertEqual(val_invoice['to_invoice'], [0, 0], "To invoice should be 0")
            self.assertEqual(val_invoice['invoiced'], [3, 1], "To invoice should be equal to quantity")
            self.assertEqual(val_invoice['delivered_qty'], [3, 1], "Delivered qty should be equal to quantity")

        with freeze_time("2021-02-15"):
            self.subscription.order_line[0].write({'qty_delivered': 3, 'product_uom_qty': 3})
            val_invoice = self._get_quantities(
                self.subscription.order_line
            )
            self.assertEqual(val_invoice['to_invoice'], [0, 2], "To invoice should be equal to quantity")
            self.assertEqual(val_invoice['invoiced'], [3, 1], "invoiced should be correct")
            self.assertEqual(val_invoice['delivered_qty'], [3, 3], "Delivered qty should be equal to quantity")

        with freeze_time("2021-03-01"):
            self.env['sale.order']._cron_recurring_create_invoice()
            self.env.invalidate_all()
            val_invoice = self._get_quantities(self.subscription.order_line)
            self.assertEqual(val_invoice['to_invoice'], [0, 0], "To invoice should be equal to quantity")
            self.assertEqual(val_invoice['delivered_qty'], [3, 3], "Delivered qty should be equal to quantity")
            self.assertEqual(val_invoice['invoiced'], [3, 3], "To invoice should be equal to quantity delivered")

    def test_update_prices_template(self):
        recurring_bound_tmpl = self.env['sale.order.template'].create({
            'name': 'Subscription template without discount',
            'recurring_rule_type': 'year',
            'recurring_rule_boundary': 'limited',
            'recurring_rule_count': 2,
            'recurrence_id': self.recurrence_month.id,
            'note': "This is the template description",
            'auto_close_limit': 5,
            'sale_order_template_line_ids': [
                Command.create({
                    'name': "monthly",
                    'product_id': self.product.id,
                    'product_uom_id': self.product.uom_id.id
                }),
                Command.create({
                    'name': "yearly",
                    'product_id': self.product.id,
                    'product_uom_id': self.product.uom_id.id,
                }),
            ],
            'sale_order_template_option_ids': [
                Command.create({
                    'name': "option",
                    'product_id': self.product.id,
                    'quantity': 1,
                    'uom_id': self.product2.uom_id.id
                }),
            ],
        })

        sub_form = Form(self.env['sale.order'])
        sub_form.partner_id = self.user_portal.partner_id
        sub_form.sale_order_template_id = recurring_bound_tmpl
        sub = sub_form.save()
        self.assertEqual(len(sub.order_line.ids), 2)

    def test_product_invoice_delivery(self):
        sub = self.subscription
        sub.order_line = [Command.clear()]
        context_no_mail = {'no_reset_password': True, 'mail_create_nosubscribe': True, 'mail_create_nolog': True, }
        delivered_product_tmpl = self.env['product.template'].with_context(context_no_mail).create({
            'name': 'Delivery product',
            'type': 'service',
            'recurring_invoice': True,
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'invoice_policy': 'delivery',
        })
        product = delivered_product_tmpl.product_variant_id
        product.write({
            'list_price': 50.0,
            'taxes_id': [(6, 0, [self.tax_10.id])],
            'property_account_income_id': self.account_income.id,
        })

        with freeze_time("2021-01-03"):
            # January
            sub.recurrence_id = self.recurrence_month.id
            sub.start_date = False
            sub.next_invoice_date = False
            sub.order_line = [Command.create({'product_id': product.id,
                                              'name': "coucou",
                                              'price_unit': 42,
                                              'product_uom_qty': 1,
                                              })]
            sub.action_confirm()
            sub._create_recurring_invoice(automatic=True)
            self.assertFalse(sub.order_line.qty_delivered)
            # We only invoice what we deliver
            self.assertFalse(sub.order_line.qty_to_invoice)
            self.assertFalse(sub.invoice_count, "We don't invoice if we don't deliver the product")
            # Deliver some product
            sub.order_line.qty_delivered = 1
            self.assertEqual(sub.order_line.qty_to_invoice, 1)
            sub._create_recurring_invoice(automatic=False)
            self.assertTrue(sub.invoice_count, "We should have invoiced")
            self.assertEqual(sub.next_invoice_date, datetime.date(2021, 2, 3))
            sub.order_line.invoice_lines.move_id._post()

        with freeze_time("2021-02-03"):
            sub._create_recurring_invoice(automatic=True)
            # The quantity to invoice and delivered are reset after the creation of the invoice
            self.assertTrue(sub.order_line.qty_delivered)
            inv = sub.invoice_ids.sorted('date')[-1]
            self.assertEqual(inv.invoice_line_ids.quantity, 1)

        with freeze_time("2021-03-03"):
            # February
            sub.order_line.qty_delivered = 1
            sub._create_recurring_invoice(automatic=True)
            self.assertEqual(sub.order_line.qty_delivered, 1)
            inv = sub.invoice_ids.sorted('date')[-1]
            self.assertEqual(inv.invoice_line_ids.quantity, 1)

        with freeze_time("2021-04-03"):
            # March
            sub.order_line.qty_delivered = 2
            inv = sub._create_recurring_invoice(automatic=True)
            self.assertEqual(inv.invoice_line_ids.quantity, 2)
            self.assertEqual(sub.order_line.product_uom_qty, 1)

    def test_recurring_invoices_from_interface(self):
        # From the interface, all the subscription lines are invoiced
        sub = self.subscription
        sub.end_date = datetime.date(2029, 4, 1)
        with freeze_time("2021-01-01"):
            self.subscription.write({'start_date': False, 'next_invoice_date': False, 'recurrence_id': self.recurrence_month.id})
            sub.action_confirm()
            # first invoice: automatic or not, it's the same behavior. All line are invoiced
            sub._create_recurring_invoice(automatic=False)
            sub.order_line.invoice_lines.move_id._post()
            self.assertEqual("2021-02-01", sub.next_invoice_date.strftime("%Y-%m-%d"))
            inv = sub.invoice_ids.sorted('date')[-1]
            invoice_start_periods = inv.invoice_line_ids.mapped('subscription_start_date')
            invoice_end_periods = inv.invoice_line_ids.mapped('subscription_end_date')
            self.assertEqual(invoice_start_periods, [datetime.date(2021, 1, 1), datetime.date(2021, 1, 1)])
            self.assertEqual(invoice_end_periods, [datetime.date(2021, 1, 31), datetime.date(2021, 1, 31)])
        with freeze_time("2021-02-01"):
            sub._create_recurring_invoice(automatic=False)
            sub.invoice_ids.filtered(lambda am: am.state == 'draft')._post()
            self.assertEqual("2021-03-01", sub.next_invoice_date.strftime("%Y-%m-%d"), "Next invoice date should be updated")
            inv = sub.invoice_ids.sorted('date')[-1]
            invoice_start_periods = inv.invoice_line_ids.mapped('subscription_start_date')
            invoice_end_periods = inv.invoice_line_ids.mapped('subscription_end_date')
            self.assertEqual(invoice_start_periods, [datetime.date(2021, 2, 1), datetime.date(2021, 2, 1)], "monthly is updated everytime in manual action")
            self.assertEqual(invoice_end_periods, [datetime.date(2021, 2, 28), datetime.date(2021, 2, 28)], "both lines are invoiced")
            draft_invoice = sub._create_recurring_invoice()
            with self.assertRaisesRegex(ValidationError, 'The following recurring orders have draft invoices.*'):
                sub._create_invoices()

            draft_invoice._post()
            inv = sub.invoice_ids.sorted('id')[-1]
            self.assertEqual("2021-04-01", sub.next_invoice_date.strftime("%Y-%m-%d"))
            invoice_start_periods = inv.invoice_line_ids.mapped('subscription_start_date')
            invoice_end_periods = inv.invoice_line_ids.mapped('subscription_end_date')
            self.assertEqual(invoice_start_periods, [datetime.date(2021, 3, 1), datetime.date(2021, 3, 1)], "monthly is updated everytime in manual action")
            self.assertEqual(invoice_end_periods, [datetime.date(2021, 3, 31), datetime.date(2021, 3, 31)], "monthly is updated everytime in manual action")

        with freeze_time("2021-04-01"):
            # Automatic invoicing, only one line generated
            sub._create_recurring_invoice(automatic=True)
            inv = sub.invoice_ids.sorted('date')[-1]
            invoice_start_periods = inv.invoice_line_ids.mapped('subscription_start_date')
            invoice_end_periods = inv.invoice_line_ids.mapped('subscription_end_date')
            self.assertEqual(invoice_start_periods, [datetime.date(2021, 4, 1), datetime.date(2021, 4, 1)], "Monthly is updated because it is due")
            self.assertEqual(invoice_end_periods, [datetime.date(2021, 4, 30), datetime.date(2021, 4, 30)], "Monthly is updated because it is due")
            self.assertEqual(inv.date, datetime.date(2021, 4, 1))

        with freeze_time("2021-05-01"):
            # Automatic invoicing, only one line generated
            sub._create_recurring_invoice(automatic=True)
            inv = sub.invoice_ids.sorted('date')[-1]
            invoice_start_periods = inv.invoice_line_ids.mapped('subscription_start_date')
            invoice_end_periods = inv.invoice_line_ids.mapped('subscription_end_date')
            self.assertEqual(invoice_start_periods, [datetime.date(2021, 5, 1), datetime.date(2021, 5, 1)], "Monthly is updated because it is due")
            self.assertEqual(invoice_end_periods, [datetime.date(2021, 5, 31), datetime.date(2021, 5, 31)], "Monthly is updated because it is due")
            self.assertEqual(inv.date, datetime.date(2021, 5, 1))

        with freeze_time("2022-02-02"):
            # We prevent the subscription to be automatically closed because the next invoice date is passed for too long
            sub.sale_order_template_id.auto_close_limit = 999
            # With non-automatic, we invoice all line prior to today once
            inv = sub._create_recurring_invoice(automatic=False)
            inv._post()
            self.assertEqual("2021-07-01", sub.next_invoice_date.strftime("%Y-%m-%d"), "on the 1st of may, nid is updated to 1fst of june and here we force the line to be apdated again")
            inv = sub.invoice_ids.sorted('date')[-1]
            invoice_start_periods = inv.invoice_line_ids.mapped('subscription_start_date')
            invoice_end_periods = inv.invoice_line_ids.mapped('subscription_end_date')
            self.assertEqual(invoice_start_periods, [datetime.date(2021, 6, 1), datetime.date(2021, 6, 1)], "monthly is updated when prior to today")
            self.assertEqual(invoice_end_periods, [datetime.date(2021, 6, 30), datetime.date(2021, 6, 30)], "monthly is updated when prior to today")

    def test_renew_kpi_mrr(self):
        # Test that renew with MRR transfer give correct result
        # First, whe create a sub with MRR = 21
        # Then we renew it with a MRR of 42
        # After a few months the MRR of the renewal is 63
        # We also create and renew a free subscription
        SaleOrder = self.env["sale.order"]
        with freeze_time("2021-01-01"), patch.object(type(SaleOrder), '_get_unpaid_subscriptions', lambda x: []):
            self.subscription_tmpl.auto_close_limit = 5000 # don't close automatically contract if unpaid invoices
            # so creation with mail tracking
            context_mail = {'tracking_disable': False}
            sub = self.env['sale.order'].with_context(context_mail).create({
                'name': 'TestSubscription',
                'is_subscription': True,
                'note': "original subscription description",
                'partner_id': self.user_portal.partner_id.id,
                'pricelist_id': self.company_data['default_pricelist'].id,
                'sale_order_template_id': self.subscription_tmpl.id,
            })
            free_sub = self.env['sale.order'].with_context(context_mail).create({
                'name': 'Parent Sub',
                'is_subscription': True,
                'note': "original subscription description",
                'partner_id': self.user_portal.partner_id.id,
                'pricelist_id': self.company_data['default_pricelist'].id,
                'recurrence_id': self.recurrence_month.id,
                'order_line': [
                    (0, 0, {
                        'name': self.product.name,
                        'product_id': self.product.id,
                        'product_uom_qty': 3.0,
                        'product_uom': self.product.uom_id.id,
                        'price_unit': 0,
                    })],
            })

            future_sub = self.env['sale.order'].with_context(context_mail).create({
                'name': 'FutureSub',
                'is_subscription': True,
                'note': "original subscription description",
                'partner_id': self.user_portal.partner_id.id,
                'pricelist_id': self.company_data['default_pricelist'].id,
                'recurrence_id': self.recurrence_month.id,
                'start_date': '2021-06-01',
                'order_line': [
                    (0, 0, {
                        'name': self.product.name,
                        'product_id': self.product.id,
                        'product_uom_qty': 1.0,
                        'product_uom': self.product.uom_id.id,
                    })],
            })

            self.assertFalse(free_sub.amount_total)
            self.flush_tracking()
            sub._onchange_sale_order_template_id()
            # Same product for both lines
            sub.order_line.product_uom_qty = 1
            (free_sub | sub).end_date = datetime.date(2022, 1, 1)
            (free_sub | sub | future_sub).action_confirm()
            self.flush_tracking()
            self.assertEqual(sub.recurring_monthly, 21, "20 + 1 for both lines")
            self.env['sale.order'].with_context(tracking_disable=False)._cron_recurring_create_invoice()
        with freeze_time("2021-02-01"):
            self.env['sale.order'].with_context(tracking_disable=False)._cron_recurring_create_invoice()
        with freeze_time("2021-03-01"):
            self.env['sale.order'].with_context(tracking_disable=False)._cron_recurring_create_invoice()
        with freeze_time("2021-04-01"):
            # We create a renewal order in april for the new year
            self.env['sale.order']._cron_recurring_create_invoice()
            action = sub.with_context(tracking_disable=False).prepare_renewal_order()
            renewal_so = self.env['sale.order'].browse(action['res_id'])
            renewal_so = renewal_so.with_context(tracking_disable=False)
            renewal_so.order_line.product_uom_qty = 3
            renewal_so.name = "Renewal"
            action = free_sub.with_context(tracking_disable=False).prepare_renewal_order()
            free_renewal_so = self.env['sale.order'].browse(action['res_id'])
            free_renewal_so = free_renewal_so.with_context(tracking_disable=False)
            free_renewal_so.order_line.write({'product_uom_qty': 2, 'price_unit': 0})
            (renewal_so | free_renewal_so).action_confirm()
            # Most of the time, the renewal invoice is created by the salesman
            # before the renewal start date
            renewal_invoices = (free_renewal_so|renewal_so)._create_invoices()
            renewal_invoices._post()
            # "upsell" of the simple sub that did not start yet
            future_sub.order_line.product_uom_qty = 4

            self.flush_tracking()
            self.assertEqual(sub.recurring_monthly, 21, "The first SO is still valid")
            self.assertTrue(sub.recurring_live)
            self.assertTrue(free_sub.recurring_live)
            self.assertFalse(renewal_so.recurring_live)
            self.assertEqual(renewal_so.recurring_monthly, 63, "MRR of renewal should not be computed before start_date of the lines")
            self.flush_tracking()
            # renew is still not ongoing;  Total MRR is 21 coming from the original sub
            self.env['sale.order'].sudo().cron_subscription_expiration()
            self.assertEqual(sub.recurring_monthly, 21)
            self.assertEqual(renewal_so.recurring_monthly, 63)
            self.env['sale.order']._cron_recurring_create_invoice()
            self.flush_tracking()
            self.subscription._cron_update_kpi()
            self.assertEqual(sub.kpi_1month_mrr_delta, 0)
            self.assertEqual(sub.kpi_1month_mrr_percentage, 0)
            self.assertEqual(sub.kpi_3months_mrr_delta, 0)
            self.assertEqual(sub.kpi_3months_mrr_percentage, 0)
            self.assertEqual(sub.stage_category, 'progress')

        with freeze_time("2021-05-05"): # We switch the cron the X of may to make sure the day of the cron does not affect the numbers
            # Renewal period is from 2021-05 to 2021-06
            self.env['sale.order']._cron_recurring_create_invoice()
            self.assertEqual(sub.recurring_monthly, 0)
            self.assertEqual(sub.stage_category, 'closed')
            self.assertFalse(sub.recurring_live)
            self.assertFalse(free_sub.recurring_live)
            self.assertEqual(renewal_so.next_invoice_date, datetime.date(2021, 6, 1))
            self.assertEqual(renewal_so.recurring_monthly, 63)
            self.assertTrue(renewal_so.recurring_live)
            self.assertTrue(free_renewal_so.recurring_live)
            self.flush_tracking()

        with freeze_time("2021-05-15"):
            self.env['sale.order']._cron_recurring_create_invoice()
            sub.order_line._compute_recurring_monthly()
            self.flush_tracking()

        with freeze_time("2021-06-01"):
            self.subscription._cron_update_kpi()
            self.env['sale.order']._cron_recurring_create_invoice()
            self.assertEqual(sub.recurring_monthly, 0)
            self.assertEqual(renewal_so.recurring_monthly, 63)
            self.flush_tracking()

        with freeze_time("2021-07-01"), patch.object(type(SaleOrder), '_get_unpaid_subscriptions', lambda x: []):
            # Total MRR is 42 coming from renew
            self.subscription._cron_update_kpi()
            self.env['sale.order']._cron_recurring_create_invoice()
            self.env['sale.order'].cron_subscription_expiration()
            # we trigger the compute because it depends on today value.
            self.assertEqual(sub.recurring_monthly, 0)
            self.assertEqual(renewal_so.recurring_monthly, 63)
            self.flush_tracking()

        with freeze_time("2021-08-03"), patch.object(type(SaleOrder), '_get_unpaid_subscriptions', lambda x: []):
            # We switch the cron the X of august to make sure the day of the cron does not affect the numbers
            renewal_so.end_date = datetime.date(2032, 1, 1)
            self.flush_tracking()
            # Total MRR is 80 coming from renewed sub
            self.env['sale.order']._cron_recurring_create_invoice()
            self.env['sale.order'].sudo().cron_subscription_expiration()
            self.assertEqual(sub.recurring_monthly, 0)
            self.assertEqual(renewal_so.recurring_monthly, 63)
            self.assertEqual(sub.stage_category, "closed")
            self.flush_tracking()
        with freeze_time("2021-09-01"), patch.object(type(SaleOrder), '_get_unpaid_subscriptions', lambda x: []):
            renewal_so.order_line.product_uom_qty = 4
            # We update the MRR of the renewed
            self.env['sale.order']._cron_recurring_create_invoice()
            self.env['sale.order'].cron_subscription_expiration()
            self.assertEqual(renewal_so.recurring_monthly, 84)
            # free subscription is not free anymore
            free_renewal_so.order_line.price_unit = 10
            self.flush_tracking()
            self.subscription._cron_update_kpi()
            self.assertEqual(sub.kpi_1month_mrr_delta, 0)
            self.assertEqual(sub.kpi_1month_mrr_percentage, 0)
            self.assertEqual(sub.kpi_3months_mrr_delta, 0)
            self.assertEqual(sub.kpi_3months_mrr_percentage, 0)
            self.assertEqual(renewal_so.kpi_1month_mrr_delta, 21)
            self.assertEqual(round(renewal_so.kpi_1month_mrr_percentage, 2), 0.33)
            self.assertEqual(renewal_so.kpi_3months_mrr_delta, 21)
            self.assertEqual(round(renewal_so.kpi_3months_mrr_percentage, 2), 0.33)

        order_log_ids = sub.order_log_ids.sorted('event_date')
        sub_data = [(log.event_type, log.event_date, log.category, log.amount_signed, log.recurring_monthly) for log in order_log_ids]
        self.assertEqual(sub_data, [('0_creation', datetime.date(2021, 1, 1), 'progress', 21, 21),
                                    ('3_transfer', datetime.date(2021, 5, 5), 'closed', -21, 0)])
        renew_logs = renewal_so.order_log_ids.sorted('event_date')
        renew_data = [(log.event_type, log.event_date, log.category, log.amount_signed, log.recurring_monthly) for log in renew_logs]

        self.assertEqual(renew_data, [('3_transfer', datetime.date(2021, 5, 1), 'progress', 21.0, 21.0),
                                      ('1_change', datetime.date(2021, 5, 5), 'progress', 42.0, 63.0),
                                      ('1_change', datetime.date(2021, 9, 1), 'progress', 21.0, 84.0)])

        free_log_ids = free_sub.order_log_ids.sorted('event_date')
        sub_data = [(log.event_type, log.event_date, log.category, log.amount_signed, log.recurring_monthly) for log in
                    free_log_ids]
        self.assertEqual(sub_data, [('0_creation', datetime.date(2021, 1, 1), 'progress', 0, 0)])
        renew_logs = free_renewal_so.order_log_ids.sorted('event_date')
        renew_data = [(log.event_type, log.event_date, log.category, log.amount_signed, log.recurring_monthly) for log
                      in renew_logs]
        self.assertEqual(renew_data, [('0_creation', datetime.date(2021, 9, 1), 'progress', 20.0, 20.0)])

        future_data = future_sub.order_log_ids.sorted('event_type') # several events aggregated on the same date
        simple_data = [(log.event_type, log.event_date, log.category, log.amount_signed, log.recurring_monthly) for log
                       in future_data]

        self.assertEqual(simple_data, [('0_creation', datetime.date(2021, 6, 1), 'progress', 1.0, 1.0),
                                       ('1_change', datetime.date(2021, 6, 1), 'progress', 3.0, 4.0)])

    def test_option_template(self):
        self.product.product_tmpl_id.product_pricing_ids = [(6, 0, 0)]
        self.env['product.pricing'].create({
            'price': 10,
            'recurrence_id': self.recurrence_year.id,
            'pricelist_id': self.company_data['default_pricelist'].id,
            'product_template_id': self.product.product_tmpl_id.id
        })
        other_pricelist = self.env['product.pricelist'].create({
            'name': 'New pricelist',
            'currency_id': self.company.currency_id.id,
        })
        self.env['product.pricing'].create({
            'recurrence_id': self.recurrence_year.id,
            'pricelist_id': other_pricelist.id,
            'price': 15,
            'product_template_id': self.product.product_tmpl_id.id
        })
        template = self.subscription_tmpl = self.env['sale.order.template'].create({
            'name': 'Subscription template without discount',
            'recurring_rule_boundary': 'unlimited',
            'note': "This is the template description",
            'auto_close_limit': 5,
            'recurrence_id': self.recurrence_year.id,
            'sale_order_template_line_ids': [Command.create({
                'name': "monthly",
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'product_uom_id': self.product.uom_id.id
            }), ],
            'sale_order_template_option_ids': [Command.create({
                'name': "line 1",
                'product_id': self.product.id,
                'quantity': 1,
                'uom_id': self.product.uom_id.id,
            })],
        })
        subscription = self.env['sale.order'].create({
            'name': 'TestSubscription',
            'is_subscription': True,
            'partner_id': self.user_portal.partner_id.id,
            'pricelist_id': self.company_data['default_pricelist'].id,
            'sale_order_template_id': template.id,
        })
        subscription._onchange_sale_order_template_id()
        self.assertEqual(subscription.order_line.price_unit, 10, "The second pricing should be applied")
        self.assertEqual(subscription.sale_order_option_ids.price_unit, 10, "The second pricing should be applied")
        subscription.pricelist_id = other_pricelist.id
        subscription.with_context(arj=True)._onchange_sale_order_template_id()
        self.assertEqual(subscription.pricelist_id.id, other_pricelist.id, "The second pricelist should be applied")
        self.assertEqual(subscription.pricelist_id, subscription.order_line.pricing_id.pricelist_id, "The second pricing should be applied")
        self.assertEqual(subscription.order_line.price_unit, 15, "The second pricing should be applied")
        self.assertEqual(subscription.sale_order_option_ids.price_unit, 15, "The second pricing should be applied")
        # Note: the pricing_id on the line is not saved on the line, but it is used to calculate the price.

    def test_update_subscription_company(self):
        """ Update the taxes of confirmed lines when the subscription company is updated """
        tax_group_1 = self.env['account.tax.group'].create({
            'name': 'Test tax group',
            'property_tax_receivable_account_id': self.company_data['default_account_receivable'].copy().id,
            'property_tax_payable_account_id': self.company_data['default_account_payable'].copy().id,
        })
        sale_tax_percentage_incl_1 = self.env['account.tax'].create({
            'name': 'sale_tax_percentage_incl_1',
            'amount': 20.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
            'price_include': True,
            'tax_group_id': tax_group_1.id,
        })
        other_company_data = self.setup_company_data("Company 3", chart_template=self.env.company.chart_template_id)
        tax_group_2 = self.env['account.tax.group'].create({
            'name': 'Test tax group',
            'property_tax_receivable_account_id': other_company_data['default_account_receivable'].copy().id,
            'property_tax_payable_account_id': other_company_data['default_account_payable'].copy().id,
        })
        sale_tax_percentage_incl_2 = self.env['account.tax'].create({
            'name': 'sale_tax_percentage_incl_2',
            'amount': 40.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
            'price_include': True,
            'tax_group_id': tax_group_2.id,
            'company_id': other_company_data['company'].id,
        })
        self.product.write({
            'taxes_id': [(6, 0, [sale_tax_percentage_incl_1.id, sale_tax_percentage_incl_2.id])],
        })
        simple_product = self.product.copy({'recurring_invoice': False})
        simple_so = self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'company_id': self.company_data['company'].id,
            'order_line': [
                (0, 0, {
                    'name': self.product.name,
                    'product_id': simple_product.id,
                    'product_uom_qty': 2.0,
                    'product_uom': simple_product.uom_id.id,
                    'price_unit': 12,
                })],
        })
        self.assertEqual(simple_so.order_line.tax_id.id, sale_tax_percentage_incl_1.id, 'The so has the first tax')
        subscription = self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'company_id': self.company_data['company'].id,
            'recurrence_id': self.recurrence_month.id,
            'order_line': [
                (0, 0, {
                    'name': self.product.name,
                    'product_id': self.product.id,
                    'product_uom_qty': 2.0,
                    'product_uom': self.product.uom_id.id,
                    'price_unit': 12,
                })],
        })
        self.assertEqual(subscription.order_line.tax_id.id, sale_tax_percentage_incl_1.id)
        (simple_so | subscription).write({'company_id': other_company_data['company'].id})
        self.assertEqual(simple_so.order_line.tax_id.id, sale_tax_percentage_incl_2.id, "Simple SO taxes must be recomputed on company change")
        self.assertEqual(subscription.order_line.tax_id.id, sale_tax_percentage_incl_2.id, "Subscription taxes must be recomputed on company change")

    def test_onchange_product_quantity_with_different_currencies(self):
        # onchange_product_quantity compute price unit into the currency of the sale_order pricelist
        # when currency of the product (Gold Coin) is different than subscription pricelist (USD)
        self.subscription.order_line = False
        self.subscription.recurrence_id = self.recurrence_month.id,
        self.pricing_month.pricelist_id = self.subscription.pricelist_id
        self.pricing_month.price = 50
        self.sub_product_tmpl.product_pricing_ids = [(6, 0, self.pricing_month.ids)]
        self.subscription.write({
            'order_line': [(0, 0, {
                'name': 'TestRecurringLine',
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'product_uom': self.product.uom_id.id,
            })],
        })
        self.assertEqual(self.subscription.currency_id.name, 'USD')
        line = self.subscription.order_line
        self.assertEqual(line.price_unit, 50, 'Price unit should not have changed')
        currency = self.currency_data['currency']
        self.product.currency_id = currency
        line.pricing_id.currency_id = currency
        line._compute_price_unit()
        conversion_rate = self.env['res.currency']._get_conversion_rate(
            self.product.currency_id,
            self.subscription.pricelist_id.currency_id,
            self.product.company_id or self.env.company,
            fields.Date.today())
        self.assertEqual(line.price_unit, self.subscription.pricelist_id.currency_id.round(50 * conversion_rate),
                         'Price unit must be converted into the currency of the pricelist (USD)')

    def test_archive_partner_invoice_shipping(self):
        # archived a partner must not remain set on invoicing/shipping address in subscription
        # here, they are set manually on subscription
        self.subscription.action_confirm()
        self.subscription.write({
            'partner_invoice_id': self.partner_a_invoice.id,
            'partner_shipping_id': self.partner_a_shipping.id,
        })
        self.assertEqual(self.partner_a_invoice, self.subscription.partner_invoice_id,
                         "Invoice address should have been set manually on the subscription.")
        self.assertEqual(self.partner_a_shipping, self.subscription.partner_shipping_id,
                         "Delivery address should have been set manually on the subscription.")
        invoice = self.subscription._create_recurring_invoice(automatic=True)
        self.assertEqual(self.partner_a_invoice, invoice.partner_id,
                         "On the invoice, invoice address should be the same as on the subscription.")
        self.assertEqual(self.partner_a_shipping, invoice.partner_shipping_id,
                         "On the invoice, delivery address should be the same as on the subscription.")
        with self.assertRaises(ValidationError):
            self.partner_a.child_ids.write({'active': False})

    def test_subscription_invoice_shipping_address(self):
        """Test to check that subscription invoice first try to use partner_shipping_id and partner_id from
        subscription"""
        partner = self.env['res.partner'].create(
            {'name': 'Stevie Nicks',
             'email': 'sti@fleetwood.mac',
             'company_id': self.env.company.id})

        partner2 = self.env['res.partner'].create(
            {'name': 'Partner 2',
             'email': 'sti@fleetwood.mac',
             'company_id': self.env.company.id})

        subscription = self.env['sale.order'].create({
            'partner_id': partner.id,
            'company_id': self.company_data['company'].id,
            'recurrence_id': self.recurrence_month.id,
            'order_line': [
                (0, 0, {
                    'name': self.product.name,
                    'product_id': self.product.id,
                    'product_uom_qty': 2.0,
                    'product_uom': self.product.uom_id.id,
                    'price_unit': 12,
                    'pricing_id': self.pricing_month.id,
                })],
        })
        subscription.action_confirm()

        invoice_id = subscription._create_recurring_invoice(automatic=True)
        addr = subscription.partner_id.address_get(['delivery', 'invoice'])
        self.assertEqual(invoice_id.partner_shipping_id.id, addr['invoice'])
        self.assertEqual(invoice_id.partner_id.id, addr['delivery'])

        subscription.write({
            'partner_id': partner.id,
            'partner_shipping_id': partner2.id,
        })
        invoice_id = subscription._create_recurring_invoice(automatic=False) # force a new invoice with all lines
        self.assertEqual(invoice_id.partner_shipping_id.id, partner2.id)
        self.assertEqual(invoice_id.partner_id.id, partner.id)

    def test_portal_pay_subscription(self):
        # When portal pays a subscription, a success mail is sent.
        # This calls AccountMove.amount_by_group, which triggers _compute_invoice_taxes_by_group().
        # As this method writes on this field and also reads tax_ids, which portal has no rights to,
        # it might cause some access rights issues. This test checks that no error is raised.
        portal_partner = self.user_portal.partner_id
        portal_partner.country_id = self.env['res.country'].search([('code', '=', 'US')])
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
        })
        provider = self.env['payment.provider'].create({
            'name': 'Test',
        })
        tx = self.env['payment.transaction'].create({
            'amount': 100,
            'provider_id': provider.id,
            'currency_id': self.env.company.currency_id.id,
            'partner_id': portal_partner.id,
        })
        self.subscription.with_user(self.user_portal).sudo().send_success_mail(tx, invoice)

    def test_upsell_date_check(self):
        """ Test what happens when the upsell invoice is not generated before the next invoice cron call """
        self.pricing_year.price = 100
        self.sub_product_tmpl.write({
            'product_pricing_ids': [(6, 0, self.pricing_year.ids)]
        })
        self.product_tmpl_2.write({
            'product_pricing_ids': [(6, 0, self.pricing_year_2.ids)]
        })
        self.product_tmpl_3.write({
            'product_pricing_ids': [(6, 0, self.pricing_year_3.ids)]
        })
        with freeze_time("2022-01-01"):
            sub = self.env['sale.order'].create({
                'name': 'TestSubscription',
                'is_subscription': True,
                'note': "original subscription description",
                'partner_id': self.user_portal.partner_id.id,
                'pricelist_id': self.company_data['default_pricelist'].id,
                'recurrence_id': self.recurrence_year.id,
                'order_line': [
                    (0, 0, {
                        'name': self.product.name,
                        'product_id': self.product.id,
                        'product_uom_qty': 1.0,
                        'product_uom': self.product.uom_id.id,
                    }),
                    (0, 0, {
                        'name': self.product2.name,
                        'product_id': self.product2.id,
                        'product_uom_qty': 1.0,
                        'product_uom': self.product.uom_id.id,
                    })
                ]
            })
            sub.action_confirm()
            self.env['sale.order']._cron_recurring_create_invoice()
            inv = sub.invoice_ids
            line_names = inv.invoice_line_ids.mapped('name')
            periods = [n.split('\n')[1] for n in line_names]
            for p in periods:
                self.assertEqual(p, '01/01/2022 to 12/31/2022', 'the first year should be invoiced')

        with freeze_time("2022-06-20"):
            action = sub.prepare_upsell_order()
            upsell_so = self.env['sale.order'].browse(action['res_id'])
            upsell_so.order_line[0].product_uom_qty = 2
            upsell_so.order_line = [(0, 0, {
                'product_id': self.product3.id,
                'product_uom_qty': 1.0,
                'product_uom': self.product.uom_id.id,
            })]
            self.assertEqual(upsell_so.next_invoice_date, datetime.date(2023, 1, 1), "The end date is the same than the parent sub")
            discounts = upsell_so.order_line.mapped('discount')
            self.assertEqual(discounts, [46.58, 46.58, 0.0, 46.58], "The discount is almost equal to 50%")
            self.assertEqual(sub.next_invoice_date, datetime.date(2023, 1, 1), 'the first year should be invoiced')
            upsell_so.action_confirm()
            self.assertEqual(upsell_so.next_invoice_date, datetime.date(2023, 1, 1), 'the first year should be invoiced')
            # We trigger the invoice cron before the generation of the upsell invoice
            self.env['sale.order']._cron_recurring_create_invoice()
            inv = sub.invoice_ids.sorted('date')[-1]
            self.assertEqual(inv.date, datetime.date(2022, 1, 1), "No invoice should be created")
        with freeze_time("2022-07-01"):
            discount = upsell_so.order_line.mapped('discount')[0]
            self.assertEqual(discount, 46.58, "The discount is almost equal to 50% and should not be updated for confirmed SO")
            self.assertEqual(upsell_so.order_line.mapped('qty_to_invoice'), [2, 0, 0, 1])
            upsell_invoice = upsell_so._create_invoices()
            inv_line_ids = upsell_invoice.invoice_line_ids.filtered('product_id')
            self.assertEqual(inv_line_ids.mapped('subscription_id'), upsell_so.subscription_id)
            self.assertEqual(inv_line_ids.mapped('subscription_start_date'), [datetime.date(2022, 6, 20), datetime.date(2022, 6, 20)])
            self.assertEqual(inv_line_ids.mapped('subscription_end_date'), [datetime.date(2022, 12, 31), datetime.date(2022, 12, 31)])
            (upsell_so | sub)._cron_recurring_create_invoice()
            inv = sub.invoice_ids.sorted('date')[-1]
            self.assertEqual(inv.date, datetime.date(2022, 1, 1), "No invoice should be created")
            self.assertEqual(upsell_invoice.amount_untaxed, 267.1, "The upsell amount should be equal to 267.1") # (1-0.4658)*(200+300)

        with freeze_time("2023-01-01"):
            (upsell_so | sub)._cron_recurring_create_invoice()
            inv = sub.invoice_ids.sorted('date')[-1]
            self.assertEqual(inv.date, datetime.date(2023, 1, 1), "A new invoice should be created")
            self.assertEqual(inv.amount_untaxed, 800, "A new invoice should be created, all the lines should be invoiced")

    def test_subscription_starts_in_future(self):
        """ Start a subscription in 2 weeks. The next invoice date should be aligned with start_date """
        with freeze_time("2022-05-15"):
            subscription = self.env['sale.order'].create({
                'partner_id': self.partner.id,
                'sale_order_template_id': self.subscription_tmpl.id,
                'recurrence_id': self.recurrence_month.id,
                'start_date': '2022-06-01',
                'next_invoice_date': '2022-06-01',
                'order_line': [
                    (0, 0, {
                        'name': self.product.name,
                        'product_id': self.product.id,
                        'product_uom_qty': 1.0,
                        'product_uom': self.product.uom_id.id,
                        'price_unit': 12,
                    })],
            })
            subscription.action_confirm()
            self.assertEqual(subscription.order_line.invoice_status, 'no', "The line qty should be black.")
            self.assertEqual(subscription.start_date, datetime.date(2022, 6, 1), 'Start date should be in the future')
            self.assertEqual(subscription.next_invoice_date, datetime.date(2022, 6, 1), 'next_invoice_date should be in the future')
            subscription._create_recurring_invoice()
            with self.assertRaisesRegex(ValidationError, 'The following recurring orders have draft invoices.*'):
                subscription._create_invoices()
            subscription.invoice_ids.filtered(lambda am: am.state == 'draft')._post()
            self.assertEqual(subscription.next_invoice_date, datetime.date(2022, 7, 1),
                             'next_invoice_date should updated')

            subscription._create_recurring_invoice()
            subscription.invoice_ids.filtered(lambda am: am.state == 'draft')._post()
            self.assertEqual(subscription.next_invoice_date, datetime.date(2022, 8, 1),
                             'next_invoice_date should updated')

    def test_invoice_status(self):
        with freeze_time("2022-05-15"):
            self.product.invoice_policy = 'delivery'
            subscription_future = self.env['sale.order'].create({
                'partner_id': self.partner.id,
                'sale_order_template_id': self.subscription_tmpl.id,
                'recurrence_id': self.recurrence_month.id,
                'start_date': '2022-06-01',
                'next_invoice_date': '2022-06-01',
                'order_line': [
                    (0, 0, {
                        'name': self.product.name,
                        'product_id': self.product.id,
                        'product_uom_qty': 1.0,
                        'product_uom': self.product.uom_id.id,
                        'price_unit': 12,
                    })],
            })

            subscription_now = self.env['sale.order'].create({
                'partner_id': self.partner.id,
                'sale_order_template_id': self.subscription_tmpl.id,
                'recurrence_id': self.recurrence_month.id,
                'start_date': '2022-05-15',
                'next_invoice_date': '2022-05-15',
                'order_line': [
                    (0, 0, {
                        'name': self.product.name,
                        'product_id': self.product.id,
                        'product_uom_qty': 1.0,
                        'product_uom': self.product.uom_id.id,
                        'price_unit': 12,
                    })],
            })

            subscription_future.action_confirm()
            subscription_now.action_confirm()
            self.assertEqual(subscription_future.order_line.invoice_status, 'no', "The line qty should be black.")
            self.assertEqual(subscription_now.order_line.invoice_status, 'no', "The line qty should be black.")
            subscription_now.order_line.qty_delivered = 1
            self.assertEqual(subscription_now.order_line.invoice_status, 'to invoice', "The line qty should be blue.")

    def test_product_pricing_respects_variants(self):
        # create a product with 2 variants
        ProductTemplate = self.env['product.template']
        ProductAttributeVal = self.env['product.attribute.value']
        Pricing = self.env['product.pricing']
        SaleOrderTemplate = self.env['sale.order.template']
        product_attribute = self.env['product.attribute'].create({'name': 'Weight'})
        product_attribute_val1 = ProductAttributeVal.create({
            'name': '1kg',
            'attribute_id': product_attribute.id
        })
        product_attribute_val2 = ProductAttributeVal.create({
            'name': '2kg',
            'attribute_id': product_attribute.id
        })
        product = ProductTemplate.create({
            'recurring_invoice': True,
            'detailed_type': 'service',
            'name': 'Variant Products',
            'list_price': 5,
        })
        product.attribute_line_ids = [(Command.create({
            'attribute_id': product_attribute.id,
            'value_ids': [Command.set([product_attribute_val1.id, product_attribute_val2.id])],
        }))]

        product_product_1 = product.product_variant_ids[0]
        product_product_2 = product.product_variant_ids[-1]

        # Define extra price for variant without temporal pricing
        self.assertEqual(product_product_2.list_price, 5.0)
        self.assertEqual(product_product_2.lst_price, 5.0)
        product_product_2.product_template_attribute_value_ids.price_extra = 15.0
        self.assertEqual(product_product_2.lst_price, 20.0)
        template = SaleOrderTemplate.create({
            'name': 'Variant Products Plan',
            'recurrence_id': self.recurrence_week.id,
            'sale_order_template_line_ids': [Command.create({
                'product_id': product_product_2.id
            })]
        })

        sale_order_form = Form(self.env['sale.order'])
        sale_order_form.partner_id = self.user_portal.partner_id
        sale_order_form.sale_order_template_id = template
        sale_order = sale_order_form.save()
        self.assertEqual(sale_order.order_line.price_unit, 20.0)

        # set pricing for variants. make sure the cheaper one is not for the variant we're testing
        cheaper_pricing = Pricing.create({
            'recurrence_id': self.recurrence_week.id,
            'price': 10,
            'product_template_id': product.id,
            'product_variant_ids': [Command.link(product_product_1.id)],
        })

        pricing2 = Pricing.create({
            'recurrence_id': self.recurrence_week.id,
            'price': 25,
            'product_template_id': product.id,
            'product_variant_ids': [Command.link(product_product_2.id)],
        })

        product.write({
            'product_pricing_ids': [Command.set([cheaper_pricing.id, pricing2.id])]
        })

        # create SO with product variant having the most expensive pricing
        sale_order = self.env['sale.order'].create({
            'name': 'TestSubscription',
            'is_subscription': True,
            'partner_id': self.user_portal.partner_id.id,
            'pricelist_id': self.company_data['default_pricelist'].id,
            'recurrence_id': self.recurrence_week.id,
            'order_line': [
                Command.create({
                    'product_id': product_product_2.id,
                    'product_uom_qty': 1
                }),
                Command.create({
                    'product_id': product_product_1[0].id,
                    'product_uom_qty': 1
                })
            ]
        })
        # check that correct pricings are being used
        self.assertEqual(sale_order.order_line[0].pricing_id.id, pricing2.id)
        self.assertEqual(sale_order.order_line[1].pricing_id.id, cheaper_pricing.id)

        # check that correct price units were selected
        self.assertEqual(sale_order.order_line[0].price_unit, 25)
        self.assertEqual(sale_order.order_line[1].price_unit, 10)

    def test_upsell_parent_line_id(self):
        with freeze_time("2022-01-01"):
            self.subscription.order_line = False
            self.subscription.write({
                'partner_id': self.partner.id,
                'recurrence_id': self.recurrence_month.id,
                'start_date': False,
                'next_invoice_date': False,
                'order_line': [
                    Command.create({
                        'product_id': self.product.id,
                        'name': "month: original",
                        'price_unit': 50,
                        'product_uom_qty': 1,
                    })
                ]
            })
            self.subscription.action_confirm()
            self.subscription._create_recurring_invoice(automatic=True)

        with freeze_time("2022-01-20"):
            action = self.subscription.prepare_upsell_order()
            upsell_so = self.env['sale.order'].browse(action['res_id'])
            # Create new lines that should be aligned with existing ones
            parent_line_id = upsell_so.order_line.parent_line_id
            self.assertEqual(self.subscription.order_line, parent_line_id, "The parent line is the one from the subscription")
            first_line_id = upsell_so.order_line[0] # line 0 is the upsell line
            first_line_id.product_id = self.product2
            self.assertFalse(first_line_id.parent_line_id, "The new line should not have a parent line")
            upsell_so.currency_id = False
            self.assertFalse(first_line_id.parent_line_id, "The new line should not have a parent line even without currency_id")
            self.subscription._compute_pricelist_id() # reset the currency_id
            upsell_so._compute_pricelist_id()
            first_line_id.product_id = self.product
            upsell_so.order_line[0].price_unit = parent_line_id.price_unit + 0.004 # making sure that rounding issue will not affect computed result
            self.assertEqual(upsell_so.order_line[0].parent_line_id, parent_line_id, "The parent line is the one from the subscription")
            first_line_id.pricing_id = parent_line_id.pricing_id
            self.assertEqual(upsell_so.order_line.parent_line_id, parent_line_id,
                             "The parent line is still the one from the subscription")
            # reset the product to another one to lose the link
            first_line_id.product_id = self.product2
            so_line_vals = [{
                'name': 'Upsell added: 1 month',
                'order_id': upsell_so.id,
                'product_id': self.product3.id,
                'product_uom_qty': 3,
                'product_uom': self.product.uom_id.id,
            }]
            self.env['sale.order.line'].create(so_line_vals)
            self.assertFalse(upsell_so.order_line[2].parent_line_id, "The new line should not have any parent line")
            upsell_so.order_line[2].product_id = self.product3
            upsell_so.order_line[2].product_id = self.product # it should recreate a link
            upsell_so.order_line[0].product_uom_qty = 2
            self.assertEqual(upsell_so.order_line.parent_line_id, parent_line_id,
                             "The parent line is the one from the subscription")
            upsell_so.action_confirm()
            self.assertEqual(self.subscription.order_line[0].product_uom_qty, 4, "The original line qty should be 4 (1 + 3 upsell line 1)")
            self.assertEqual(self.subscription.order_line[1].product_uom_qty, 2, "The new line qty should be 2 (upsell line 0)")

            action = self.subscription.prepare_renewal_order()
            renew_so = self.env['sale.order'].browse(action['res_id'])
            parent_line_id = renew_so.order_line.parent_line_id
            self.assertEqual(self.subscription.order_line, parent_line_id, "The parent line is the one from the subscription")
            renew_so.recurrence_id = self.recurrence_year.id

    def test_subscription_constraint(self):
        sub = self.subscription.copy()
        self.subscription.recurrence_id = False
        with self.assertRaisesRegex(UserError, 'You cannot save a sale order with recurring product and no recurrence.'):
            self.subscription.action_confirm()
        self.subscription.recurrence_id = self.recurrence_month
        self.product.recurring_invoice = False
        self.product2.recurring_invoice = False
        with self.assertRaisesRegex(UserError, 'You cannot save a sale order with a recurrence and no recurring product.'):
            self.subscription.action_confirm()
        # order linked to subscription with recurring product and no recurrence: it was created before the upgrade
        # of sale.subscription into sale.order
        context_no_mail = {'no_reset_password': True, 'mail_create_nosubscribe': True, 'mail_create_nolog': True, }
        delivered_product_tmpl = self.env['product.template'].with_context(context_no_mail).create({
            'name': 'Delivery product',
            'type': 'service',
            'recurring_invoice': False,
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'invoice_policy': 'delivery',
        })
        self.product.recurring_invoice = True
        self.product2.recurring_invoice = True
        sub.action_confirm()

        # Simulate the order without recurrence but linked to a subscription
        order = self.env['sale.order'].create({
            'partner_id': self.user_portal.partner_id.id,
            'pricelist_id': self.company_data['default_pricelist'].id,
            'subscription_id': sub.id,
            'order_line': [Command.create({
                'name': "recurring line",
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'product_uom': self.product.uom_id.id
                }), Command.create({
                'name': "None recurring line",
                'product_id': delivered_product_tmpl.product_variant_id.id,
                'product_uom_qty': 1,
                'product_uom': delivered_product_tmpl.product_variant_id.uom_id.id
                }),
            ],
        })
        # The following lines should raise error if the order with
        # subscription_id and no subscription_management were not False
        self.assertFalse(order.subscription_management)
        order.action_confirm()
        order.write({'order_line': [Command.create({
                    'name': "None recurring line",
                    'product_id': delivered_product_tmpl.product_variant_id.id,
                    'product_uom_qty': 1,
                    'qty_delivered': 3,
                    'product_uom': delivered_product_tmpl.product_variant_id.uom_id.id
        })],})

    def test_multiple_renew(self):
        """ Prevent to confirm several renewal quotation for the same subscription """
        self.subscription.write({'start_date': False, 'next_invoice_date': False})
        self.subscription.action_confirm()
        action = self.subscription.prepare_renewal_order()
        renewal_so_1 = self.env['sale.order'].browse(action['res_id'])
        action = self.subscription.prepare_renewal_order()
        renewal_so_2 = self.env['sale.order'].browse(action['res_id'])
        renewal_so_1.action_confirm()
        self.assertEqual(renewal_so_2.state, 'cancel', 'The other quotation should be canceled')

    def test_next_invoice_date(self):
        with freeze_time("2022-01-20"):
            subscription = self.env['sale.order'].create({
                'partner_id': self.partner.id,
                'sale_order_template_id': self.subscription_tmpl.id,
                'recurrence_id': self.recurrence_month.id,
                'order_line': [
                    (0, 0, {
                        'name': self.product.name,
                        'product_id': self.product.id,
                        'product_uom_qty': 1.0,
                        'product_uom': self.product.uom_id.id,
                        'price_unit': 12,
                    })],
            })
            self.assertFalse(subscription.next_invoice_date)
            self.assertFalse(subscription.start_date)

        with freeze_time("2022-02-10"):
            subscription.action_confirm()
            self.assertEqual(subscription.next_invoice_date, datetime.date(2022, 2, 10))
            self.assertEqual(subscription.start_date, datetime.date(2022, 2, 10))

    def test_refund_qty_invoiced(self):
        subscription = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'recurrence_id': self.recurrence_month.id,
            'order_line': [
                (0, 0, {
                    'name': self.product.name,
                    'product_id': self.product.id,
                    'product_uom_qty': 3.0,
                    'product_uom': self.product.uom_id.id,
                    'price_unit': 12,
                })],
        })
        subscription.action_confirm()
        subscription._create_recurring_invoice(automatic=True)
        self.assertEqual(subscription.order_line.qty_invoiced, 3, "The 3 products should be invoiced")
        subscription._get_invoiced()
        inv = subscription.invoice_ids
        inv.payment_state = 'paid'
        # We refund the invoice
        refund_wizard = self.env['account.move.reversal'].with_context(
            active_model="account.move",
            active_ids=inv.ids).create({
            'reason': 'Test refund tax repartition',
            'refund_method': 'cancel',
            'journal_id': inv.journal_id.id,
        })
        res = refund_wizard.reverse_moves()
        refund_move = self.env['account.move'].browse(res['res_id'])
        self.assertEqual(inv.reversal_move_id, refund_move, "The initial move should be reversed")
        self.assertEqual(subscription.order_line.qty_invoiced, 0, "The products should be not be invoiced")

    def test_discount_parent_line(self):
        with freeze_time("2022-01-01"):
            self.subscription.start_date = False
            self.subscription.next_invoice_date = False
            self.subscription.write({
                'partner_id': self.partner.id,
                'recurrence_id': self.recurrence_year.id,
            })
            self.subscription.order_line.discount = 10
            self.subscription.action_confirm()
            self.env['sale.order']._cron_recurring_create_invoice()
        with freeze_time("2022-10-31"):
            self.env['sale.order']._cron_recurring_create_invoice()
            action = self.subscription.prepare_upsell_order()
            upsell_so = self.env['sale.order'].browse(action['res_id'])
            # Discount is 55.61: 83% for pro rata temporis and 10% coming from the parent order
            # price_unit must be multiplied by (1-0.831) * 0,9
            # 100 * [1 - ((1 - 0.831) * 0.9)] = ~84%
            discount = [round(v, 2) for v in upsell_so.order_line.mapped('discount')]
            self.assertAlmostEqual(discount, [84.71, 84.71, 0])

    def test_upsell_renewal(self):
        """ Upselling a invoiced renewed order before it started should create a negative discount to invoice the previous
            period. If the renewal has not been invoiced yet, we should only invoice for the previous period.
        """
        with freeze_time("2022-01-01"):
            self.subscription.start_date = False
            self.subscription.next_invoice_date = False
            self.subscription.write({
                'partner_id': self.partner.id,
                'recurrence_id': self.recurrence_year.id,
            })
            subscription_2 = self.subscription.copy()
            (self.subscription | subscription_2).action_confirm()
            self.env['sale.order']._cron_recurring_create_invoice()

        with freeze_time("2022-09-10"):
            action = self.subscription.prepare_renewal_order()
            renewal_so = self.env['sale.order'].browse(action['res_id'])
            renewal_so.action_confirm()
            renewal_so._create_recurring_invoice()
            renewal_so.order_line.invoice_lines.move_id._post()
            self.assertEqual(renewal_so.start_date, datetime.date(2023, 1, 1))
            self.assertEqual(renewal_so.next_invoice_date, datetime.date(2024, 1, 1))
            action = self.subscription.prepare_renewal_order()
            renewal_so_2 = self.env['sale.order'].browse(action['res_id'])
            renewal_so_2.action_confirm()
            # We don't invoice renewal_so_2 yet to see what happens.
            self.assertEqual(renewal_so_2.start_date, datetime.date(2023, 1, 1))
            self.assertEqual(renewal_so_2.next_invoice_date, datetime.date(2023, 1, 1))

        with freeze_time("2022-10-2"):
            self.env['sale.order']._cron_recurring_create_invoice()
            action = renewal_so.prepare_upsell_order()
            upsell_so = self.env['sale.order'].browse(action['res_id'])
            upsell_so.order_line.filtered(lambda l: not l.display_type).product_uom_qty = 1

            action = renewal_so_2.prepare_upsell_order()
            upsell_so_2 = self.env['sale.order'].browse(action['res_id'])
            upsell_so_2.order_line.filtered(lambda l: not l.display_type).product_uom_qty = 1
            parents = upsell_so.order_line.mapped('parent_line_id')
            line_match = [
                renewal_so.order_line[0],
                renewal_so.order_line[1],
            ]
            for idx in range(2):
                self.assertEqual(parents[idx], line_match[idx])
            self.assertEqual(self.subscription.order_line.mapped('product_uom_qty'), [1, 1])
            self.assertEqual(renewal_so.order_line.mapped('product_uom_qty'), [1, 1])
            upsell_so.action_confirm()
            self.assertEqual(upsell_so.order_line.mapped('product_uom_qty'), [1.0, 1.0, 0])
            self.assertEqual(renewal_so.order_line.mapped('product_uom_qty'), [2, 2])
            self.assertEqual(upsell_so.order_line.mapped('discount'), [-24.93, -24.93, 0])
            self.assertEqual(upsell_so.start_date, datetime.date(2022, 10, 2))
            self.assertEqual(upsell_so.next_invoice_date, datetime.date(2024, 1, 1))

            self.assertEqual(upsell_so_2.amount_untaxed, 29.92, 'We only invoice for the period before the renewal')
            self.assertEqual(upsell_so_2.order_line.mapped('product_uom_qty'), [1.0, 1.0, 0])
            for discount, value in zip(upsell_so_2.order_line.mapped('discount'), [75.07, 75.07, 0.0]):
                self.assertAlmostEqual(discount, value)
            self.assertEqual(upsell_so_2.next_invoice_date, datetime.date(2023, 1, 1),
                             'We only invoice until the start of the renewal')

    def test_free_product_do_not_invoice(self):
        sub_product_tmpl = self.env['product.template'].create({
            'name': 'Free product',
            'type': 'service',
            'recurring_invoice': True,
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'list_price': 0,
        })

        self.subscription.start_date = False
        self.subscription.next_invoice_date = False
        self.subscription.order_line = [Command.clear()]
        self.subscription.write({
            'partner_id': self.partner.id,
            'recurrence_id': self.recurrence_year.id,
            'order_line': [Command.create({
                'name': sub_product_tmpl.name,
                'product_id': sub_product_tmpl.product_variant_id.id,
                'product_uom_qty': 1.0,
                'product_uom': sub_product_tmpl.uom_id.id,
            })]
        })
        self.assertEqual(self.subscription.amount_untaxed, 0, "The price shot be 0")
        self.assertEqual(self.subscription.order_line.price_subtotal, 0, "The price line should be 0")
        self.assertEqual(self.subscription.order_line.invoice_status, 'no', "Nothing to invoice here")

    def test_invoice_done_order(self):
        # Prevent to invoice order in done state
        with freeze_time("2021-01-03"):
            self.subscription.action_confirm()
            self.env['sale.order']._cron_recurring_create_invoice()
            self.assertEqual(self.subscription.invoice_count, 1)

        with freeze_time("2021-02-03"):
            self.subscription.action_done()
            self.env['sale.order']._cron_recurring_create_invoice()
            self.assertEqual(self.subscription.invoice_count, 1)

    def test_subscription_management(self):
        # test default value for subcription_management
        sub_1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'recurrence_id': self.recurrence_month.id,
            'order_line': [
                (0, 0, {
                    'name': self.product.name,
                    'product_id': self.product.id,
                    'product_uom_qty': 3.0,
                    'product_uom': self.product.uom_id.id,
                    'price_unit': 12,
                })],
        })
        self.assertEqual(sub_1.subscription_management, 'create')
        sub_2 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self.assertFalse(sub_2.subscription_management,)
        sub_2.recurrence_id = self.recurrence_month.id
        sub_2.order_line = [
            (0, 0, {
                'name': self.product.name,
                'product_id': self.product.id,
                'product_uom_qty': 3.0,
                'product_uom': self.product.uom_id.id,
                'price_unit': 12,
            })]
        self.assertEqual(sub_2.subscription_management, 'create')

    def test_free_subscription(self):
        with freeze_time("2023-01-01"):
            pricelist = self.env['product.pricelist'].create({
                'name': 'Pricelist A',
            })
            # We don't want to create invoice when the sum of recurring line is 0
            nr_product = self.env['product.template'].create({
                'name': 'Non recurring product',
                'type': 'service',
                'uom_id': self.product.uom_id.id,
                'list_price': 25,
                'invoice_policy': 'order',
            })
            # nr_product.taxes_id = False # we avoid using taxes in this example
            self.pricing_year.unlink()
            self.pricing_month.price = 25
            self.product2.list_price = -25.0
            # total = 0 & recurring amount = 0
            sub_0_0 = self.env['sale.order'].create({
                'partner_id': self.partner.id,
                'recurrence_id': self.recurrence_month.id,
                'pricelist_id': pricelist.id,
                'order_line': [
                    (0, 0, {
                        'name': self.product.name,
                        'product_id': self.product.id,
                        'product_uom_qty': 2.0,
                        'product_uom': self.product.uom_id.id,
                    }),
                    (0, 0, {
                        'name': self.product.name,
                        'product_id': self.product2.id,
                        'product_uom_qty': 2.0,
                        'product_uom': self.product.uom_id.id,
                        'price_unit': -25,
                    })
                ],
            })
            # total = 0 & recurring amount > 0
            sub_0_1 = self.env['sale.order'].create({
                'partner_id': self.partner.id,
                'recurrence_id': self.recurrence_month.id,
                'pricelist_id': pricelist.id,
                'order_line': [
                    (0, 0, {
                        'name': self.product.name,
                        'product_id': self.product.id,
                        'product_uom_qty': 2.0,
                        'product_uom': self.product.uom_id.id,
                    }),
                    (0, 0, {
                        'name': nr_product.name,
                        'product_id': nr_product.product_variant_id.id,
                        'product_uom_qty': 2.0,
                        'product_uom': nr_product.uom_id.id,
                        'price_unit': -25,
                    })
                ],
            })
            # total > 0 & recurring amount = 0
            sub_1_0 = self.env['sale.order'].create({
                'partner_id': self.partner.id,
                'recurrence_id': self.recurrence_month.id,
                'pricelist_id': pricelist.id,
                'order_line': [
                    (0, 0, {
                        'name': self.product.name,
                        'product_id': self.product.id,
                        'product_uom_qty': 2.0,
                        'product_uom': self.product.uom_id.id,
                    }),
                    (0, 0, {
                        'name': self.product.name,
                        'product_id': self.product2.id,
                        'product_uom_qty': 2.0,
                        'product_uom': self.product2.uom_id.id,
                    }),
                    (0, 0, {
                        'name': nr_product.name,
                        'product_id': nr_product.product_variant_id.id,
                        'product_uom_qty': 2.0,
                        'product_uom': nr_product.uom_id.id,
                    }),
                ],
            })

            sub_negative_recurring = self.env['sale.order'].create({
                'partner_id': self.partner.id,
                'recurrence_id': self.recurrence_month.id,
                'pricelist_id': pricelist.id,
                'order_line': [
                    (0, 0, {
                        'name': self.product.name,
                        'product_id': self.product.id,
                        'product_uom_qty': 2.0,
                        'product_uom': self.product.uom_id.id,
                        'price_unit': -30
                    }),
                    (0, 0, {
                        'name': self.product.name,
                        'product_id': self.product2.id,
                        'product_uom_qty': 2.0,
                        'product_uom': self.product2.uom_id.id,
                        'price_unit': -10
                    }),
                ],
            })

            # negative_nonrecurring_sub
            negative_nonrecurring_sub = self.env['sale.order'].create({
                'partner_id': self.partner.id,
                'recurrence_id': self.recurrence_month.id,
                'pricelist_id': pricelist.id,
                'order_line': [
                    (0, 0, {
                        'name': self.product.name,
                        'product_id': self.product.id,
                        'product_uom_qty': 2.0,
                        'product_uom': self.product.uom_id.id,
                        'price_unit': -30
                    }),
                    (0, 0, {
                        'name': self.product.name,
                        'product_id': self.product2.id,
                        'product_uom_qty': 2.0,
                        'product_uom': self.product2.uom_id.id,
                        'price_unit': -10
                    }),
                    (0, 0, {
                        'name': nr_product.name,
                        'product_id': nr_product.product_variant_id.id,
                        'product_uom_qty': 4.0,
                        'product_uom': nr_product.uom_id.id,
                    }),
                ],
            })

            (sub_0_0 | sub_0_1 | sub_1_0 | sub_negative_recurring | negative_nonrecurring_sub).order_line.tax_id = False
            (sub_0_0 | sub_0_1 | sub_1_0 | sub_negative_recurring | negative_nonrecurring_sub).action_confirm()

            invoice_0_0 = sub_0_0._create_recurring_invoice(automatic=True)
            self.assertTrue(sub_0_0.currency_id.is_zero(sub_0_0.amount_total))
            self.assertFalse(invoice_0_0, "Free contract with recurring products should not create invoice")
            self.assertEqual(sub_0_0.order_line.mapped('invoice_status'), ['no', 'no'], 'No invoice needed')

            self.assertTrue(sub_0_1.currency_id.is_zero(sub_0_1.amount_total))
            self.assertTrue(sub_0_1.order_line.filtered(lambda l: l.temporal_type == 'subscription').price_subtotal > 0)
            invoice_0_1 = sub_0_1._create_recurring_invoice(automatic=True)
            self.assertEqual(invoice_0_1.amount_total, 0, "Total is 0 but an invoice should be created.")
            self.assertEqual(sub_0_1.order_line.mapped('invoice_status'), ['invoiced', 'invoiced'], 'No invoice needed')

            self.assertTrue(sub_1_0.amount_total > 0)
            invoice_1_0 = sub_1_0._create_recurring_invoice(automatic=True)
            self.assertEqual(invoice_1_0.amount_total, 50, "Total is 0 and an invoice should be created.")
            self.assertEqual(sub_1_0.order_line.mapped('invoice_status'), ['no', 'no', 'invoiced'], 'No invoice needed')
            self.assertFalse(all(invoice_1_0.invoice_line_ids.sale_line_ids.product_id.mapped('recurring_invoice')),
                             "The recurring line should be invoiced")

            # Negative subscription will be invoiced by cron the next day
            negative_invoice = sub_negative_recurring._create_recurring_invoice(automatic=True)
            self.assertEqual(sub_negative_recurring.amount_total, -80)
            self.assertFalse(negative_invoice, "Free contract with recurring products should not create invoice")
            self.assertEqual(sub_negative_recurring.order_line.mapped('invoice_status'), ['no', 'no'], 'No invoice needed')

            negative_non_recurring_inv = negative_nonrecurring_sub._create_recurring_invoice(automatic=True)
            self.assertEqual(negative_nonrecurring_sub.amount_total, 20)
            self.assertFalse(negative_non_recurring_inv, "negative contract with non recurring products should not create invoice")
            self.assertEqual(sub_negative_recurring.order_line.mapped('invoice_status'), ['no', 'no'],
                             'No invoice needed')
            self.assertTrue(negative_nonrecurring_sub.payment_exception, "The contract should be in exception")

    def test_subscription_unlink_flow(self):
        """
            Check that the user receives the correct messages when he deletes a subscription.
            Check that the flow to delete a subscription is confirm => close => cancel
        """
        subscription_a = self.env['sale.order'].create({
            'partner_id': self.user_portal.partner_id.id,
            'sale_order_template_id': self.subscription_tmpl.id,
        })
        subscription_b = self.env['sale.order'].create({
            'partner_id': self.user_portal.partner_id.id,
            'sale_order_template_id': self.subscription_tmpl.id,
        })
        subscription_c = self.env['sale.order'].create({
            'partner_id': self.user_portal.partner_id.id,
            'sale_order_template_id': self.subscription_tmpl.id,
        })
        subscription_d = self.env['sale.order'].create({
            'partner_id': self.user_portal.partner_id.id,
            'sale_order_template_id': self.subscription_tmpl.id,
        })
        subscription_a._onchange_sale_order_template_id()
        subscription_b._onchange_sale_order_template_id()
        subscription_c._onchange_sale_order_template_id()
        subscription_d._onchange_sale_order_template_id()
        # Subscription can be deleted if it is in draft
        subscription_a.unlink()
        # Subscription cannot be deleted if it was confirmed once before and it is not closed
        subscription_b.action_confirm()
        with self.assertRaisesRegex(UserError,
            r'You can not delete a confirmed subscription. You must first close and cancel it before you can delete it.'):
            subscription_b.unlink()
        # Subscription cannot be deleted if it is closed
        subscription_c.action_confirm()
        subscription_c.set_close()
        with self.assertRaisesRegex(UserError,
            r'You can not delete a sent quotation or a confirmed sales order. You must first cancel it.'):
            subscription_c.unlink()
        # Subscription can be deleted if it is cancel
        subscription_d.action_confirm()
        subscription_d.set_close()
        subscription_d._action_cancel()
        subscription_d.unlink()

    def test_modify_discount_on_upsell(self):
        """
        Makes sure that you can edit the discount on an upsell, save it, and then confirm it,
        and it doesn't change/reset to default
        """
        with freeze_time("2022-10-31"):
            self.subscription.action_confirm()
            self.env['sale.order']._cron_recurring_create_invoice()
            action = self.subscription.prepare_upsell_order()
            upsell_so = self.env['sale.order'].browse(action['res_id'])
            upsell_line = upsell_so.order_line.filtered(lambda l: not l.display_type)[0]
            old_discount = upsell_line.discount
            new_discount = 42
            self.assertTrue(old_discount != new_discount,
                            "These discounts should be different, change the value of new_discount if this test fail.")
            upsell_line.write({'discount': new_discount})
            self.assertEqual(upsell_line.discount, new_discount,
                             "The line should have the new discount written.")
            upsell_so.action_confirm()
            self.assertEqual(upsell_line.discount, new_discount,
                             "The line should have the new discount after confirmation.")

    def test_renew_different_currency(self):
        with freeze_time("2023-03-28"):
            self.product.product_pricing_ids.unlink()
            default_pricelist = self.company_data['default_pricelist']
            other_currency = self.env.ref('base.EUR')
            other_currency.action_unarchive()
            other_pricelist = self.env['product.pricelist'].create({
                'name': 'Test Pricelist (EUR)',
                'currency_id': other_currency.id,
            })
            other_currency.write({
                'rate_ids': [(0, 0, {
                    'rate': 20,
                })]
            })
            pricing_month_1 = self.env['product.pricing'].create({
                'recurrence_id': self.recurrence_month.id,
                'price': 10,
                'pricelist_id': default_pricelist.id,
            })
            pricing_month_2 = self.env['product.pricing'].create({
                'recurrence_id': self.recurrence_month.id,
                'price': 200,
                'pricelist_id': other_pricelist.id,
            })
            sub_product_tmpl = self.env['product.template'].create({
                'name': 'BaseTestProduct',
                'type': 'service',
                'recurring_invoice': True,
                'uom_id': self.env.ref('uom.product_uom_unit').id,
                'product_pricing_ids': [(6, 0, (pricing_month_1 | pricing_month_2).ids)]
            })
            subscription_tmpl = self.env['sale.order.template'].create({
                'name': 'Subscription template without discount',
                'recurring_rule_type': 'year',
                'recurring_rule_boundary': 'limited',
                'recurring_rule_count': 2,
                'note': "This is the template description",
                'auto_close_limit': 5,
                'recurrence_id': self.recurrence_month.id,
                'sale_order_template_line_ids': [Command.create({
                    'name': "Product 1",
                    'product_id': sub_product_tmpl.product_variant_id.id,
                    'product_uom_qty': 1,
                    'product_uom_id': sub_product_tmpl.product_variant_id.uom_id.id,
                })]
            })
            sub = self.subscription.create({
                'name': 'Company1 - Currency1',
                'sale_order_template_id': subscription_tmpl.id,
                'partner_id': self.user_portal.partner_id.id,
                'currency_id': self.company.currency_id.id,
                'recurrence_id': self.recurrence_month.id,
                'order_line': [(0, 0, {
                    'name': "Product 1",
                    'product_id': sub_product_tmpl.product_variant_id.id,
                    'product_uom_qty': 1,
                    'product_uom': sub_product_tmpl.uom_id.id
                })]
            })
            sub.pricelist_id = default_pricelist.id
            sub._onchange_sale_order_template_id() # recompute the pricings
            self.flush_tracking()
            sub.action_confirm()
            self.assertEqual(sub.recurring_monthly, 10)
            self.flush_tracking()
            self.env['sale.order']._cron_recurring_create_invoice()
            self.flush_tracking()

        with freeze_time("2023-04-29"):
            action = sub.prepare_renewal_order()
            renewal_so = self.env['sale.order'].browse(action['res_id'])
            renewal_so.write({
                'pricelist_id': other_pricelist.id,
            })
            renewal_so._onchange_sale_order_template_id()
            renewal_so.order_line.product_uom_qty = 3
            self.flush_tracking()
            renewal_so.action_confirm()
            self.flush_tracking()
            self.env['sale.order']._cron_recurring_create_invoice()
            self.flush_tracking()
            renewal_so.action_confirm()
            self.flush_tracking()
            order_log_ids = sub.order_log_ids.sorted('event_date')
            sub_data = [(log.event_type, log.event_date, log.amount_signed, log.recurring_monthly, log.currency_id)
                        for log in order_log_ids]
            self.assertEqual(sub_data,
                             [('0_creation', datetime.date(2023, 3, 28), 10, 10, default_pricelist.currency_id),
                              ('3_transfer', datetime.date(2023, 4, 29), -10, 0, default_pricelist.currency_id)
                              ])

            renew_logs = renewal_so.order_log_ids.sorted('id')
            renew_data = [(log.event_type, log.event_date, log.amount_signed, log.recurring_monthly, log.currency_id)
                          for log in renew_logs]
            self.assertEqual(renew_data,
                             [('3_transfer', datetime.date(2023, 4, 29), 200, 200, other_currency),
                              ('1_change', datetime.date(2023, 4, 29), 400, 600, other_currency)
                              ])

    def test_subscription_pricelist_discount(self):
        context_no_mail = {'no_reset_password': True, 'mail_create_nosubscribe': True, 'mail_create_nolog': True, }
        pricelist = self.company_data['default_pricelist']
        pricelist.discount_policy = 'without_discount'
        pricelist.item_ids.create({
            'pricelist_id': pricelist.id,
            'compute_price': 'percentage',
            'percent_price': 50,
        })
        sub = self.env["sale.order"].with_context(**context_no_mail).create({
            'name': 'TestSubscription',
            'is_subscription': True,
            'recurrence_id': self.recurrence_month.id,
            'note': "original subscription description",
            'partner_id': self.user_portal.partner_id.id,
            'pricelist_id': self.company_data['default_pricelist'].id,
            'sale_order_template_id': self.subscription_tmpl.id,
        })
        sub._onchange_sale_order_template_id()
        sub.order_line.create({
            'order_id': sub.id,
            'product_id': self.product_a.id, # non-subscription product
        })
        self.assertEqual(sub.order_line.mapped('discount'), [0, 0, 50],
            "Regular pricelist discounts should't affect temporal items.")
        sub.order_line.discount = 20
        self.assertEqual(sub.order_line.mapped('discount'), [20, 20, 20])
        sub.action_confirm()
        self.assertEqual(sub.order_line.mapped('discount'), [20, 20, 20],
             "Discounts should not be reset on confirmation.")

    def test_churn_log_renew(self):
        self.flush_tracking()
        today = datetime.date.today()
        context_mail = {'tracking_disable': False}
        sub = self.env['sale.order'].with_context(context_mail).create({
            'name': 'TestSubscription',
            'is_subscription': True,
            'note': "original subscription description",
            'partner_id': self.user_portal.partner_id.id,
            'pricelist_id': self.company_data['default_pricelist'].id,
            'sale_order_template_id': self.subscription_tmpl.id,
        })
        sub._onchange_sale_order_template_id()
        # Same product for both lines
        sub.order_line.product_uom_qty = 1
        sub.end_date = datetime.date(2022, 1, 1)
        self.flush_tracking()
        sub.action_confirm()
        self.flush_tracking()
        sub.order_line.product_uom_qty = 2
        self.flush_tracking()
        self.env['sale.order'].with_context(tracking_disable=False)._cron_recurring_create_invoice()
        self.flush_tracking()
        action = sub.with_context(tracking_disable=False).prepare_renewal_order()
        renewal_so = self.env['sale.order'].browse(action['res_id'])
        renewal_so = renewal_so.with_context(tracking_disable=False)
        renewal_so.order_line.product_uom_qty = 3
        renewal_so.name = "Renewal"
        sub.set_close()
        self.flush_tracking()
        renewal_so.action_confirm()
        self.flush_tracking()
        # Most of the time, the renewal invoice is created by the salesman
        # before the renewal start date
        renewal_invoices = renewal_so._create_invoices()
        renewal_invoices._post()
        self.flush_tracking()
        order_log_ids = sub.order_log_ids.sorted('id')
        sub_data = [(log.event_type, log.event_date, log.category, log.amount_signed, log.recurring_monthly) for log in
                    order_log_ids]
        self.assertEqual(sub_data, [('0_creation', today, 'progress', 21, 21),
                                    ('1_change', today, 'progress', 21.0, 42.0),
                                    ('2_churn', today, 'closed', -42, 0)])
        renew_logs = renewal_so.order_log_ids.sorted('id')
        renew_data = [(log.event_type, log.event_date, log.category, log.amount_signed, log.recurring_monthly) for log
                      in renew_logs]

        self.assertEqual(renew_data, [('0_creation', today, 'progress', 63, 63)])

    def test_renew_pricelist_currency_update(self):
        """
        Assert that after renewing a subscription, changing the pricelist
        to another one will recompute the order lines pricings.
        """
        with freeze_time("2023-04-04"):
            default_pricelist = self.company_data['default_pricelist']
            other_currency = self.env.ref('base.EUR')
            other_currency.action_unarchive()
            other_pricelist = self.env['product.pricelist'].create({
                'name': 'Test Pricelist (EUR)',
                'currency_id': other_currency.id,
            })
            other_currency.rate_ids = [Command.create({'rate': 20})]
            pricing_month_1_usd = self.env['product.pricing'].create({
                'recurrence_id': self.recurrence_month.id,
                'price': 100,
                'pricelist_id': default_pricelist.id,
            })
            pricing_month_2_eur = self.env['product.pricing'].create({
                'recurrence_id': self.recurrence_month.id,
                'price': 200,
                'pricelist_id': other_pricelist.id,
            })
            sub_product_tmpl = self.env['product.template'].create({
                'name': 'BaseTestProduct',
                'type': 'service',
                'recurring_invoice': True,
                'uom_id': self.env.ref('uom.product_uom_unit').id,
                'product_pricing_ids': [Command.set((pricing_month_1_usd | pricing_month_2_eur).ids)]
            })
            sub = self.subscription.create({
                'name': 'Company1 - Currency1',
                'partner_id': self.user_portal.partner_id.id,
                'currency_id': self.company.currency_id.id,
                'recurrence_id': self.recurrence_month.id,
                'pricelist_id': default_pricelist.id,
                'order_line': [Command.create({
                    'name': "Product 1",
                    'product_id': sub_product_tmpl.product_variant_id.id,
                    'product_uom_qty': 1,
                    'product_uom': sub_product_tmpl.uom_id.id
                })]
            })
            sub.action_confirm()
            self.flush_tracking()

            # Assert that order line was created with correct pricing and currency.
            self.assertEqual(sub.order_line[0].price_unit, 100.0, "Subscription product's order line must be created with default pricelist pricing (USD) having the price unit as 100.0.")
            self.assertEqual(sub.order_line[0].order_id.currency_id.id, self.company.currency_id.id, "Subscription product's order line must be created with the default company currency (USD).")
            self.assertEqual(sub.pricelist_id.id, default_pricelist.id, "Subscription must be created with the default company pricelist (in USD).")
            self.env['sale.order']._cron_recurring_create_invoice()
            self.flush_tracking()

        with freeze_time("2023-04-05"):
            action = sub.prepare_renewal_order()
            renewal_so = self.env['sale.order'].browse(action['res_id'])

            # Assert that parent_line_id is saved in renewed subscription.
            self.assertEqual(renewal_so.order_line[0].parent_line_id.id, sub.order_line[0].id, "The parent line of the order line should have been saved after subscription renewal.")
            renewal_so.pricelist_id = other_pricelist.id

            # Computes the updated price unit through 'Update Prices' button.
            renewal_so.action_update_prices()
            renewal_so.invalidate_recordset()

            # Assert that updated pricing has the correct currency, price_unit and pricelist.
            self.assertEqual(renewal_so.pricelist_id.id, other_pricelist.id, "Pricelist must update to the new one (in EUR) after performing a manual update.")
            self.assertEqual(renewal_so.order_line[0].currency_id.id, other_currency.id, "Order line's currency should have been updated from USD to EUR after changing the pricelist.")
            self.assertEqual(renewal_so.order_line[0].price_unit, 200.0, "Order line's price unit must update to 200.0 according to the new pricelist pricing (in EUR).")

            # Update prices button removes the parent_line_id of order lines to recalculate pricings.
            self.assertFalse(renewal_so.order_line[0].parent_line_id, "Parent order line should not exist anymore after updating prices, it was intentionally deleted for forcing price recalculation.")

    def test_recurrence_field_automatic_price_unit_update(self):
        """
        Assert that after changing the 'Recurrence' field of a subscription,
        prices will recompute automatically ONLY for subscription products.
        """
        default_pricelist = self.company_data['default_pricelist']
        other_currency = self.env.ref('base.EUR')
        other_currency.action_unarchive()
        pricing_month_1_eur = self.env['product.pricing'].create({
            'recurrence_id': self.recurrence_month.id,
            'price': 100,
            'pricelist_id': default_pricelist.id,
        })
        pricing_year_1_eur = self.env['product.pricing'].create({
            'recurrence_id': self.recurrence_year.id,
            'price': 1000,
            'pricelist_id': default_pricelist.id,
        })
        simple_product = self.product.copy({'recurring_invoice': False})
        simple_product_order_line = {
            'name': self.product.name,
            'product_id': simple_product.id,
            'product_uom_qty': 2.0,
            'product_uom': simple_product.uom_id.id
        }
        sub_product_tmpl = self.env['product.template'].create({
            'name': 'BaseTestProduct',
            'type': 'service',
            'recurring_invoice': True,
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'product_pricing_ids': [Command.set((pricing_month_1_eur | pricing_year_1_eur).ids)]
        })
        sub_product_order_line = {
            'name': "Product 1",
            'product_id': sub_product_tmpl.product_variant_id.id,
            'product_uom_qty': 1,
            'product_uom': sub_product_tmpl.uom_id.id
        }
        sub = self.subscription.create({
            'name': 'Company1 - Currency1',
            'partner_id': self.user_portal.partner_id.id,
            'currency_id': self.company.currency_id.id,
            'recurrence_id': self.recurrence_month.id,
            'pricelist_id': default_pricelist.id,
            'order_line': [
                Command.create(sub_product_order_line),
                Command.create(simple_product_order_line)
            ]
        })
        sub.action_confirm()
        self.flush_tracking()
        # Assert that order lines were created with correct pricing and currency.
        self.assertEqual(sub.order_line[0].price_unit, 100.0, "Subscription product's order line should have its price unit as 100.0 according to the 'Monthly' pricing during creation.")
        self.assertEqual(sub.order_line[1].price_unit, 50.0, "Simple product's order line must have its default price unit of 50.0 during creation.")

        # Change the 'Recurrence' field and check if price unit updated ONLY in the recurring order line.
        sub.recurrence_id = self.recurrence_year.id
        self.assertEqual(sub.order_line[0].price_unit, 1000.0, "Subscription product's order line must have its unit price as 1000.0 after 'Recurrence' is changed to 'Yearly'.")
        self.assertEqual(sub.order_line[1].price_unit, 50.0, "Simple product's order line must not update its price unit, it must be kept as 50.0 during the 'Recurrence' field changes.")

        # Update price of normal product and check if it is updated in recurrence (it should not!)
        sub.order_line[1].product_id.list_price = 70.0
        self.assertEqual(sub.order_line[1].price_unit, 50.0, "Simple product's price unit must be kept as 50.0 even though the product price was updated outside the subscription scope.")
        self.env['sale.order']._cron_recurring_create_invoice()
        self.flush_tracking()

        # Change again the 'Recurrence' field and check if the price unit update during renewal was done in the recurring order line.
        action = sub.prepare_renewal_order()
        renewal_so = self.env['sale.order'].browse(action['res_id'])
        renewal_so.recurrence_id = self.recurrence_month.id
        self.assertEqual(renewal_so.order_line[0].price_unit, 100.0, "Subscription product's order line must have its unit price as 100.0 after 'Recurrence' is changed to 'Monthly'.")

        # Change the 'Recurrence' field to yearly and ensure that price was updated accordingly for the subscription product.
        renewal_so.recurrence_id = self.recurrence_year.id
        self.assertEqual(renewal_so.order_line[0].price_unit, 1000.0, "Subscription product's order line must have its unit price as 1000.0 after 'Recurrence' is changed to 'Yearly'.")

    def test_new_recurrence_id_optional_products_price_update(self):
        """
        Assert that after changing the 'Recurrence' field of a subscription, prices will be recomputed
        for Optional Products with time-based pricing linked to the subscription template.
        """
        # Define a subscription template with a optional product having time-based pricing.
        self.product.product_tmpl_id.product_pricing_ids.unlink()
        self.env['product.pricing'].create({
            'price': 150,
            'recurrence_id': self.recurrence_month.id,
            'product_template_id': self.product.product_tmpl_id.id
        })
        self.env['product.pricing'].create({
            'price': 1000,
            'recurrence_id': self.recurrence_year.id,
            'product_template_id': self.product.product_tmpl_id.id
        })
        template = self.subscription_tmpl = self.env['sale.order.template'].create({
            'name': 'Subscription template with time-based pricing on optional product',
            'note': "This is the template description",
            'auto_close_limit': 5,
            'recurrence_id': self.recurrence_year.id,
            'sale_order_template_line_ids': [Command.create({
                'name': "monthly",
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'product_uom_id': self.product.uom_id.id
            })],
            'sale_order_template_option_ids': [Command.create({
                'name': "line 1",
                'product_id': self.product.id,
                'quantity': 1,
                'uom_id': self.product.uom_id.id,
            })],
        })
        # Create the subscription based on the subscription template.
        subscription = self.env['sale.order'].create({
            'name': 'TestSubscription',
            'is_subscription': True,
            'partner_id': self.user_portal.partner_id.id,
            'pricelist_id': self.company_data['default_pricelist'].id,
            'recurrence_id': self.recurrence_month.id,
            'sale_order_template_id': template.id,
        })
        subscription._onchange_sale_order_template_id()

        # Assert that optional product has its price updated after changing the 'recurrence' field.
        self.assertEqual(subscription.sale_order_option_ids.price_unit, 150, "The price unit for the optional product must be 150.0 due to 'Monthly' value in the 'Recurrence' field.")
        subscription.recurrence_id = self.recurrence_year.id
        self.assertEqual(subscription.sale_order_option_ids.price_unit, 1000, "The price unit for the optional product must update to 1000.0 after changing the 'Recurrence' field to 'Yearly'.")

    def test_stage_progress_for_order_with_no_stage(self):
        """ Test that the stage progress is computed for a subscription
        with no stage. """

        self.subscription.stage_id = False
        self.subscription.action_confirm()
        self.assertTrue(self.subscription.stage_id, "The stage should be set")

    def test_change_uom_on_reccuring_SO(self):
        """ Tests that the unit_price of a product is computed when changing its UoM
        on a sale order that is recurring."""

        self.product_tmpl_2.write({'name': 'Subscription product', 'type': 'consu'})
        self.product_tmpl_5.write({'name': 'Not Subscription product', 'type': 'consu'})

        self.product2 = self.product_tmpl_2.product_variant_id
        self.product5 = self.product_tmpl_5.product_variant_id
        self.product2.write({'list_price': 10})
        self.product5.write({'list_price': 1})

        subscription_so = self.env['sale.order'].create({
            'name': 'Sale Order with subscription',
            'is_subscription': True,
            'partner_id': self.user_portal.partner_id.id,
            'recurrence_id': self.recurrence_month.id,
            'order_line': [
                Command.create({
                    'name': self.product2.name,
                    'product_id': self.product2.id,
                    'product_uom_qty': 1,
                    'product_uom': self.env.ref('uom.product_uom_unit').id,
                }),
                Command.create({
                    'name': self.product5.name,
                    'product_id': self.product5.id,
                    'product_uom_qty': 1,
                    'product_uom': self.env.ref('uom.product_uom_unit').id,
                })
            ]
        })

        base = subscription_so.order_line[0].price_unit
        subscription_so.order_line[0]['product_uom'] = self.env.ref('uom.product_uom_dozen').id
        self.assertEqual(subscription_so.order_line[0].price_unit, 12 * base)

        base = subscription_so.order_line[1].price_unit
        subscription_so.order_line[1]['product_uom'] = self.env.ref('uom.product_uom_dozen').id
        self.assertEqual(subscription_so.order_line[1].price_unit, 12 * base)

    def test_upsell_descriptions(self):
        with freeze_time("2022-10-31"):
            self.subscription.action_confirm()
            self.env['sale.order']._cron_recurring_create_invoice()

            action = self.subscription.prepare_upsell_order()
            upsell_so = self.env['sale.order'].browse(action['res_id'])
            upsell_so.order_line = [Command.create({'product_id': self.product_a.id})]
            upsell_so.order_line.filtered('product_id').product_uom_qty = 1
            upsell_so.action_confirm()
            invoice = upsell_so._create_invoices()

            self.assertEqual(len(invoice.invoice_line_ids), 4)
            for line in invoice.invoice_line_ids:
                name = line.name
                sol_name = line.sale_line_ids.name
                if line.sale_line_ids.temporal_type == 'subscription':
                    self.assertRegex(name, rf"^{sol_name} - 1 Month", "Sub lines require duration")
                else:
                    self.assertEqual(name, sol_name, "Non-sub lines shouldn't add duration")

    def test_sale_subscription_upsell_does_not_copy_non_recurring_products(self):
        """
        Check that the non-recurring product of the upsell is not
        copied to the subscription.
        """
        nr_product = self.env['product.template'].create({
            'name': 'Non recurring product',
            'type': 'service',
            'uom_id': self.product.uom_id.id,
            'list_price': 25,
            'invoice_policy': 'order',
        })
        self.subscription.action_confirm()
        self.env['sale.order']._cron_recurring_create_invoice()

        action = self.subscription.prepare_upsell_order()
        upsell_so = self.env['sale.order'].browse(action['res_id'])
        upsell_so.order_line = [(6, 0, self.env['sale.order.line'].create({
            'name': nr_product.name,
            'order_id': upsell_so.id,
            'product_id': nr_product.product_variant_id.id,
            'product_uom_qty': 1,
        }).ids)]

        upsell_so._confirm_upsell()
        self.assertEqual(len(upsell_so.order_line), 1)
        self.assertEqual(len(self.subscription.order_line), 2)
        self.assertEqual(upsell_so.order_line.name, nr_product.name)
        self.assertFalse(nr_product in self.subscription.order_line.product_template_id)

    def test_uspell_same_product_different_discount(self):
        subscription = self.env['sale.order'].create({
            'name': 'Original subscription',
            'is_subscription': True,
            'partner_id': self.user_portal.partner_id.id,
            'recurrence_id': self.recurrence_month.id,
            'order_line': [
                Command.create({
                    'name': self.product2.name,
                    'product_id': self.product2.id,
                    'product_uom_qty': 1,
                    'product_uom': self.env.ref('uom.product_uom_unit').id,
                    'discount': 0,
                }),
                Command.create({
                    'name': self.product2.name,
                    'product_id': self.product2.id,
                    'product_uom_qty': 1,
                    'product_uom': self.env.ref('uom.product_uom_unit').id,
                    'discount': 50,
                })
            ]
        })

        subscription.action_confirm()
        self.env['sale.order']._cron_recurring_create_invoice()
        action = subscription.prepare_upsell_order()
        upsell = self.env['sale.order'].browse(action['res_id'])
        self.assertEqual(set(upsell.order_line.mapped('discount')), {0, 50}, 'Upsell discounts should match subscription discounts')
