# -*- coding: utf-8 -*-
import io
from io import BytesIO
import base64
import pytz
import calendar
from datetime import datetime
from PIL import Image

from odoo.tools.misc import xlsxwriter

from odoo import api, models, fields
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class FreightOSDReport(models.Model):
    """ Freight OS&D Report Analysis """

    _name = 'freight.osd.report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Freight OS&D Report"

    freight_id = fields.Many2one(comodel_name="freight.freight", string="PL Record", tracking=True)
    sku_id = fields.Many2one(comodel_name="product.product", string="SKU", tracking=True)
    description = fields.Char(related="sku_id.name", string="Description", tracking=True)
    # report_type = fields.Selection(string="Report Type", selection=[('overage', 'Overage'),
    #                                                                 ('shortage', 'Shortage'),
    #                                                                 ('damaged', 'Damaged'),
    #                                                                 ], required=False, default='overage')
    osd_total_qty = fields.Float(string="QTY", digits=(999,0), tracking=True)
    overage_qty = fields.Float(string="Overage",digits=(999,0), tracking=True)
    shortage_qty = fields.Float(string="Shortage",digits=(999,0), tracking=True)
    damaged_qty = fields.Float(string="Product Damaged",digits=(999,0), tracking=True)
    package_damaged_qty = fields.Float(string="Packaging Damaged",digits=(999,0), tracking=True)
