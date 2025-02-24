# -*- coding: utf-8 -*-
# Copyright 2023 IZI PT Solusi Usaha Mudah

from datetime import datetime, timezone
import time
import json
import requests
import base64

from odoo import api, fields, models
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError, UserError

from odoo.addons.izi_marketplace.objects.utils.tools import json_digger


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def tiktok_add_rec_mp_field_mapping(self, mp_field_mappings=None):
        res = super(SaleOrder, self).tiktok_add_rec_mp_field_mapping(mp_field_mappings=mp_field_mappings)

        res.update({'mp_recipient_address_full': ('recipient_address/address_detail', None)})
        res.update({'mp_recipient_address_zip': ('recipient_address/zipcode', None)})

        return res

    @api.model
    def lookup_partner_shipping(self, order_values, default_customer=None):
        partner_obj = self.env['res.partner']
        mp_account_id = order_values.get('mp_account_id')
        if not default_customer:
            default_customer = partner_obj
        partner_shipping = partner_obj
        partner_shipping_values = {
            'name': order_values.get('mp_recipient_address_name'),
            'phone': order_values.get('mp_recipient_address_phone'),
            'street': order_values.get('mp_recipient_address_full'),
            'zip': order_values.get('mp_recipient_address_zip')
        }

        # Started custom code =================================================================

        if order_values.get('mp_recipient_address_district'):
            partner_shipping_values.update({'street2': order_values.get('mp_recipient_address_district')})
        if order_values.get('mp_recipient_address_city'):
            partner_shipping_values.update({'city': order_values.get('mp_recipient_address_city')})
        if order_values.get('mp_recipient_address_country') and order_values.get('mp_recipient_address_state'):
            country_id = self.env['res.country'].search([('name', '=', order_values.get('mp_recipient_address_country'))], limit=1)
            if country_id:
                state_id = self.env['res.country.state'].search(
                    [('name', '=', order_values.get('mp_recipient_address_state')), ('country_id', '=', country_id.id)],
                    limit=1)
                partner_shipping_values.update({'state_id': state_id.id, 'country_id': country_id.id})

        # End custom code =================================================================

        if default_customer.exists():  # Then look for child partner (delivery address) of default customer
            if order_values.get('mp_recipient_address_phone'):
                if mp_account_id not in default_customer.mp_account_ids.ids:
                    default_customer.write({
                        'mp_account_ids': [(4, mp_account_id)]
                    })
                partner_shipping = partner_obj.search([
                    ('parent_id', '=', default_customer.id),
                    ('phone', '=', order_values.get('mp_recipient_address_phone'))
                ], limit=1)
            if not partner_shipping.exists():  # Then create new child partner of default customer
                partner_shipping_values.update({'parent_id': default_customer.id, 'type': 'delivery'})
                partner_shipping = partner_obj.create(partner_shipping_values)
        else:  # Then look for child partner (delivery address) first
            if order_values.get('mp_recipient_address_phone'):
                partner_shipping = partner_obj.search([
                    ('parent_id', '!=', False),
                    ('type', '=', 'delivery'),
                    ('phone', '=', order_values.get('mp_recipient_address_phone'))
                ], limit=1)
                if not partner_shipping.exists():  # Then look for parent partner
                    partner = partner_obj.search([
                        ('parent_id', '=', False),
                        ('type', '=', 'contact'),
                        ('phone', '=', order_values.get('mp_recipient_address_phone'))
                    ], limit=1)
                    if not partner.exists():  # Then create partner
                        partner_values = partner_shipping_values.copy()
                        partner_values.update({
                            'type': 'contact',
                            'mp_account_ids': [(4, mp_account_id)]
                        })
                        partner = partner_obj.create(partner_values)
                    # Then pass it to this method recursively
                    return self.lookup_partner_shipping(order_values, default_customer=partner)
        # Finally return the partner shipping
        return partner_shipping
