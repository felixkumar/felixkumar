from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    is_category_page = fields.Boolean(string='Allow Category Page',
                                      help="It will set the separate page for this category")
    category_page = fields.Many2one("website.page", string="Select Page",
                                    help="Select the page which you want to set for this category.")
    icon = fields.Binary('Category Icon')
    menu_label_id = fields.Many2one('menu.label', string='Menu Label', help='Select a menu label for this category')

    @api.model
    def create(self, vals):
        if vals.get('parent_id'):
            parent_id = vals.get('parent_id')
            if parent_id:
                parent_length = len(self.env['product.public.category'].browse(parent_id).parent_path.split('/'))
                if parent_length > 3:
                    raise UserError(_('You can add upto 2 nested categories!'))
        res = super(ProductPublicCategory, self).create(vals)
        self.update_dynamic_mega_menu(res)
        return res

    def write(self, vals):
        self.clear_caches()
        parent_catg = self.parent_path and self.parent_path.split('/')
        if vals.get('parent_id', False):
            parent_id = vals.get('parent_id')
            if parent_id:
                parent_catg += self.env['product.public.category'].browse(parent_id).parent_path.split('/')
        parent_catg = parent_catg and [int(m) for m in parent_catg if m and m != self.id]
        menu = self.env['website.menu'].search(['|', ('ecom_category', 'in', parent_catg),
                                                ('category_selection', '=', 'all')])
        res = super(ProductPublicCategory, self).write(vals)
        for m in menu:
            m._set_field_is_mega_menu_overrided()
        return res

    def unlink(self):
        parent_catg = []
        for cate in self:
            categorie = cate.parent_path and cate.parent_path.split('/')
            sub_list = categorie and [int(c) for c in categorie if c and c != cate.id]
            parent_catg += sub_list
        res = super(ProductPublicCategory, self).unlink()
        menu = self.env['website.menu'].search(['|', ('ecom_category', 'in', parent_catg),
                                                ('category_selection', '=', 'all')])
        for m in menu:
            m._set_field_is_mega_menu_overrided()
        return res

    def update_dynamic_mega_menu(self, obj):
        parent_catg = obj.parent_path and obj.parent_path.split('/')
        parent_catg = parent_catg and [int(m) for m in parent_catg if m and m != obj.id]
        menu = self.env['website.menu'].search(['|', ('ecom_category', 'in', parent_catg),
                                                ('category_selection', '=', 'all')])
        for m in menu:
            m._set_field_is_mega_menu_overrided()
