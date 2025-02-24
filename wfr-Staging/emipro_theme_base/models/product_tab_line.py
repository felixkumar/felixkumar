from odoo import api, fields, models
from odoo.tools.translate import html_translate


class ProductTabLine(models.Model):
    _name = "product.tab.line"
    _inherit = ['website.published.multi.mixin']
    _description = 'Product Tab Line'
    _order = "sequence, id"
    _rec_name = "tab_name"

    def _get_default_icon_content(self):
        return """
            <span class="fa fa-info-circle me-2"/>
            """

    product_id = fields.Many2one('product.template', string='Product Template')
    tab_name = fields.Char("Tab Name", required=True, translate=True)
    tab_content = fields.Html("Tab Content", sanitize_attributes=False, translate=html_translate, sanitize_form=False)
    icon_content = fields.Html("Icon Content", translate=html_translate, default=_get_default_icon_content)
    website_ids = fields.Many2many('website', help="You can set the description in particular website.")
    sequence = fields.Integer('Sequence', default=1, help="Gives the sequence order when displaying.")
    tab_type = fields.Selection([('specific product', 'Specific Product'), ('global', 'Global')], string='Tab Type')
    is_modified = fields.Boolean(string='Is Modified')
    parent_id = fields.Many2one(string='Parent Tab', comodel_name='product.tab.line')

    def check_tab(self, current_website, tab_website_array):
        """
        check tab for display
        @param current_website: current website
        @param tab_website_array: website array
        @return: Boolean
        """
        if current_website in tab_website_array or len(tab_website_array) == 0:
            return True
        return False

    def check_tab_publish(self, tab):
        user = self.env['res.users'].search([('id', '=', self._uid)])
        if tab.tab_type == 'global' and tab.website_published == True:
            return True
        elif tab.tab_type == 'global' and user.has_group('website.group_website_designer'):
            return True
        elif tab.tab_type == 'specific product':
            return True
        return False

    @api.onchange('tab_type')
    def onchange_tab_type(self):
        """
        onchange for tab type
        """
        if self.tab_type == 'global':
            self.product_id = None

    def write(self, vals):
        """
        vals: Dictionary which will include the values that need to be updated.
        If global tab is edited from product template than no changes should be made.
        @return: Boolean
        """
        self.clear_caches()
        context = dict(self._context or {})
        model_name = context.get('tree_view_ref', False)
        if model_name and model_name == 'website_sale.product_template_view_tree_website_sale' and self.tab_type == 'global':
            return True
        elif model_name and model_name == 'emipro_theme_base.product_tab_line':
            return super(ProductTabLine, self).write(vals)
        elif model_name and model_name == 'website_sale.product_template_view_tree_website_sale' and self.tab_type != 'global':
            return super(ProductTabLine, self).write(vals)
        elif context.get('website_id', False):
            return super(ProductTabLine, self).write(vals)
        elif len(vals) == 1 and (vals.get('sequence', False) or vals.get('tab_content', False)):
            return super(ProductTabLine, self).write(vals)
        return True
