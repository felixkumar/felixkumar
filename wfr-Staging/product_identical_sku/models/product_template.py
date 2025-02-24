import json

from odoo import fields, models, api


class ProductTemplateInherited(models.Model):
    _inherit = 'product.template'

    identical_sku_ids = fields.One2many(comodel_name="identical.sku", inverse_name='product_id',
                                        string="SKU Mapping")

    def update_shipstation_quantities(self):
        products_with_sku = self.search([('identical_sku_ids', '!=', False)])
        for product in products_with_sku:
            quants = self.env['stock.quant'].search([('product_id', 'in', product.product_variant_ids.ids)])
            identical_skus = product.identical_sku_ids
            warehouses = {}
            for quant in [q for q in quants if
                          'Stock' in q.location_id.display_name and 'OS&D' not in q.location_id.display_name]:
                available_qty = quant.available_quantity - quant.reserved_quantity
                if quant.warehouse_id in warehouses:
                    warehouses[quant.warehouse_id] += available_qty
                else:
                    warehouses[quant.warehouse_id] = available_qty
            for warehouse_id in warehouses:
                for sku in identical_skus:
                    curr_sku = sku.location_ids.filtered(lambda x: x.warehouse_id == warehouse_id)
                    if curr_sku:
                        curr_sku.forecasted_qty = warehouses[warehouse_id]
                        curr_sku.shipstation_qty = warehouses[warehouse_id]
                    else:
                        sku.location_ids.create(
                            {
                                'warehouse_id': warehouse_id.id,
                                'forecasted_qty': warehouses[warehouse_id],
                                'shipstation_qty': warehouses[warehouse_id],
                                'sku_id': sku.id
                            }
                        )

    def copy_identical_sku(self):
        products_with_sku = self.search([('identical_sku', '!=', False)])
        for product in products_with_sku:
            identical_skus = json.loads(product.identical_sku)
            lines = [(0, 0, {
                'name': sku,
                'product_id': product.id,
                'original_sku': product.default_code,
            }) for sku in identical_skus if sku not in product.identical_sku_ids.mapped('name')]
            product.write({
                'identical_sku_ids': lines
            })

