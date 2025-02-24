# -*- coding: utf-8 -*-
# Copyright 2023 IZI PT Solusi Usaha Mudah
import logging
import time
import hashlib
import hmac
import json
from odoo import api, fields, models
import requests
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

base_url = 'https://open-api.tiktokglobalshop.com'
auth_url = 'https://auth.tiktok-shops.com/oauth/authorize'
auth_base_url = 'https://auth.tiktok-shops.com'
auth_state = 'IZITIKTOKSHOP'
base_url = 'https://open-api.tiktokglobalshop.com'


class MarketplaceAccount(models.Model):
    _inherit = 'mp.account'

    READONLY_STATES = {
        'authenticated': [('readonly', True)],
        'authenticating': [('readonly', False)],
    }

    tts_app_key = fields.Char(string='App Key', required_if_marketplace="tiktok", states=READONLY_STATES)
    tts_app_secret = fields.Char(string='App Secret', required_if_marketplace="tiktok", states=READONLY_STATES)
    tts_access_token = fields.Text(string='Access Token', states=READONLY_STATES)
    tts_refresh_token = fields.Char(string='Refresh Token', states=READONLY_STATES)
    tts_shop_id = fields.Many2one(comodel_name="mp.tiktok.shop", string="Tiktok Current Shop")
    tts_state_order_ids = fields.Many2many(
        comodel_name='mp.tiktok.state.order', string='Default Status Order',
        help='To get specific order from tiktok. Get all order if this field is empty.')

    def tiktok_generate_sign(self, path, params):
        params = params.copy()
        if 'sign' in params:
            del params['sign']
        if 'access_token' in params:
            del params['access_token']
        signstring = ''
        for key in params:
            signstring += (key + str(params[key]))
        signstring = '%s%s%s%s' % (
            self.tts_app_secret, path, signstring, self.tts_app_secret)
        sign = hmac.new(self.tts_app_secret.encode(), msg=signstring.encode(), digestmod=hashlib.sha256).hexdigest()
        return sign

    def tiktok_request(self, method, path, body, params={}):
        url = base_url + path
        if not params:
            timestamp = int(time.time())
            shop = self.env['mp.tiktok.shop'].search([('mp_account_id', '=', self.id)], limit=1)
            shop_id = shop.shop_id
            params = {
                'app_key': self.tts_app_key,
                'access_token': self.tts_access_token,
                'shop_id': shop_id,
                'timestamp': timestamp,
            }
            params.update({
                'sign': self.tiktok_generate_sign(path, params),
            })

        request_parameters = {
            'method': method,
            'url': url,
            'headers': {
                'Content-Length': '0',
                'User-Agent': 'PostmanRuntime/7.17.1',
                'Content-Type': 'application/json',
            },
            'params': params,
        }
        if body and body != None and body != {}:
            request_parameters['json'] = body
        response = requests.request(**request_parameters)
        response = response.json()
        return response

    # @api.multi
    def tiktok_authenticate(self):
        state = '%s%s' % (auth_state, str(self.id))
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '%s?app_key=%s&state=%s' % (auth_url, self.tts_app_key, state)
        }

    def tiktok_refresh_token(self):
        _logger.info("Refresh token tiktok %s" % (self.id))
        url = auth_base_url + '/api/token/refreshToken'
        response = requests.request(**{
            'method': 'post',
            'url': url,
            'headers': {
                'Content-Length': '0',
                'User-Agent': 'PostmanRuntime/7.17.1',
                'Content-Type': 'application/json',
            },
            'json': {
                'app_key': self.tts_app_key,
                'app_secret': self.tts_app_secret,
                'refresh_token': self.tts_refresh_token,
                'grant_type': 'refresh_token',
            },
        })
        response = response.json()
        _logger.info("Response refresh token tiktok - %s" % str(response))
        # Success
        if response.get('code') == 0:
            self.write({
                'tts_access_token': response['data']['access_token'],
                'tts_refresh_token': response['data']['refresh_token'],
                'state': 'authenticated',
            })
        else:
            self.write({
                'state': 'authenticating',
            })

    def tiktok_get_access_token(self, code):
        _logger.info("Get access token tiktok %s - %s" % (self.id, code))
        url = auth_base_url + '/api/token/getAccessToken'
        response = requests.request(**{
            'method': 'post',
            'url': url,
            'headers': {
                'Content-Length': '0',
                'User-Agent': 'PostmanRuntime/7.17.1',
                'Content-Type': 'application/json',
            },
            'json': {
                'app_key': self.tts_app_key,
                'app_secret': self.tts_app_secret,
                'auth_code': code,
                'grant_type': 'authorized_code',
            },
        })
        response = response.json()
        _logger.info("Response access token tiktok - %s" % str(response))
        # Success
        if response.get('code') == 0:
            self.write({
                'tts_access_token': response['data']['access_token'],
                'tts_refresh_token': response['data']['refresh_token'],
                'state': 'authenticated',
            })

    def tiktok_get_shop(self):
        mp_account_ctx = self.generate_context()
        tiktok_shop_obj = self.env['mp.tiktok.shop'].with_context(mp_account_ctx)
        tiktok_shop_rec = tiktok_shop_obj.search([])
        tiktok_shop_by_exid = {}
        for tiktok_shop in tiktok_shop_rec:
            tiktok_shop_by_exid[tiktok_shop.mp_external_id] = tiktok_shop

        path = '/api/shop/get_authorized_shop'
        url = base_url + path
        timestamp = int(time.time())
        params = {
            'app_key': self.tts_app_key,
            'access_token': self.tts_access_token,
            'timestamp': timestamp
        }
        params.update({
            'sign': self.tiktok_generate_sign(path, params),
        })
        response = requests.request(**{
            'method': 'get',
            'url': url,
            'headers': {
                'Content-Length': '0',
                'User-Agent': 'PostmanRuntime/7.17.1',
                'Content-Type': 'application/json',
            },
            'params': params,
        })
        response = response.json()
        # Success
        if response.get('code') == 0:
            data = response.get('data')
            if 'shop_list' in data:
                for shop in data['shop_list']:
                    vals = {
                        'shop_id': shop['shop_id'],
                        'shop_name': shop['shop_name'],
                        'region': shop['region'],
                        'type': str(shop['type']),
                        'mp_account_id': self.id,
                        'raw': json.dumps(shop, indent=4),
                        # 'md5sign': self.generate_signature(shop),
                        'mp_external_id': shop['shop_id'],
                    }
                    if shop['shop_id'] not in tiktok_shop_by_exid:
                        shop_rec = tiktok_shop_obj.create(vals)
                    else:
                        shop_rec = tiktok_shop_by_exid[shop['shop_id']]
                        shop_rec.write(vals)
                self.write({'tts_shop_id': shop_rec.id})

    def tiktok_get_dependencies(self):
        self.ensure_one()
        self.tiktok_get_shop()
        self.tiktok_get_warehouse()
        self.tiktok_get_logistics()
        self.get_tiktok_brand()
        # self.tiktok_get_categories()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }

    def tiktok_get_products(self, **kw):
        rec = self
        if kw.get('id', False):
            rec = self.browse(kw.get('id'))
        rec.ensure_one()
        MPProduct = self.env['mp.product']
        index = 0
        page_size = 100
        page_number = 1
        total = 1

        if kw.get('product_ids'):
            for product in kw.get('product_ids'):
                response = rec.tiktok_get_product_detail(product)
                if response.get('code') == 0:
                    product_by_external_id = MPProduct.tiktok_get_existing_products(rec.id)
                    product_detail = response.get('data')
                    mp_account_id = rec.id
                    mp_product_id = MPProduct.tiktok_product_save(
                        mp_account_id, product_detail, product_by_external_id)
                    # Get Existing Variant
                    variant_by_external_id = MPProduct.tiktok_get_existing_product_variants(mp_product_id)
                    MPProduct.tiktok_product_variant_save(
                        mp_account_id, mp_product_id, product_detail, variant_by_external_id)
        else:
            while (index < total):
                response = rec.tiktok_request('post', '/api/products/search', {
                    'page_size': page_size,
                    'page_number': page_number,
                    'search_status': 0,
                    'seller_sku_list': []
                })
                # Success
                if response.get('code') == 0:
                    # Get Existing Product
                    product_by_external_id = MPProduct.tiktok_get_existing_products(rec.id)
                    # Get Product Detail
                    data = response.get('data')
                    for product in data['products']:
                        response = rec.tiktok_get_product_detail(product)
                        if response.get('code') == 0:
                            product_detail = response.get('data')
                            mp_account_id = rec.id
                            mp_product_id = MPProduct.tiktok_product_save(
                                mp_account_id, product_detail, product_by_external_id)
                            # Get Existing Variant
                            variant_by_external_id = MPProduct.tiktok_get_existing_product_variants(mp_product_id)
                            MPProduct.tiktok_product_variant_save(
                                mp_account_id, mp_product_id, product_detail, variant_by_external_id)

                    total = data.get('total')
                    page_number += 1
                    index = (page_number-1)*page_size
                    if index >= total:
                        break
                else:
                    raise UserError(str(response))
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }

    def tiktok_get_warehouse(self):
        mp_account_ctx = self.generate_context()
        tiktok_warehouse_obj = self.env['mp.tiktok.warehouse'].with_context(mp_account_ctx)
        tiktok_warehouse_rec = tiktok_warehouse_obj.search([])
        tiktok_warehouse_by_exid = {}
        for tiktok_warehouse in tiktok_warehouse_rec:
            tiktok_warehouse_by_exid[tiktok_warehouse.mp_external_id] = tiktok_warehouse

        response = self.tiktok_request('get', '/api/logistics/get_warehouse_list', {})
        # Success
        if response.get('code') == 0:
            data = response.get('data')
            if 'warehouse_list' in data:
                for warehouse in data['warehouse_list']:
                    vals = {
                        'warehouse_id': warehouse['warehouse_id'],
                        'warehouse_name': warehouse['warehouse_name'],
                        'warehouse_type': str(warehouse['warehouse_type']),
                        'warehouse_sub_type': str(warehouse['warehouse_sub_type']),
                        'warehouse_effect_status': str(warehouse['warehouse_effect_status']),
                        'region': warehouse.get('warehouse_address').get('region',''),
                        'state': warehouse.get('warehouse_address').get('state',''),
                        'city': warehouse.get('warehouse_address').get('city',''),
                        'district': warehouse.get('warehouse_address').get('district',''),
                        'town': warehouse.get('warehouse_address').get('town',''),
                        'zipcode': warehouse.get('warehouse_address').get('zipcode',''),
                        'phone': warehouse.get('warehouse_address').get('phone',''),
                        'contact_person': warehouse.get('warehouse_address').get('contact_person',''),
                        'mp_account_id': self.id,
                        'raw': json.dumps(warehouse, indent=4),
                        # 'md5sign': self.generate_signature(shop),
                        'mp_external_id': warehouse['warehouse_id'],
                    }
                    if warehouse['warehouse_id'] not in tiktok_warehouse_by_exid:
                        warehouse_rec = tiktok_warehouse_obj.create(vals)
                    else:
                        warehouse_rec = tiktok_warehouse_by_exid[warehouse['warehouse_id']]
                        warehouse_rec.write(vals)

    def tiktok_get_product_detail(self, product):
        # Custom Parameters
        path = '/api/products/details'
        product_id = product.get('id')
        timestamp = int(time.time())
        params = {
            'app_key': self.tts_app_key,
            'access_token': self.tts_access_token,
            'product_id': product_id,   
            'timestamp': timestamp,
        }
        params.update({
            'sign': self.tiktok_generate_sign(path, params),
        })
        response = self.tiktok_request('get', path, {}, params)
        return response

    def tiktok_get_categories(self):
        mp_account_ctx = self.generate_context()
        tiktok_category_obj = self.env['mp.tiktok.product.category'].with_context(mp_account_ctx)
        tiktok_category_rec = tiktok_category_obj.search([])
        tiktok_category_by_exid = {}
        for tiktok_category in tiktok_category_rec:
            tiktok_category_by_exid[tiktok_category.mp_external_id] = tiktok_category

        response = self.tiktok_request('get', '/api/products/categories', {})
        # Success
        if response.get('code') == 0:
            data = response.get('data')
            if 'category_list' in data:
                for category in data['category_list']:
                    vals = {
                        'category_id': category['id'],
                        'parent_id': category['parent_id'],
                        'local_display_name': category['local_display_name'],
                        'is_leaf': category['is_leaf'],
                        'mp_account_id': self.id,
                        'raw': json.dumps(category, indent=4),
                        # 'md5sign': self.generate_signature(shop),
                        'mp_external_id': category['id'],
                    }
                    if category['id'] not in tiktok_category_by_exid:
                        category_rec = tiktok_category_obj.create(vals)
                    else:
                        category_rec = tiktok_category_by_exid[category['id']]
                        category_rec.write(vals)

    def tiktok_get_sale_order(self, **kwargs):
        rec = self
        mp_account_ctx = self.generate_context()
        order_obj = self.env['sale.order'].with_context(mp_account_ctx)
        if kwargs.get('params', False) == 'by_mp_invoice_number':
            self.tiktok_process_single_order(kwargs.get('mp_invoice_number'))
            return True
        if kwargs.get('id', False):
            rec = self.browse(kwargs.get('id'))
        rec.ensure_one()
        tts_orders_by_mpexid = {}
        tts_orders = order_obj.search([('mp_account_id', '=', self.id)])
        for tts_order in tts_orders:
            tts_orders_by_mpexid[tts_order.mp_invoice_number] = tts_order

        if kwargs.get('params') == 'by_date_range':
            update_time_from = int(datetime.timestamp(kwargs.get('from_date')))
            update_time_to = int(datetime.timestamp(kwargs.get('to_date')))
            more = True
            cursor = False
            index = 0
            order_data_raw = []
            force_update_ids = []
            while (more):
                params = {
                    'page_size': 50,
                    'update_time_from': update_time_from,
                    'update_time_to': update_time_to,
                    # 'order_status': 100,
                    # 'cursor': '',
                }
                if cursor:
                    params['cursor'] = cursor
                elif index > 0:
                    raise UserError('No Cursor Found')

                response = self.tiktok_request('post', '/api/orders/search', params)
                # Success
                if response.get('code') == 0:
                    data = response.get('data')
                    more = data.get('more')
                    cursor = data.get('next_cursor')
                    print('Get Order List Index %s' % str(index))

                    order_id_list = []
                    if data.get('total'):
                        for data_order in data.get('order_list', 0):
                            order_status = data_order['order_status']
                            if data_order['order_id'] in tts_orders_by_mpexid:
                                existing_order = tts_orders_by_mpexid[data_order['order_id']]
                                mp_status_changed = existing_order.tts_order_status != str(order_status)
                                if mp_status_changed:
                                    order_id_list.append(data_order['order_id'])
                                elif mp_account_ctx.get('force_update'):
                                    force_update_ids.append(existing_order.id)
                                    order_id_list.append(data_order['order_id'])
                                else:
                                    continue
                            else:
                                existing_order = False
                                mp_status_changed = False
                                if order_status == 140 and not self.get_cancelled_orders:
                                    continue
                                if order_status == 100 and not self.get_unpaid_orders:
                                    continue
                                state_order = rec.tts_state_order_ids.mapped('code')  # for specific status order
                                allowed_order = order_status in state_order if state_order else order_status
                                if allowed_order:
                                    order_id_list.append(data_order['order_id'])

                        # Get Order Detail
                        response_order_detail = self.tiktok_request('post', '/api/orders/detail/query', {
                            'order_id_list': order_id_list,
                        })
                        if response_order_detail.get('code') == 0:
                            detail_data = response_order_detail.get('data')
                            order_data_raw.extend(detail_data['order_list'])
                    else:
                        more = False
                        break
                else:
                    more = False
                    break

                index += 1
            self.tiktok_mapping_orders(order_data_raw, force_update_ids)
        elif kwargs.get('by_mp_invoice_number'):
            self.tiktok_process_single_order(kwargs.get('mp_invoice_number'))

    def tiktok_get_orders(self, **kwargs):
        rec = self
        if kwargs.get('id', False):
            rec = self.browse(kwargs.get('id'))
        rec.ensure_one()
        time_range = kwargs.get('time_range', False)
        if time_range:
            if time_range == 'last_hour':
                from_time = datetime.now() - timedelta(hours=1)
                to_time = datetime.now()
            elif time_range == 'last_3_days':
                from_time = datetime.now() - timedelta(days=3)
                to_time = datetime.now()
            kwargs.update({
                'from_date': from_time,
                'to_date': to_time
            })
        rec.tiktok_get_sale_order(**kwargs)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }

    def tiktok_mapping_orders(self, order_data_raw, force_update_ids):
        mp_account_ctx = self.generate_context()
        order_obj = self.env['sale.order'].with_context(mp_account_ctx)
        # Start mapping order data
        tts_order_raws, tts_order_sanitizeds = [], []
        for data in order_data_raw:
            tts_order_data_raw, tts_order_data_sanitized = order_obj.with_context(
                mp_account_ctx)._prepare_mapping_raw_data(raw_data=data)
            tts_order_raws.append(tts_order_data_raw)
            tts_order_sanitizeds.append(tts_order_data_sanitized)

        if force_update_ids:
            order_obj = order_obj.with_context(dict(order_obj._context.copy(), **{
                'force_update_ids': force_update_ids
            }))

        if tts_order_raws and tts_order_sanitizeds:
            check_existing_records_params = {
                'identifier_field': 'tts_order_id',
                'raw_data': tts_order_raws,
                'mp_data': tts_order_sanitizeds,
                'multi': isinstance(tts_order_sanitizeds, list)
            }
            check_existing_records = order_obj.with_context(mp_account_ctx).check_existing_records(
                **check_existing_records_params)
            order_obj.with_context(mp_account_ctx).handle_result_check_existing_records(check_existing_records)

    def tiktok_process_single_order(self, tts_order_id, sale_order=False):
        response_order_detail = self.tiktok_request('post', '/api/orders/detail/query', {
            'order_id_list': [tts_order_id],
        })
        if response_order_detail.get('code') == 0:
            order_data_raw = response_order_detail.get('data').get('order_list')
            force_ids = []
            if sale_order:
                force_ids = [sale_order.id]
            self.tiktok_mapping_orders(order_data_raw, force_ids)

    def tiktok_ship_order(self, sale_order):
        response_ship_order = self.tiktok_request('post', '/api/fulfillment/rts', {
            'package_id': sale_order.tts_package_id,
        })
        if response_ship_order.get('code') == 0:
            if sale_order.state == 'draft':
                sale_order.action_confirm()
            self.tiktok_process_single_order(sale_order.tts_order_id, sale_order)

    def tiktok_print_label(self, sale_order):
        res = {
            'message': 'Cannot Print Label',
            'url': False,
        }
        # Custom Parameters
        path = '/api/logistics/shipping_document'
        order_id = sale_order.tts_order_id
        timestamp = int(time.time())
        params = {
            'app_key': self.tts_app_key,
            'access_token': self.tts_access_token,
            'document_type': 'SHIPPING_LABEL',
            'order_id': order_id,
            'timestamp': timestamp,
        }
        params.update({
            'sign': self.tiktok_generate_sign(path, params),
        })
        response = self.tiktok_request('get', path, {}, params)
        if response.get('code') == 0:
            if response.get('data'):
                res.update({
                    'message': False,
                    'url': response.get('data').get('doc_url'),
                })
        else:
            if response.get('message'):
                res.update({
                    'message': response.get('message'),
                })
        return res

    def tiktok_get_logistics(self):
        mp_delivery_product_tmpl = self.env.ref('izi_marketplace.product_tmpl_mp_delivery', raise_if_not_found=False)
        mp_account_ctx = self.generate_context()
        tiktok_logistic_obj = self.env['mp.tiktok.logistic'].with_context(mp_account_ctx)
        tiktok_logistic_record = self.env['mp.tiktok.logistic']
        tiktok_logistic_provider_obj = self.env['mp.tiktok.logistic.provider'].with_context(mp_account_ctx)
        tiktok_logistic_rec = tiktok_logistic_obj.search([('shop_id', '=', self.tts_shop_id.id)])
        tiktok_logistic_by_exid = {}
        for tiktok_logistic in tiktok_logistic_rec:
            tiktok_logistic_by_exid[tiktok_logistic.mp_external_id] = tiktok_logistic

        response = self.tiktok_request('get', '/api/logistics/shipping_providers', {})

        if response.get('code') == 0:
            data = response.get('data')
            for logistic in data['delivery_option_list']:
                vals = {
                    'delivery_option_id': logistic['delivery_option_id'],
                    'delivery_option_name': logistic['delivery_option_name'],
                    'item_max_weight': logistic['item_weight_limit']['max_weight'],
                    'item_min_weight': logistic['item_weight_limit']['min_weight'],
                    'item_dimension_length_limit': logistic['item_dimension_limit']['length'],
                    'item_dimension_width_limit': logistic['item_dimension_limit']['width'],
                    'item_dimension_height_limit': logistic['item_dimension_limit']['height'],
                    'shop_id': self.tts_shop_id.id,
                    'mp_account_id': self.id,
                    'raw': json.dumps(logistic, indent=4),
                    # 'md5sign': self.generate_signature(shop),
                    'mp_external_id': logistic['delivery_option_id'],
                    'product_id': mp_delivery_product_tmpl.product_variant_id.id if mp_delivery_product_tmpl else False
                }
                if logistic['delivery_option_id'] not in tiktok_logistic_by_exid:
                    tiktok_logistic_record |= tiktok_logistic_obj.create(vals)
                else:
                    logistic_rec = tiktok_logistic_by_exid[logistic['delivery_option_id']]
                    logistic_rec.write(vals)
                    tiktok_logistic_record |= logistic_rec

            for record in tiktok_logistic_record:
                tiktok_logistic_provider_rec = tiktok_logistic_provider_obj.search([('logistic_id', '=', record.id)])
                tiktok_logistic_provider_by_exid = {}
                for tiktok_logistic_provider in tiktok_logistic_provider_rec:
                    tiktok_logistic_provider_by_exid[tiktok_logistic_provider.mp_external_id] = tiktok_logistic_provider
                tts_logistic_raw = json.loads(record.raw, strict=False)
                tts_logistic_provider = [dict(tp_logistic_service, **dict([('logistic_id', record.id)])) for
                                         tp_logistic_service in tts_logistic_raw['shipping_provider_list']]

                for logistic_provier in tts_logistic_provider:
                    vals = {
                        'shipping_provider_id': logistic_provier['shipping_provider_id'],
                        'shipping_provider_name': logistic_provier['shipping_provider_name'],
                        'mp_account_id': self.id,
                        'raw': json.dumps(logistic_provier, indent=4),
                        # 'md5sign': self.generate_signature(shop),
                        'mp_external_id': logistic_provier['shipping_provider_id'],
                        'logistic_id': logistic_provier['logistic_id'],
                        'product_id': mp_delivery_product_tmpl.product_variant_id.id if mp_delivery_product_tmpl else False,
                    }
                    if logistic_provier['shipping_provider_id'] not in tiktok_logistic_provider_by_exid:
                        logistic_provider_rec = tiktok_logistic_provider_obj.create(vals)
                    else:
                        logistic_provider_rec = tiktok_logistic_provider_by_exid[logistic_provier['shipping_provider_id']]
                        logistic_provider_rec.write(vals)

    def get_tiktok_brand(self):
        mp_account_ctx = self.generate_context()
        tiktok_brand_obj = self.env['mp.tiktok.brand'].with_context(mp_account_ctx)
        tiktok_brand_rec = tiktok_brand_obj.search([])
        tiktok_brand_by_exid = {}
        for tiktok_brand in tiktok_brand_rec:
            tiktok_brand_by_exid[tiktok_brand.mp_external_id] = tiktok_brand

        response = self.tiktok_request('get', '/api/products/brands', {})
        # Success
        if response.get('code') == 0:
            data = response.get('data')
            if 'brand_list' in data:
                for brand in data['brand_list']:
                    vals = {
                        'brand_id': brand['id'],
                        'brand_name': brand['name'],
                        'mp_account_id': self.id,
                        'raw': json.dumps(brand, indent=4),
                        # 'md5sign': self.generate_signature(shop),
                        'mp_external_id': brand['id'],
                    }
                    if brand['id'] not in tiktok_brand_by_exid:
                        brand_rec = tiktok_brand_obj.create(vals)
                    else:
                        brand_rec = tiktok_brand_by_exid[brand['id']]
                        brand_rec.write(vals)

    def tiktok_set_product(self, **kw):
        self.ensure_one()
        mp_product_ids = []

        if kw.get('mode') == 'stock_only':
            base_payload = {
                'product_id': '',
                'skus': []
            }
            try:
                for data in kw.get('data', []):
                    if data['product_obj']._name == 'mp.product':
                        base_payload.update({
                            'product_id': data['product_obj'].mp_external_id
                        })
                        base_payload['skus'].append({
                            'stock_infos': [{
                                'available_stock': data['stock']
                            }]
                        })
                        mp_product_ids.append({'id': data['product_obj'].mp_external_id})
                    elif data['product_obj']._name == 'mp.product.variant':
                        base_payload.update({
                            'product_id': data['product_obj'].mp_product_id.mp_external_id
                        })
                        base_payload['skus'].append({
                            'id': data['product_obj'].mp_external_id,
                            'stock_infos': [{
                                'available_stock': data['stock']
                            }]
                        })
                        mp_product_ids.append({'id': data['product_obj'].mp_product_id.mp_external_id})
                response = self.tiktok_request('put', '/api/products/stocks', base_payload)
                self.tiktok_get_products(**{'product_ids': mp_product_ids})
            except Exception as e:
                pass
        if kw.get('mode') == 'price_only':
            base_payload = {
                'product_id': '',
                'skus': []
            }
            try:
                for data in kw.get('data', []):
                    if data['product_obj']._name == 'mp.product':
                        base_payload.update({
                            'product_id': data['product_obj'].mp_external_id
                        })
                        base_payload['skus'].append({
                            'original_price': data['price']
                        })
                        mp_product_ids.append({'id': data['product_obj'].mp_external_id})
                    elif data['product_obj']._name == 'mp.product.variant':
                        base_payload.update({
                            'product_id': data['product_obj'].mp_product_id.mp_external_id
                        })
                        base_payload['skus'].append({
                            'id': data['product_obj'].mp_external_id,
                            'original_price': str(data['price'])
                        })
                        mp_product_ids.append({'id': data['product_obj'].mp_product_id.mp_external_id})
                response = self.tiktok_request('put', '/api/products/prices', base_payload)
                self.tiktok_get_products(**{'product_ids': mp_product_ids})
            except Exception as e:
                pass
        if kw.get('mode') == 'activation':
            try:
                for data in kw.get('data', []):
                    base_payload = {
                        'product_ids': [data['product_obj'].mp_external_id]
                    }
                    if data['product_obj']._name == 'mp.product.variant':
                        base_payload.update({'product_ids': [data['product_obj'].mp_product_id.mp_external_id]})
                    path = '/api/products/activate' if data['activate'] else '/api/products/inactivated_products'
                    response = self.tiktok_request('post', path, base_payload)
                    data['product_obj'].write({'active': data['activate']})
            except Exception as e:
                pass
        if kw.get('mode') == 'detail':
            # Mandatory field
            base_payload = {
                'product_id': '',
                'product_name': '',
                'description': '',
                'category_id': '',
                'package_weight': '',
                'skus': [],
                'images': []
            }
            try:
                for data in kw.get('data', []):
                    if len(data.name) < 25:
                        raise UserError('Product name must have at least 25 Character')
                    
                    base_payload.update({
                        'product_id': data.mp_product_id.mp_external_id,
                        'product_name': data.name,
                        'description': data.description,
                        'category_id': data.mp_product_id.tts_pd_category,
                        'package_weight': data.weight,
                        'package_length': int(data.length),
                        'package_height': int(data.height),
                        'package_width': int(data.width),
                        'product_attributes': []
                    })
                    variants = data.variant_ids
                    for var in variants:
                        sku_payload = {
                            'id' : var.mp_external_id,
                            'original_price': var.mp_product_variant_id.list_price,
                            'seller_sku': var.sku if len(data.mp_product_id.mp_product_variant_ids) > 1 else data.sku,
                            'stock_infos': [],
                        }

                        # prepare sales attribute for sku
                        key_mapping = {
                            'id': 'attribute_id',
                            'name': 'attribute_name',
                            'value_name': 'custom_value'
                        }
                        sales_attributes_raw = json.loads(var.raw).get('sales_attributes')
                        sales_attributes = [{key_mapping.get(key, key): value for key, value in d.items()} for d in sales_attributes_raw]

                        sku_payload.update({
                            'sales_attributes': sales_attributes
                        })

                        # stock
                        for stock in var.stock_ids:
                            stock_vals = {
                                'warehouse_id': stock.warehouse_id.mp_external_id,
                                'available_stock': stock.tts_var_stock
                            }
                            sku_payload['stock_infos'].append(stock_vals)
                        
                        base_payload['skus'].append(sku_payload)
                    
                    # attributes
                    for attr in data.mp_product_id.tts_product_attribute_ids:
                        pd_attribute_vals = {
                            'attribute_id': attr.mp_external_id,
                            'attribute_values': []
                        }
                        for attr_value in attr.value_ids:
                            pd_attribute_vals['attribute_values'].append({
                                'value_id': attr_value.value_id,
                                'value_name': attr_value.name
                            })
                        base_payload['product_attributes'].append(pd_attribute_vals)

                    # images
                    for image in data.mp_product_id.mp_product_image_ids:
                        image_vals = {
                            'id': image.mp_external_id
                        }
                        base_payload['images'].append(image_vals)
                    # else:
                    #     base_payload.update({
                    #         'product_id': data['product_obj'].mp_product_id.mp_external_id
                    #     })
                    #     base_payload['skus'].append({
                    #         'id': data['product_obj'].mp_external_id,
                    #         'original_price': data['price']
                    #     })
                    if not base_payload['skus']:
                        raw = json.loads(data.mp_product_id.raw)
                        skus_data = raw['skus']
                        skus_data[0]['seller_sku'] = data.sku
                        skus_data[0]['original_price'] = skus_data[0]['price']['original_price']
                        del skus_data[0]['price']
                        base_payload['skus'].append(skus_data[0])
                    mp_product_ids.append({'id': data.mp_product_id.mp_external_id})
                    response = self.tiktok_request('put', '/api/products', base_payload)
                    if response.get('message') != 'Success':
                        raise UserError(response.get('message'))
                # time.sleep(15)
                self.tiktok_get_products(**{'product_ids': mp_product_ids})
            except Exception as e:
                raise UserError(str(e))


    def tiktok_product_refetch(self, datas=[]):
        products = []
        for pd_id in datas:
            products.append({'id': pd_id})
        if products:
            self.tiktok_get_products(**{'product_ids': products})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }
    
    def tiktok_get_order_reverse(self):
        reverse_datas = []
        cursor = 0
        more = True
        reverse_order = False
        while(more):
            response_get_order_reverse = self.tiktok_request('post','/api/reverse/reverse_order/list', {
                'offset': 0,
                'size': 100,
                'reverse_type': 2
            })
            if response_get_order_reverse.get('code') == 0:
                reverse_datas.extend(response_get_order_reverse['data']['reverse_list'])
            more = response_get_order_reverse.get('data').get('more')
            cursor += 100
        
        return reverse_datas