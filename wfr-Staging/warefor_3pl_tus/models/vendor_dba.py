# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class VendorDBA(models.Model):
    _name = "vendor.dba"
    _description = "Vendor DBA"
    _rec_name = "name"

    name = fields.Char(string="Name", required="1")
