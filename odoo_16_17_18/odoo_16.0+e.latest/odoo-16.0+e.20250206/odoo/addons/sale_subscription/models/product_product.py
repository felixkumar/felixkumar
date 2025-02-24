# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_best_pricing_rule(self, **kwargs):
        """ Return the best pricing rule for the given duration.
        :param float duration: duration, in unit uom
        :param str unit: duration unit (hour, day, week)
        :param datetime start_date:
        :param datetime end_date:
        :return: least expensive pricing rule for given duration
        """
        self.ensure_one()

        duration, unit = kwargs.get('duration', False), kwargs.get('unit', '')

        if not self.recurring_invoice or not duration or not unit:
            return super()._get_best_pricing_rule(**kwargs)

        # For subscription products, we select either the list_price if no pricing correspond to the
        # SO recurrence_id or the best suited but we don't calculate the lowest price.
        pricelist = kwargs.get('pricelist', self.env['product.pricelist'])
        available_pricings = self.product_pricing_ids.filtered(lambda p: p.recurrence_id.duration == duration and p.recurrence_id.unit == unit)
        best_pricing_with_pricelist = self.env['product.pricing']
        best_pricing_without_pricelist = self.env['product.pricing']
        for pricing in available_pricings:
            # If there are any variants for the pricing, check if current product id is included in the variants ids.
            variants_ids = pricing.product_variant_ids.ids
            variant_pricing_compatibility = len(variants_ids) == 0 or len(variants_ids) > 0 and self.id in variants_ids
            if pricing.pricelist_id == pricelist and variant_pricing_compatibility:
                best_pricing_with_pricelist |= pricing
            elif not pricing.pricelist_id and variant_pricing_compatibility:
                best_pricing_without_pricelist |= pricing

        return best_pricing_with_pricelist[:1] or best_pricing_without_pricelist[:1] or self.env['product.pricing']

    @api.onchange('recurring_invoice')
    def _onchange_recurring_invoice(self):
        """
        Raise a warning if the user has checked 'Subscription Product'
        while the product has already been set as a 'Storable Product'.
        In this case, the 'Subscription Product' field is automatically
        unchecked.
        """
        return self.product_tmpl_id._onchange_recurring_invoice()

    @api.onchange('type')
    def _onchange_product_type(self):
        """
        Raise a warning if the user has selected 'Storable Product'
        while the product has already been set as a 'Subscription Product'.
        """
        return self.product_tmpl_id._onchange_product_type()
