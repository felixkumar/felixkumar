"""This model is used to create a website wise dynamic category listing"""
from odoo import api, fields, models
from odoo.http import request


class WebsiteMenu(models.Model):

    _inherit = 'website.menu'

    is_dynamic_menu = fields.Boolean(string="Is All Category Dynamic Menu", default=False)
    dynamic_mega_menu = fields.Boolean(string="Dynamic Mega Menu", inverse='_set_field_is_mega_menu_overrided')
    category_selection = fields.Selection([('all', 'All Categories'),
                                           ('specific', 'Specific Category')], 'Category Selection',
                                          default='specific',
                                          inverse='_set_field_is_mega_menu_overrided')
    ecom_category = fields.Many2one('product.public.category',
                                    string='Select Category',
                                    inverse='_set_field_is_mega_menu_overrided')
    category_menu_styles = fields.Selection([('style1', 'Style 1'),
                                             ('style2', 'Style 2'),
                                             ('style3', 'Style 3'),
                                             ('style4', 'Style 4'),
                                             ('style5', 'Style 5'),
                                             ('style6', 'Nested menu')], 'Mega Menu Style',
                                            inverse='_set_field_is_mega_menu_overrided')
    menu_label_id = fields.Many2one('menu.label', string='Menu Label', help='Select a menu label for this category')
    is_highlight_menu = fields.Boolean(string="Highlight Menu")
    website_id = fields.Many2one('website', 'Website', ondelete='cascade',
                                      inverse = '_set_field_is_mega_menu_overrided')

    # is_mega_menu = fields.Boolean(compute='_compute_field_is_mega_menu_overrided')

    # Overide get_tree method to add is_dynamic_menu field
    @api.model
    def get_tree(self, website_id, menu_id=None):
        """
        Overide get_tree method to add custom is_dynamic_menu field
        :param website_id: current website id
        :param menu_id: menu id default none
        :return: make_tree function which is recursively called
        """
        def make_tree(node):
            is_homepage = bool(node.page_id and self.env['website'].browse(website_id).homepage_id.id == node.page_id.id)
            menu_node = {'fields': {'id': node.id,
                                    'name': node.name,
                                    'url': node.page_id.url if node.page_id else node.url,
                                    'new_window': node.new_window,
                                    'is_mega_menu': node.is_mega_menu,
                                    'sequence': node.sequence,
                                    'parent_id': node.parent_id.id,
                                    'dynamic_mega_menu': node.dynamic_mega_menu,
                                    'is_dynamic_menu': node.is_dynamic_menu,},
                         'children': [],
                         'is_homepage': is_homepage}
            for child in node.child_id:
                menu_node['children'].append(make_tree(child))
            return menu_node
        menu = menu_id and self.browse(menu_id) or self.env['website'].browse(website_id).menu_id
        return make_tree(menu)

    def _set_field_is_mega_menu_overrided(self):
        for menu in self:
            if menu.is_mega_menu and not menu.dynamic_mega_menu:
                if not menu.mega_menu_content:
                    menu.mega_menu_content = self.env['ir.ui.view']._render_template('website.s_mega_menu_odoo_menu')
            elif menu.is_mega_menu and menu.dynamic_mega_menu:
                website_id = self.website_id.id if self.website_id else request.env['website'].sudo().get_current_website().id
                context = {'category_menu_styles': menu.category_menu_styles, 'menu': menu, 'website_id': website_id}
                template = 'theme_clarico_vega.dynamic_category_mega_menu'
                menu.mega_menu_content = self.env['ir.ui.view']._render_template(template, values=context)
            else:
                menu.mega_menu_content = False
                menu.mega_menu_classes = False
