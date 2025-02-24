# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    label_line_ids = fields.One2many('product.label.line', 'product_tmpl_id', 'Product Labels',
                                     help="Set the number of product labels")
    document_ids = fields.Many2many('ir.attachment',
                                    domain="[('mimetype', 'not in', ('application/javascript','text/css'))]")

    tab_line_ids = fields.One2many('product.tab.line', 'product_id', 'Product Tabs',
                                   compute="_get_product_tabs",
                                   inverse="_set_product_tabs", help="Set the product tabs")

    product_brand_id = fields.Many2one('product.brand', string='Brand',
                                       help='Select a brand for this product')
    free_qty = fields.Float(
        'Free To Use Quantity', compute='_compute_quantities', search='_search_free_qty',
        compute_sudo=True, digits='Product Unit of Measure')

    @api.depends(
        'product_variant_ids.free_qty',
        'product_variant_ids.virtual_available',
        'product_variant_ids.incoming_qty',
        'product_variant_ids.outgoing_qty',
        'product_variant_ids.free_qty',
    )
    def _compute_quantities(self):
        super(ProductTemplate, self)._compute_quantities()
        res = self._compute_quantities_dict()
        for template in self:
            template.free_qty = res[template.id]['free_qty']

    def _compute_quantities_dict(self):
        prod_available = super(ProductTemplate, self)._compute_quantities_dict()
        variants_available = {p['id']: p for p in
                              self.product_variant_ids._origin.read(['free_qty'])}
        for template in self:
            free_qty = 0
            for p in template.product_variant_ids._origin:
                free_qty += variants_available[p.id]["free_qty"]
            prod_available[template.id].update({"free_qty": free_qty, })
        return prod_available

    def _search_free_qty(self, operator, value):
        domain = [('free_qty', operator, value)]
        product_variant_query = self.env['product.product'].sudo()._search(domain)
        return [('product_variant_ids', 'in', product_variant_query)]

    def _get_product_tabs(self):
        """
        displays the global tab and product specific tab in the product template
        @return: product tabs
        """
        for product in self:
            all_global_product_tabs = self.env['product.tab.line'].search(
                [('tab_type', '=', 'global')])
            product_tabs = self.env['product.tab.line'].search([('product_id', '=', self.id)])
            all_products_tabs = all_global_product_tabs + product_tabs
            product_tabs = all_products_tabs.ids
            for product_tab in all_products_tabs:
                if product_tab.is_modified == True and product_tab.product_id.id == self.id and product_tab.parent_id:
                    if product_tab.parent_id.id in product_tabs:
                        product_tabs.remove(product_tab.parent_id.id)

            product.tab_line_ids = [(6, 0, product_tabs)]

    def _set_product_tabs(self):
        return True

    def _website_show_quick_add(self):
        website = self.env['website'].get_current_website()
        res = False
        check_hide_add_to_cart = True if website.b2b_hide_add_to_cart and website.is_public_user() else False
        if not check_hide_add_to_cart:
            res = super(ProductTemplate, self)._website_show_quick_add()
        return res

    @api.model
    def _search_get_detail(self, website, order, options):
        res = super(ProductTemplate, self)._search_get_detail(website=website, order=order,
                                                              options=options)
        attrib_values = options.get('attrib_values')
        res['search_fields'].append('product_variant_ids.barcode')
        curr_website = self.env['website'].sudo().get_current_website()
        if curr_website.enable_smart_search:
            if curr_website.search_in_brands:
                res['search_fields'].append('product_brand_id.name')
            if curr_website.search_in_attributes_and_values:
                # pass
                res['search_fields'].append('attribute_line_ids.value_ids.name')
        if attrib_values:
            ids = []
            # brand Filter
            for value in attrib_values:
                if value[0] == 0:
                    ids.append(value[1])
                    res.get('base_domain', False) and res['base_domain'].append(
                        [('product_brand_id.id', 'in', ids)])
        if not curr_website.display_out_of_stock or options.get('out_of_stock', False) == '1':
            res.get('base_domain', False) and res['base_domain'].append(
                ['|', ('allow_out_of_stock_order', '=', True), '&', ('free_qty', '>', 0),
                 ('allow_out_of_stock_order', '=', False)])
        return res

    @api.constrains('tab_line_ids')
    def check_tab_lines(self):
        """
        check for not more than 4 tabs
        @return:
        """
        if len(self.tab_line_ids.ids) > 4:
            raise UserError(_("You can not create more then 4 tabs!!"))

    def write(self, vals):
        """
        vals: Dictionary which will include the values that need to be updated
        Inherited write method so when product tab is added from product template then the record should be created and
        also when the global tab is edited then the new product specific product tab will be created.
        @return: Boolean
        """
        if vals.get('tab_line_ids', False):
            for value in vals.get('tab_line_ids', False):
                if type(value[1]) == int:
                    global_tab = self.env['product.tab.line'].search([('id', '=', value[1])])
                    if global_tab.tab_type == 'global' and value[0] == 1:
                        if global_tab.website_ids:
                            websites_ids = global_tab.website_ids.ids if len(
                                global_tab.website_ids.ids) > 1 else [
                                global_tab.website_ids.id]
                        else:
                            websites_ids = []
                        vals_tab = {'tab_name': global_tab.tab_name,
                                    'is_modified': True,
                                    'parent_id': global_tab.id,
                                    'product_id': self.id,
                                    'tab_type': 'specific product',
                                    'tab_content': value[2].get('tab_content',
                                                                False) or global_tab.tab_content,
                                    'sequence': global_tab.sequence,
                                    'website_ids': [[6, 0, websites_ids]],}
                        self.env['product.tab.line'].create(vals_tab)
                    elif type(value[1]) == int and value[0] == 2:
                        tab_to_delete = self.env['product.tab.line'].search([('id', '=', value[1])])
                        if not tab_to_delete.tab_type == 'global':
                            tab_to_delete.unlink()
                elif type(value[1]) == str and value[0] == 0:
                    vals_tab = value[2]
                    vals_tab.update({'product_id': self.id})
                    self.env['product.tab.line'].create(vals_tab)
        res = super(ProductTemplate, self).write(vals)
        return res

    def remove_cart_button(self):
        if self.detailed_type == 'product' and not self.allow_out_of_stock_order and self.sudo().free_qty < 1:
            return True
        return False


    def _is_add_to_cart_possible(self, parent_combination=None):
        website = self.env['website'].get_current_website()
        if not website.display_out_of_stock and not self.allow_out_of_stock_order and \
                self.sudo().free_qty <= 0:
            return False
        return super(ProductTemplate, self)._is_add_to_cart_possible(parent_combination=parent_combination)

    def _get_website_accessory_product(self):
        res = super(ProductTemplate, self)._get_website_accessory_product()
        website = self.env['website'].get_current_website()
        if not website.display_out_of_stock:
            res = res.filtered(lambda l : l.free_qty > 0 or l.allow_out_of_stock_order is True)
        return res

    def _get_sales_prices(self, pricelist):
        """Overrided base method"""
        pricelist.ensure_one()
        partner_sudo = self.env.user.partner_id

        # Try to fetch geoip based fpos or fallback on partner one
        fpos_id = self.env['website']._get_current_fiscal_position_id(partner_sudo)
        fiscal_position = self.env['account.fiscal.position'].sudo().browse(fpos_id)

        sales_prices = pricelist._get_products_price(self, 1.0)
        show_discount = pricelist.discount_policy == 'without_discount'

        base_sales_prices = self.price_compute('list_price', currency=pricelist.currency_id)

        res = {}
        for template in self:
            price_reduce = sales_prices[template.id]

            product_taxes = template.sudo().taxes_id.filtered(lambda t: t.company_id == t.env.company)
            taxes = fiscal_position.map_tax(product_taxes)

            price_reduce = self.env['account.tax']._fix_tax_included_price_company(price_reduce, product_taxes, taxes, self.env.company)

            global_setting = self.env['ir.config_parameter'].sudo().get_param('account.show_line_subtotals_tax_selection')

            if pricelist and pricelist.display_product_price != "system_setting" and global_setting != pricelist.display_product_price:
                is_exclude = pricelist.display_product_price == "tax_excluded"
                tax_display = is_exclude and 'total_excluded' or 'total_included'
            else:
                tax_display = self.user_has_groups('account.group_show_line_subtotals_tax_excluded') and 'total_excluded' or 'total_included'

            price_reduce = taxes.compute_all(price_reduce, pricelist.currency_id, 1, template, partner_sudo)[tax_display]

            template_price_vals = {'price_reduce': price_reduce}
            base_price = None
            price_list_contains_template = price_reduce != base_sales_prices[template.id]

            if template.compare_list_price:
                # The base_price becomes the compare list price and the price_reduce becomes the price
                base_price = template.compare_list_price
                if not price_list_contains_template:
                    price_reduce = base_sales_prices[template.id]
                    template_price_vals.update(price_reduce=price_reduce)
            elif show_discount and price_list_contains_template:
                base_price = base_sales_prices[template.id]

            if base_price and base_price != price_reduce:
                base_price = self.env['account.tax']._fix_tax_included_price_company(
                    base_price, product_taxes, taxes, self.env.company)
                base_price = taxes.compute_all(base_price, pricelist.currency_id, 1, template, partner_sudo)[
                    tax_display]
                template_price_vals['base_price'] = base_price

            res[template.id] = template_price_vals
        return res

    def _price_with_tax_computed(self, price, product_taxes, taxes, company_id, pricelist, product, partner):
        res = super(ProductTemplate, self)._price_with_tax_computed(price=price,
                                                                    product_taxes=product_taxes,
                                                                    taxes=taxes,
                                                                    company_id=company_id,
                                                                    pricelist=pricelist,
                                                                    product=product,
                                                                    partner=partner)

        global_setting = self.env['ir.config_parameter'].sudo().get_param('account.show_line_subtotals_tax_selection')
        if pricelist and pricelist.display_product_price != "system_setting" and global_setting != pricelist.display_product_price:
            is_exclude = pricelist.display_product_price == "tax_excluded"
            tax_display = 'total_excluded' if is_exclude else 'total_included'
            res = taxes.compute_all(price, pricelist.currency_id, 1, product, partner)[tax_display]
        return res

    def _get_contextual_price_tax_selection(self):
        self.ensure_one()
        price = self._get_contextual_price()
        line_tax_type = self.env['ir.config_parameter'].sudo().get_param('account.show_line_subtotals_tax_selection')
        if line_tax_type == "tax_included" and self.taxes_id:
            price = self.taxes_id.compute_all(price, product=self, partner=self.env['res.partner'])['total_included']
        return price

    def _is_add_to_cart_allowed(self):
        self.ensure_one()
        return self.user_has_groups('base.group_system') or (self.active and self.sale_ok and self.website_published)
