# -*- coding: utf-8 -*-
import logging
from collections import defaultdict

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_open_delivery_wizard(self):
        view_id = self.env.ref('delivery.choose_delivery_carrier_view_form').id
        if self.env.context.get('carrier_recompute'):
            name = _('Update shipping cost')
            carrier = self.carrier_id
        else:
            name = _('Add a shipping method')
            carrier = (
                self.with_company(self.company_id).partner_id.property_delivery_carrier_id
                or self.with_company(self.company_id).partner_id.commercial_partner_id.property_delivery_carrier_id
            )
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'choose.delivery.carrier',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
                'default_carrier_id': carrier.id,
            }
        }

    def _compute_bulk_weight_fedex(self):
        picking_weights = defaultdict(float)
        # Ordering by qty_done prevents the default ordering by groupby fields that can inject multiple Left Joins in the resulting query.
        res_groups = self.env['stock.move.line'].read_group(
            [('picking_id', 'in', self.ids), ('product_id', '!=', False), ('result_package_id', '=', False)],
            ['id:count'],
            ['picking_id', 'product_id', 'product_uom_id', 'reserved_qty'],
            lazy=False, orderby='reserved_qty asc'
        )
        products_by_id = {
            product_res['id']: (product_res['uom_id'][0], product_res['weight'])
            for product_res in
            self.env['product.product'].with_context(active_test=False).search_read(
                [('id', 'in', list(set(grp["product_id"][0] for grp in res_groups)))], ['uom_id', 'weight'])
        }
        for res_group in res_groups:
            uom_id, weight = products_by_id[res_group['product_id'][0]]
            uom = self.env['uom.uom'].browse(uom_id)
            product_uom_id = self.env['uom.uom'].browse(res_group['product_uom_id'][0])
            picking_weights[res_group['picking_id'][0]] += (
                res_group['__count']
                * product_uom_id._compute_quantity(res_group['reserved_qty'], uom)
                * weight
            )

        return picking_weights[self.id]
