# -*- coding: utf-8 -*-
"""
    Creating truck driver signature
"""
from odoo import models, fields


class TruckDriverSignature(models.Model):
    """
        Manage truck driver signature based on the name
    """
    _name = "truck.driver.name"
    _description = "Driver Signature"

    name = fields.Char("Name")
    driver_name = fields.Char(" Driver Name")
    signature = fields.Binary("Signature")
