# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class Product3PLBoxTus(models.Model):
    _name = "product.3pl.box.tus"
    _description = "Product 3PL Box"
    _order = 'sequence'
    _check_company_auto = True

    @api.depends('height', 'width', 'packaging_length')
    def _compute_package_name(self):
        for record in self:
            if all([record.height, record.width, record.packaging_length]):
                record.name = "{}X{}X{}".format(record.height, record.width, record.packaging_length)

    name = fields.Char(compute='_compute_package_name', string=_("Name"), store=True)
    sequence = fields.Integer(_('Sequence'), default=1, help=_("The first in the sequence is the default one."))
    qty = fields.Float(_('Contained Quantity'), help=_("Quantity of products contained in the packaging."))
    active = fields.Boolean(_('Active'), default=True)
    barcode = fields.Char(_('Barcode'), copy=False,
                          help=_("Barcode used for packaging identification. Scan this packaging barcode from a transfer in the Barcode app to move all the contained units"))

    height = fields.Integer(_('Height'))
    width = fields.Integer(_('Width'))
    packaging_length = fields.Integer(_('Length'))
    max_weight = fields.Float(_('Max Weight'), help=_('Maximum weight shippable in this packaging'))

    warehouse_ids = fields.Many2many('stock.warehouse', string=_('Warehouses'),
                                     help=_("Show the routes that apply on selected warehouses."))

    _sql_constraints = [
        ('positive_height', 'CHECK(height>=0)', _('Height must be positive')),
        ('positive_width', 'CHECK(width>=0)', _('Width must be positive')),
        ('positive_length', 'CHECK(packaging_length>=0)', _('Length must be positive')),
        ('positive_max_weight', 'CHECK(max_weight>=0.0)', _('Max Weight must be positive')),
    ]
