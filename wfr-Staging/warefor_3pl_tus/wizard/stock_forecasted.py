# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
import copy

from odoo import api, models
from odoo.tools import float_compare, float_is_zero, format_date, float_round


class ReplenishmentReport(models.AbstractModel):
    _inherit = 'report.stock.report_product_product_replenishment'

    def _serialize_docs(self, docs, product_template_ids=False, product_variant_ids=False):
        """
        Since conversion from report to owl client_action, adapt/override this method to make records available from js code.
        """
        res = copy.copy(docs)
        if product_template_ids:
            res['product_templates'] = docs['product_templates'].read(fields=['id', 'display_name'])
            product_variants = []
            for pv in docs['product_variants']:
                product_variants.append({
                        'id' : pv.id,
                        'combination_name' : pv.product_template_attribute_value_ids._get_combination_name(),
                    })
            res['product_variants'] = product_variants
        elif product_variant_ids:
            res['product_variants'] = docs['product_variants'].read(fields=['id', 'display_name'])

        res['lines'] = []
        for index, line in enumerate(docs['lines']):
            res['lines'].append({
                'index': index,
                'document_in' : {
                    '_name' : line['document_in']._name,
                    'id' : line['document_in']['id'],
                    'name' : line['document_in'].with_company(6)['name'],
                } if line['document_in'] else False,
                'document_out' : {
                    '_name' : line['document_out']._name,
                    'id' : line['document_out']['id'],
                    'name' : line['document_out'].with_company(6)['name'],
                } if line['document_out'] else False,
                'uom_id' : line['uom_id'].read()[0],
                'move_out' : line['move_out'].read(self._fields_for_serialized_moves())[0] if line['move_out'] else False,
                'move_in' : line['move_in'].read(self._fields_for_serialized_moves())[0] if line['move_in'] else False,
                'product': line['product'],
                'replenishment_filled': line['replenishment_filled'],
                'receipt_date': line['receipt_date'],
                'delivery_date': line['delivery_date'],
                'is_late': line['is_late'],
                'quantity': line['quantity'],
                'reservation': line['reservation'],
                'is_matched': line['is_matched'],
            })
            if line['move_out'] and line['move_out']['picking_id']:
                res['lines'][-1]['move_out'].update({
                    'picking_id' : line['move_out']['picking_id'].read(fields=['id', 'priority'])[0],
                    })

        return res
