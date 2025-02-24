# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""
    Extends the functionality of Product Template
"""
from odoo import models


class ProductTemplate(models.Model):
    """
        Product Template Inherits
    """
    _inherit = ["multi.company.abstract", "product.template"]
    _name = "product.template"
    _description = "Product Template (Multi-Company)"
