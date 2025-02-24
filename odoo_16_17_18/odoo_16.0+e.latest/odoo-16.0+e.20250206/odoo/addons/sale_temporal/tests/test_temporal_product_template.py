from odoo import Command

from odoo.addons.product.tests.common import ProductVariantsCommon


class TestSaleTemporalProduct(ProductVariantsCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.recurrence_weekly = cls.env.ref('sale_temporal.recurrence_weekly')
        cls.recurrence_monthly = cls.env.ref('sale_temporal.recurrence_monthly')
        for sofa in cls.product_template_sofa.product_variant_ids:
            cls.env['product.pricing'].create([{
                'product_template_id': cls.product_template_sofa.id,
                'product_variant_ids': [Command.link(sofa.id)],
                'pricelist_id': cls.pricelist.id,
                'recurrence_id': cls.recurrence_weekly.id,
                'price': 10.0,
            }, {
                'product_template_id': cls.product_template_sofa.id,
                'product_variant_ids': [Command.link(sofa.id)],
                'pricelist_id': cls.pricelist.id,
                'recurrence_id': cls.recurrence_monthly.id,
                'price': 25.0,
           }])

    def test_copy_product_variant_pricings(self):
        sofa_template = self.product_template_sofa
        pricings_1 = sofa_template.product_pricing_ids
        pricings_2 = sofa_template.copy().product_pricing_ids
        self.assertEqual(
            len(pricings_2.product_variant_ids),
            len(pricings_1.product_variant_ids),
            "Copied pricings should apply to an equal amount of products",
        )
        self.assertNotEqual(
            pricings_2.product_variant_ids,
            pricings_1.product_variant_ids,
            "Copied pricings shouldn't be linked to the original products",
        )
        for pricing_1 in pricings_1:
            sofa = pricing_1.product_variant_ids
            pav_ids = sofa.product_template_attribute_value_ids.product_attribute_value_id.ids
            pricing_2 = pricings_2.filtered(
                lambda p:
                    pricing_1.price == p.price
                    and p.product_variant_ids
                        .product_template_attribute_value_ids
                        .product_attribute_value_id
                        .ids == pav_ids
            )
            self.assertEqual(pricing_2.pricelist_id, pricing_1.pricelist_id)
            self.assertEqual(pricing_2.recurrence_id, pricing_1.recurrence_id)
