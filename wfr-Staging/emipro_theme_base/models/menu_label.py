# -*- coding: utf-8 -*-
"""
    This model is used to create a menu label
"""
from odoo import api, fields, models, _


class MenuLabel(models.Model):
    """
    Class to handle menu label records
    """
    _name = "menu.label"
    _description = "Menu Label"

    name = fields.Char("Name", required=True, translate=True, help="Name of the menu label")
    label_background_color = fields.Char(string='Background Color',
                                         help="Here you can set a specific HTML color index (e.g. #ff0000) to display the menu label background color", default="#ff0000")
    label_text_color = fields.Char(string='Color',
                                   help="Here you can set a specific HTML color index (e.g. #ff0000) to display the text "
                                        "color of menu label.", default="#00ff00")
    category_ids = fields.One2many('product.public.category', 'menu_label_id', 'Category Ids')

    def write(self, vals):
        self.clear_caches()
        res = super(MenuLabel, self).write(vals)
        category_ids = self.category_ids
        self.update_dynamic_mega_menu(category_ids)
        return res

    def unlink(self):
        category_ids = self.category_ids
        res = super(MenuLabel, self).unlink()
        self.update_dynamic_mega_menu(category_ids)
        return res

    def update_dynamic_mega_menu(self, category_ids):
        parent_catg = []
        for cate in category_ids:
            categorie = cate.parent_path and cate.parent_path.split('/')
            sub_list = categorie and [int(c) for c in categorie if c and c != cate.id]
            parent_catg += sub_list
        menu = self.env['website.menu'].search(['|', ('ecom_category', 'in', parent_catg),
                                                ('category_selection', '=', 'all')])
        for m in menu:
            m._set_field_is_mega_menu_overrided()