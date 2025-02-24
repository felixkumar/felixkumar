# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class OBLStatusTag(models.Model):
    _name = 'obl.status.tag'
    _description = 'OBL Stage Data In Tag'

    name = fields.Char("Name")


class FreightStagesData(models.Model):
    _name = 'freight.stages.data'
    _description = 'Manage Freight Stage Dynamically'

    name = fields.Char("Name")
    sequence = fields.Integer("Sequence")
    freight_stage_id = fields.Many2one("freight.outbound.stage", "Stage Name")
    status_ids = fields.Many2many("obl.status.tag", string="Status Tag")
