# Copyright 2020 VentorTech OU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import models, fields

import logging

_logger = logging.getLogger(__file__)


class StockPickingMixin(models.AbstractModel):
    _name = 'stock.picking.mixin'
    _description = 'Stock Picking Mixin'

    company_id = fields.Many2one(
        comodel_name='res.company',
    )
    routing_module_version = fields.Char(
        related='company_id.routing_module_version',
    )

    @staticmethod
    def _recheck_record_list(record_list):
        rechecked_list = []
        for rec in record_list:
            if rec.get('_type') == 'stock.package_level' and rec.get('is_done'):
                continue
            rechecked_list.append(rec)
        return rechecked_list

    def _read_record(self, record_tuple):
        """
        record_tuple = (
            ('id', 100),
            ('_type', 'stock.move.line'),
        )

        id:: number (int)
        _type:: 'stock.move.line' or 'stock.package_level' (str)
        """
        record_dict = dict(record_tuple)
        record = self.env[record_dict['_type']].browse(record_dict['id'])
        record_dict.update(record.read()[0])
        return record_dict

    def serialize_record_ventor(self, rec_id):
        """Record serialization for the Ventor app."""
        filtered_list = []
        try:
            stock_object = self.search([
                ('id', '=', int(rec_id)),
            ])
        except Exception as ex:
            _logger.error(ex)
            return filtered_list

        full_list = [rec._get_operation_tuple() for rec in stock_object.operations_to_pick]
        [filtered_list.append(rec) for rec in full_list if rec not in filtered_list]
        record_list = [self._read_record(rec) for rec in filtered_list]
        return self._recheck_record_list(record_list)
