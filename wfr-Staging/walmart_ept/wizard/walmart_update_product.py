from odoo import models

class WalmartUpdateProductStock(models.TransientModel):
    _name = 'walmart.update.product.stock.ept'
    _description = "Walmart Update Product Stock"

    def update_stock_in_walmart(self):
        """
            Update stock in walmart for selected products
        :return: None
        """
        walmart_offer_obj = self.env['walmart.offer.ept']

        active_ids = self._context.get('active_ids', [])
        walmart_products = walmart_offer_obj.browse(active_ids)
        instance_ids = walmart_products.mapped('marketplace_id')
        for instance_id in instance_ids:
            walmart_offer_obj.export_stock_in_walmart(instance_id, walmart_products.filtered(
                    lambda prod: prod.marketplace_id.id == instance_id.id))

class WalmartUpdateProductPrice(models.TransientModel):
    _name = 'walmart.update.product.price.ept'
    _description = "Walmart Update Product Price"

    def update_price_in_walmart(self):
        """
            Update price of selected products in walmart
        :return: None
        """
        walmart_offer_obj = self.env['walmart.offer.ept']

        active_ids = self._context.get('active_ids', [])
        walmart_products = walmart_offer_obj.browse(active_ids)
        instance_ids = walmart_products.mapped('marketplace_id')
        for instance_id in instance_ids:
            walmart_offer_obj.export_price_in_walmart(instance_id, walmart_products.filtered(
                    lambda prod: prod.marketplace_id.id == instance_id.id))

class WalmartRetireProduct(models.TransientModel):
    _name = 'walmart.retire.product.ept'
    _description = "Walmart Retire a Product"

    # FIXME: Implement this feature after proper analysis as it is deleting the product.
    def update_retire_product_in_walmart(self):
        """
            Delete the product from walmart
        :return:
        """
        return True
        # walmart_instace_obj = self.env['walmart.marketplace.ept']
        # walmart_offer_obj = self.env['walmart.offer.ept']
        #
        # active_ids = self._context.get('active_ids', [])
        # instances = walmart_instace_obj.search([('state', '=', 'confirmed')])
        # for instance_id in instances:
        #     walmart_products = walmart_offer_obj.search(
        #         [('id', 'in', active_ids), ('marketplace_id', '=', instance_id.id)])
        #     if walmart_products:
        #         walmart_offer_obj.walmart_retire_products_ept(instance_id, walmart_products)
