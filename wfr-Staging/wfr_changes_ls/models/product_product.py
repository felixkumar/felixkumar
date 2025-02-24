from odoo import fields, models, api
from odoo.osv import expression
from odoo.tools import float_round


class ProductProductInherit(models.Model):
    _inherit = 'product.product'

    unavailable_qty = fields.Float('Unavailable Quantity ', compute='_compute_quantities',
                                   digits='Product Unit of Measure', compute_sudo=False,
                                   help="Unavailable quantity (computed as Quantity in Unavailable locations)\n"
                                        "In a context with a single Stock Location, this includes "
                                        "goods stored in the OS&D locations, or any of its children.\n"
                                        "In a context with a single Warehouse, this includes "
                                        "goods stored in the Unavailable Stock Locations of this Warehouse, or any "
                                        "of its children.\n"
                                        "Otherwise, this includes goods stored in any unavailable Stock Location "
                                        "with 'internal' type.")

    # def _get_domain_locations_new(self, location_ids):
    #     """
    #     Makes changes to the locations seen by users from other companies.
    #     All users see products and quantities that are part of 3PL Warehouses
    #     """
    #     # company = self.env['res.company'].sudo().browse(2)
    #     # locations = set(self.env['stock.warehouse'].with_company(company).search(
    #     #             [('is_3pl_warehouse', '!=', False)]
    #     #         ).mapped('view_location_id').ids)
    #     domain_quant_loc, domain_move_in_loc, domain_move_out_loc = super(
    #         ProductProductInherit, self)._get_domain_locations_new(location_ids)
    #     domain_quant_loc = expression.AND([domain_quant_loc, [('location_id.name', 'not like', 'OS&')]])
    #     return (
    #         domain_quant_loc,
    #         domain_move_in_loc,
    #         domain_move_out_loc
    #     )

    # @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state')
    # @api.depends_context(
    #     'lot_id', 'owner_id', 'package_id', 'from_date', 'to_date',
    #     'location', 'warehouse', 'allowed_company_ids'
    # )
    # def _compute_quantities(self):
    #     company = self.env['res.company'].sudo().browse(2)
    #     super(ProductProductInherit, self.with_company(company))._compute_quantities()
    #
    # @api.depends('stock_valuation_layer_ids')
    # @api.depends_context('to_date', 'company')
    # def _compute_value_svl(self):
    #     company = self.env['res.company'].sudo().browse(2)
    #     super(ProductProductInherit, self.with_company(company))._compute_value_svl()

    def _compute_quantities_dict(self, lot_id, owner_id, package_id, from_date=False, to_date=False):
        res = super(ProductProductInherit, self)._compute_quantities_dict(lot_id, owner_id, package_id, from_date,
                                                                          to_date)
        # Find the quantity in unavailable locations to set Unavailable Quantity
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations()
        domain_quant_loc += [('location_id.is_omit_on_source_location', '=', True)]
        domain_quant = [('product_id', 'in', self.ids)] + domain_quant_loc


        dates_in_the_past = False

        to_date = fields.Datetime.to_datetime(to_date)
        if to_date and to_date < fields.Datetime.now():
            dates_in_the_past = True
        if lot_id is not None:
            domain_quant += [('lot_id', '=', lot_id)]
        if owner_id is not None:
            domain_quant += [('owner_id', '=', owner_id)]
        if package_id is not None:
            domain_quant += [('package_id', '=', package_id)]
        if not dates_in_the_past:
            Quant = self.env['stock.quant'].with_context(active_test=False)
            quants_res = dict((item['product_id'][0], (item['quantity'], item['reserved_quantity'])) for item in Quant._read_group(domain_quant, ['product_id', 'quantity', 'reserved_quantity'], ['product_id'], orderby='id'))
            # rec = dict()
            for product in self.with_context(prefetch_fields=False):
                origin_product_id = product._origin.id
                product_id = product.id
                if not origin_product_id:
                    continue
                rounding = product.uom_id.rounding
                qty_unavailable = quants_res.get(origin_product_id, [0.0])[0]
                # This could include Pick, Pack and Ship locations, where products will already be reserved.
                qty_unavailable_reserved = quants_res.get(origin_product_id, [0.0, 0.0])[1]
                if qty_unavailable_reserved:
                    qty_unavailable -= qty_unavailable_reserved
                if qty_unavailable:
                    res[product_id]['free_qty'] = float_round(res[product_id]['free_qty'] - qty_unavailable, precision_rounding=rounding)
                    # res[product_id]['qty_available'] = float_round(res[product_id]['qty_available'] - qty_unavailable, precision_rounding=rounding)
                    res[product_id]['virtual_available'] = float_round(res[product_id]['virtual_available'] - qty_unavailable, precision_rounding=rounding)
                    res[product_id]['unavailable_qty'] = float_round(qty_unavailable, precision_rounding=rounding)
                else:
                    res[product_id]['unavailable_qty'] = float_round(0, precision_rounding=rounding)
        return res
