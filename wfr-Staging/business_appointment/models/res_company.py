# -*- coding: utf-8 -*-

from odoo import api, fields, models


class res_company(models.Model):
    """
    Overwrite to add company settings
    """
    _inherit = "res.company"

    @api.model
    def _default_ba_pricelist_id(self):
        """
        Default method for ba_pricelist_id
        """
        main_pricelist = self.sudo().env.ref("product.list0", False)
        if not main_pricelist:
            main_pricelist = self.env["product.pricelist"].search([], limit=1)
        return main_pricelist

    ba_pricelist_id = fields.Many2one(
        "product.pricelist",
        string="Price List for Appointments",
        default=_default_ba_pricelist_id,
    )
    ba_timezone_option = fields.Boolean(string="Different Time Zones")  
