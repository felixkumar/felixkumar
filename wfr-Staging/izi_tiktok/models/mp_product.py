from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from base64 import b64encode
from bs4 import BeautifulSoup
import requests
import json

class MPProduct(models.Model):
    _inherit = 'mp.product'

    PRODUCT_STATUS = [
        ('1', 'Draft'),
        ('2', 'Pending'),
        ('3', 'Failed'),
        ('4', 'Live'),
        ('5', 'Seller Deactivated'),
        ('6', 'Platform Deactivated'),
        ('7', 'Freeze'),
        ('8', 'Deleted'),
    ]

    tts_status = fields.Selection(string='TikTok Product Status', selection=PRODUCT_STATUS)
    tts_pd_category = fields.Char(string='TikTok Product Category') 
    tts_pd_brand = fields.Char(string='TikTok Product Brand')
    tts_product_attribute_ids = fields.One2many('mp.tiktok.product.attribute', 'mp_product_id', string='Product Attribute')

    @api.model
    def tiktok_product_field_mapping(self, mp_account_id, product_detail):
        # Functions
        def _handle_product_images(product_detail):
            image_res = [(5, 0, 0)]
            if product_detail.get('images'):
                image = product_detail['images'][0]
                for index, image_url in enumerate(image.get('url_list')):
                    # image_file = b64encode(requests.get(image_url).content).decode()
                    image_values = {
                        'mp_account_id': mp_account_id,
                        'mp_external_id': image.get('id'),
                        'sequence': index,
                        'name': image_url,
                        # 'image': image_file,
                    }
                    image_res.append((0, 0, image_values))
            return image_res
        
        def _handle_product_attribute(product_detail):
            pd_attr_res = [(5, 0, 0)]
            if product_detail.get('product_attributes'):
                pd_attribute = product_detail['product_attributes']
                for attr in pd_attribute:
                    if len(attr.get('values')) > 0:
                        pd_attribute_values = {
                            'mp_account_id': mp_account_id,
                            'mp_external_id': attr.get('id'),
                            'name': attr.get('name'),
                            'value_ids': [(5, 0, 0)],
                        }
                        for val in attr.get('values'):
                            pd_attribute_values['value_ids'].append((0, 0, {
                                'name': val.get('name'),
                                'value_id': val.get('id')
                            }))
                        pd_attr_res.append((0, 0, pd_attribute_values))
            return pd_attr_res

        skus = product_detail.get('skus')
        sku = skus[0] if skus else {}
        res = {
            'mp_account_id': mp_account_id,
            'name': product_detail.get('product_name'),
            'description_sale': BeautifulSoup(product_detail.get('description')).get_text(),
            'default_code': sku.get('seller_sku'),
            'weight': float(product_detail.get('package_weight', 0)),
            'length': product_detail.get('package_length', 0),
            'width': product_detail.get('package_width', 0),
            'height': product_detail.get('package_height', 0),
            'mp_external_id': product_detail.get('product_id'),
            'list_price': sku.get('price', {}).get('original_price', 0),
            'mp_product_image_ids': _handle_product_images(product_detail),
            'mp_product_wholesale_ids': False,
            'is_active': True if product_detail.get('product_status') == 4 else False,
            'tts_status': str(product_detail.get('product_status')),
            'tts_pd_category': '',
            'tts_pd_brand': '',
            'tts_product_attribute_ids': _handle_product_attribute(product_detail),
            'raw': json.dumps(product_detail, indent=4)
        }

        # TODO: Category, Brand
        for categ in product_detail.get('category_list'):
            if categ.get('is_leaf'):
                res.update({'tts_pd_category': categ.get('id')})
                break

        return res

    @api.model
    def tiktok_product_variant_field_mapping(self, mp_account_id, mp_product_id, variant_detail):
        attributes = variant_detail.get('sales_attributes')
        att_value_list = []

        # search warehouse tiktok
        MPTiktokWarehouse = self.env['mp.tiktok.warehouse']
        mp_tts_warehouse_rec = MPTiktokWarehouse.search([])
        mp_tts_warehouse = {}
        for warehouse in mp_tts_warehouse_rec:
            mp_tts_warehouse[warehouse.mp_external_id] = warehouse

        for attribute in attributes:
            att_value_list.append(attribute['value_name'])
        
        att_value = ','.join(att_value_list)
        # attribute = attributes[0] if attributes else False
        res = {
            'mp_account_id': mp_account_id,
            'mp_product_id': mp_product_id.id,
            'mp_external_id': variant_detail.get('id'),
            'tts_variant_id': variant_detail.get('id'),
            'name': '%s - (%s)' % (mp_product_id.name, att_value),
            'default_code': variant_detail.get('seller_sku'),
            'list_price': variant_detail.get('price', {}).get('original_price', 0),
            'image': False,
            'is_active': True,
            'stock_ids': [(5,0,0)],
            'raw': json.dumps(variant_detail, indent=4)

        }
        for stock in variant_detail.get('stock_infos'):
            stock_vals = {
                'tts_var_stock': stock.get('available_stock', 0),
                'warehouse_id': mp_tts_warehouse[stock['warehouse_id']].id if stock['warehouse_id'] in mp_tts_warehouse else False
            }        
            res['stock_ids'].append((0, 0, stock_vals))


        return res

    @api.model
    def tiktok_get_existing_products(self, mp_account_id):
        existing_products = self.search([('mp_account_id', '=', mp_account_id)])
        product_by_external_id = {}
        for product in existing_products:
            if product.mp_external_id:
                product_by_external_id[product.mp_external_id] = product
        return product_by_external_id

    @api.model
    def tiktok_get_existing_product_variants(self, mp_product_id):
        existing_variants = self.env['mp.product.variant'].search([('mp_product_id', '=', mp_product_id.id)])
        variant_by_external_id = {}
        for variant in existing_variants:
            if variant.mp_external_id:
                variant_by_external_id[variant.mp_external_id] = variant
        return variant_by_external_id

    @api.model
    def tiktok_product_save(self, mp_account_id, product_detail, product_by_external_id):
        product_id = product_detail['product_id']
        values = self.tiktok_product_field_mapping(mp_account_id, product_detail)
        if product_id in product_by_external_id:
            product_by_external_id.get(product_id).write(values)
            res_id = product_by_external_id.get(product_id)
        else:
            res_id = self.create(values)
        return res_id

    @api.model
    def tiktok_product_variant_save(self, mp_account_id, mp_product_id, product_detail, variant_by_external_id):
        skus = product_detail.get('skus', [])
        res_ids = []
        for sku in skus:
            values = self.tiktok_product_variant_field_mapping(mp_account_id, mp_product_id, sku)
            if sku['id'] in variant_by_external_id:
                variant_by_external_id.get(sku['id']).write(values)
                res_id = variant_by_external_id.get(sku['id']).id
            else:
                res_id = self.env['mp.product.variant'].create(values).id
            res_ids.append(res_id)
        
        tts_vaitant_exid = list(map(lambda x: str(x['id']), skus))
        for varid in variant_by_external_id:
            if varid not in tts_vaitant_exid:
                variant_by_external_id[varid].write({'is_active': False})

        return res_ids
