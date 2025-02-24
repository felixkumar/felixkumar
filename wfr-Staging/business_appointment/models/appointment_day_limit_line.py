#coding: utf-8

from odoo import fields, models


class appointment_day_limit_line(models.Model):
    """
    The model to keep limits for daily appointments for specific days
    """
    _name = "appointment.day.limit.line"
    _description = "Appointment Restriction Day"
    _rec_name = "limit_day"

    limit_day = fields.Date("Date", required=True)
    day_limit_id = fields.Many2one(
    	"appointment.day.limit",
    	string="Day Limit",
    	required=True,
    	ondelete="cascade",
    )

    _order = "limit_day desc, id"
