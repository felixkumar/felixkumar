# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class GenerateOldDaysReport(models.TransientModel):
	_name = "generate.old.days.report"
	_description = "Generate Old Days Report"

	date = fields.Date(string='Date')

	def generate_report(self):
		self.env['warehouse.stock.inventory'].with_context(from_wizard_date=self.date)._generate_warehouse_report()
		return True
