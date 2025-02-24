import logging

from odoo import api, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'edi.import.tools.mixin']

    @api.model
    def get_gross_selling_price(self, partner, product, package=None, inv_address=None):
        """
        ToDo: Modified method for getting the product price from the edi pricelist directly
        """
        pricelist = self.env.ref('edi_sale_common.edi_pricelist')
        price = pricelist._get_product_price(product, 1.0)
        # partner_products = pricelist.item_ids.filtered_domain([('edi_partner_id', '=', partner.id), ('product_id', '=', product.id)])
        # pricelist_items = partner_products.filtered_domain([('edi_package_id', '=', package.id if package else False)])
        #
        # if len(pricelist_items) > 1:
        #     pricelist_items = pricelist_items.filtered_domain([('edi_inv_partner_id', 'in', [partner.id, False] if not inv_address or inv_address == partner else inv_address._ids)])

        if not price:
            _logger.info('Price Not found for product %s and Barcode %s' % (product.name, product.barcode))
            return 0

        return price

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        if self._context.get('is_edi'):
            edi_user = self.env['res.users'].browse(1)
            for order in res:
                valid_order_line_ids = order.order_line.filtered_domain([('display_type','not in',['line_note', 'line_section'])])
                order.edi_total_line_item_number = len(valid_order_line_ids)
                order.user_id = edi_user
        return res

    @api.model
    def process_po_number(self, node, additional_fields, nsmap=None):
        po_number = self.default_text(node)
        backorder_origin = self.env['sale.order'].sudo().search([('edi_po_number', '=', po_number), ('edi_backorder_origin_id', '=', None)], limit=1)
        return {
            'edi_po_number': po_number,
            'edi_backorder_origin_id': backorder_origin.id
        }

    @api.model
    def parse_dates_tag(self, node, additional_fields, nsmap=None):
        specific_date = None
        if node is not None:
            date_date = self.default_text(node.find('Date', namespaces=nsmap))
            date_time = self.default_text(node.find('Time', namespaces=nsmap))
            if date_time:
                specific_date = self.convert_TZ_UTC('%s %s' % (date_date, date_time), is_datetime=True)
            elif date_date:
                specific_date = self.convert_TZ_UTC(date_date)
        return specific_date


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model_create_multi
    def create(self, vals_list):
        revised_vals = []
        if self._context.get('is_edi'):
            for vals in vals_list:
                revised_vals.extend(self._get_edi_modified_lines(vals))
        else:
            revised_vals = vals_list
        return super().create(revised_vals)

    @api.model
    def _get_edi_modified_lines(self, vals):
        res = []
        product = self.env['product.product'].browse(vals.get('product_id'))
        uom = self.env['uom.uom'].browse(vals.get('product_uom'))
        uom_code = vals.get('edi_uom')
        # quantity = vals.get('product_uom_quantity', 0) # change quantity fields to product_uom_qty
        quantity = vals.get('product_uom_qty', 0)
        order = self.env['sale.order'].browse(vals.get('order_id'))
        partner = order.partner_id
        edi_price = vals.get('edi_price')
        package = None
        use_cases = False
        if uom and product and uom.edi_code == 'CA' and product.packaging_ids:
            package = product.packaging_ids.sorted(key=lambda r: r.create_date, reverse=True)[0]
            if package.qty:
                quantity *= package.qty
                use_cases = True

        # price = self.env['sale.order'].get_gross_selling_price(partner, product, package)
        # ToDo UPDATED EDI PRICE DIRECTLY IN UNIT PRICE
        price = edi_price
        # if price != edi_price:
        #     res.append({
        #         'order_id': order.id,
        #         'name': 'WARNING: Price mismatch between Odoo and EDI - Product: %s, Package: %s, EDI Price: %s, Selling Price: %s' % (
        #             product.name, package.name if package else 'None', edi_price, price),
        #         'display_type': 'line_note'
        #     })

        if uom.edi_code != uom_code and uom_code not in ['EA', 'CA']:
            res.append({
                'order_id': order.id,
                'name': 'UoM of %s not found. Units automatically assigned.' % uom_code,
                'display_type': 'line_note'
            })

        if use_cases:
            if partner.edi_price_in_cases:
                case_price = price
                price_unit = price / package.qty
            else:
                case_price = price * package.qty
                price_unit = price
        else:
            case_price = price_unit = price

        item_status_code = 'IA'
        if case_price != edi_price:
            item_status_code = 'IP'
        if order.edi_backorder_origin_id:
            item_status_code = 'IB'

        vals.update(product_uom_qty=quantity or 1, edi_case_price=case_price, price_unit=price_unit, edi_item_status_code=item_status_code)
        res.append(vals)
        return res

    @api.model
    def get_product_from_xml(self, node, additional_fields, nsmap=None):
        _logger.info('begin product method')
        Product = self.env['product.product']
        barcode = self.default_text(node)
        product = Product.search([('barcode', '=', barcode)], limit=1)

        if not product:  # For variants, strip the leading and trailing characters
            product = Product.search([('barcode', '=', barcode[1:])], limit=1)

        if not product:  # For Case UPC, strip the leading and trailing characters
            product = Product.search([('barcode', '=', barcode[1:-1])], limit=1)

        if product:
            product.sudo().write({
                'edi_gtin': self.default_text(additional_fields.get('GTIN')),
                'edi_ean': self.default_text(additional_fields.get('EAN'))
            })

        if not product:
            return {
                'edi_consumer_package_code': barcode
            }
            _logger.info('Product Not found FROM the EDI:\n Barcode: %s' % (barcode))
            product = self.env.ref('edi_sale_common.edi_product_product_error')

        _logger.info(product)

        return {
            'product_id': product.id,
            'edi_consumer_package_code': barcode
        }

    @api.model
    def get_product_from_xml_sku(self, node, additional_fields, nsmap=None):
        _logger.info('begin product method')
        Product = self.env['product.product']
        sku = self.default_text(node)
        product = Product.search([('default_code', '=', sku)], limit=1)

        if not product:  # For variants, strip the leading and trailing characters
            product = Product.search([('default_code', '=', sku[1:])], limit=1)

        if not product:  # For Case UPC, strip the leading and trailing characters
            product = Product.search([('default_code', '=', sku[1:-1])], limit=1)

        if product:
            product.sudo().write({
                'edi_gtin': self.default_text(additional_fields.get('GTIN')),
                'edi_ean': self.default_text(additional_fields.get('EAN'))
            })

        if not product:
            return {}
            _logger.info('Product Not found FROM the EDI:\n Barcode: %s' % (sku))
            product = self.env.ref('edi_sale_common.edi_product_product_error')

        _logger.info(product)

        return {
            'product_id': product.id,
            'edi_consumer_package_code': self.default_text(additional_fields.get('ConsumerPackageCode'))
        }

    @api.model
    def get_uom_from_xml(self, node, additional_fields, nsmap=None):
        try:
            uom_code = node.text
        except Exception as e:
            _logger.error("************-------------{} :".format(e))
            uom_code = ""

        uom = self.env['uom.uom'].search([('edi_code', '=', uom_code)])

        if not uom:
            uom = self.env['uom.uom'].search([('name', '=', 'Unit')], limit=1)
            if not uom:
                raise ValidationError(_('Could not assign UoM. No unit named Units.'))

        return {
            'product_uom': uom.id,
            'edi_uom': uom_code
        }

    def _is_order_in_cases(self):
        """Returns True if the sale order line was ordered in cases instead of units."""
        self.ensure_one()
        return self.product_packaging_id and self.product_packaging_id.qty and self.product_uom.edi_code == 'CA'

    def compute_price_unit_and_case_price(self, pricelist_price):
        # If the order is in cases we need to adjust the prices
        if self._is_order_in_cases():
            if self.order_id.partner_id.edi_price_in_cases:
                case_price = pricelist_price
                price_unit = pricelist_price / self.product_packaging_id.qty
            else:
                case_price = pricelist_price * self.product_packaging_id.qty
                price_unit = pricelist_price
        else:
            case_price = price_unit = pricelist_price

        return price_unit, case_price

    @api.model
    def get_payment_terms(self, payment_terms_node, additional_fields, nsmap=None):
        if not payment_terms_node:
            return ''
        terms_type = self.default_text(payment_terms_node.find('TermsType', namespaces=nsmap))
        basis_date_code = self.default_text(payment_terms_node.find('TermsBasisDateCode', namespaces=nsmap))
        discount_percentage = self.default_text(payment_terms_node.find('TermsDiscountPercentage', namespaces=nsmap))
        discount_date = self.default_text(payment_terms_node.find('TermsDiscountDate', namespaces=nsmap))
        discount_due_days = self.default_text(payment_terms_node.find('TermsDiscountDueDays', namespaces=nsmap))
        net_due_date = self.default_text(payment_terms_node.find('TermsNetDueDate', namespaces=nsmap))
        net_due_days = self.default_text(payment_terms_node.find('TermsNetDueDays', namespaces=nsmap))
        terms_description = self.default_text(payment_terms_node.find('TermsDescription', namespaces=nsmap))

        customer_payment_terms = 'Terms Type: %s\nBasis Date Code: %s\nDiscount Percentage: %s\nDiscount Date: %s\nDiscount Due Days: %s\nNet Due Date: %s\nNet Due Days: %s\nTerms Description: %s\n' \
            % (terms_type, basis_date_code, discount_percentage, discount_date, discount_due_days, net_due_date,
               net_due_days, terms_description)

        return customer_payment_terms
