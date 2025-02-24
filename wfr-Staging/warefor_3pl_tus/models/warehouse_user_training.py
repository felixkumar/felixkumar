# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class WarehouseUserTraining(models.Model):
    _name = "warehouse.user.training"

    name = fields.Char("Name")
    type = fields.Selection(
        [("OBL", "OBL"), ("IBL", "IBL"), ("INVENTORY", "INVENTORY"), ("WAREHOUSE-OPS", "WAREHOUSE-OPS")], "Type")
    training_filename = fields.Char("Training Filename")
    training_file = fields.Binary("File")
    training_file_type = fields.Selection([('pdf', 'PDF'), ('other', 'Other')], string="File Type", default="pdf")
