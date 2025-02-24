# -*- coding: utf-8 -*-

from odoo import models, fields


class OSDReportWizard(models.TransientModel):
    _name = 'osd.report.wizard'
    _description = 'OS&D Report Wizard'

    product_ids = fields.Many2many('product.product', string='Products')

    def generate_osd_report(self):
        """
            Generate the OS&D report based on the selected product
        :return:
        """
        freight_ids = self.env['freight.freight'].search([('is_outbound', '!=', True)])
        product_ids = self.product_ids
        if not product_ids:
            product_ids = product_ids.search([])
        action = freight_ids.osd_report(product_ids.ids)
        return action
