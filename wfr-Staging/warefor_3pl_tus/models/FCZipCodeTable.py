# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class FCZipCodeTable(models.Model):
    _name = "fc.zip.code.table"
    _rec_name = 'zip_code'

    zip_code = fields.Char("Zip Code")
    state = fields.Char("State")
    combined = fields.Char("Combined")

    texas = fields.Char("Texas", default="77423")
    california = fields.Char("California", default="92878")
    georgia = fields.Char("Georgia", default="30542")
    pennsylvania = fields.Char("Pennsylvania", default="18083")

    # TEXAS
    f_texas_transit_time = fields.Char("Transit Time")
    f_texas_zone = fields.Char("Zone")
    f_texas_cost = fields.Char("Cost")

    # California
    f_california_transit_time = fields.Char("Transit Time")
    f_california_zone = fields.Char("Zone")
    f_california_cost = fields.Char("Cost")

    # Georgia
    f_georgia_transit_time = fields.Char("Transit Time")
    f_georgia_zone = fields.Char("Zone")
    f_georgia_cost = fields.Char("Cost")

    # Pennsylvania
    f_pennsylvania_transit_time = fields.Char("Transit Time")
    f_pennsylvania_zone = fields.Char("Zone")
    f_pennsylvania_cost = fields.Char("Cost")

    # Pennsylvania
    f_min_transit_time = fields.Char("Min Transit Time")
    f_min_zone = fields.Char("Min Zone")
    f_min_cost = fields.Char("Min Cost")

    f_choice1 = fields.Char("Choice 1")
    f_choice2 = fields.Char("Choice 2")
    f_choice3 = fields.Char("Choice 3")
    f_choice4 = fields.Char("Choice 4")

    # TEXAS
    u_texas_transit_time = fields.Char("Transit Time")
    u_texas_zone = fields.Char("Zone")
    u_texas_cost = fields.Char("Cost")

    # California
    u_california_transit_time = fields.Char("Transit Time")
    u_california_zone = fields.Char("Zone")
    u_california_cost = fields.Char("Cost")

    # Georgia
    u_georgia_transit_time = fields.Char("Transit Time")
    u_georgia_zone = fields.Char("Zone")
    u_georgia_cost = fields.Char("Cost")

    # Pennsylvania
    u_pennsylvania_transit_time = fields.Char("Transit Time")
    u_pennsylvania_zone = fields.Char("Zone")
    u_pennsylvania_cost = fields.Char("Cost")

    # Pennsylvania
    u_min_transit_time = fields.Char("Min Transit Time")
    u_min_zone = fields.Char("Min Zone")
    u_min_cost = fields.Char("Min Cost")

    u_choice1 = fields.Char("Choice 1")
    u_choice2 = fields.Char("Choice 2")
    u_choice3 = fields.Char("Choice 3")
    u_choice4 = fields.Char("Choice 4")
