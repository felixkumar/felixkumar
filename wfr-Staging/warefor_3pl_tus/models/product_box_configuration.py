# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

BLOCK_USER = [1580]


class ProductBoxConfiguration(models.Model):
    _name = "product.box.configuration"
    _description = 'Product Box Configuration'
    _rec_name = 'box_id'

    box_id = fields.Many2one(comodel_name="product.3pl.box.tus", string="Box")
    product_qty_string = fields.Char(_('Product Qty'), compute="_compute_product_qty_string")
    product_lines = fields.One2many(comodel_name="product.qty.lines", inverse_name="product_box_id",
                                    string="Product Lines")

    @api.depends('product_lines')
    def _compute_product_qty_string(self):
        for record in self:
            product_string = ""
            for product_line in record.product_lines:
                if not product_string:
                    product_string += "{}_{}".format(product_line.product_id.default_code,
                                                     round(product_line.product_qty))
                else:
                    product_string += "_{}_{}".format(product_line.product_id.default_code,
                                                      round(product_line.product_qty))
            record.product_qty_string = product_string


class ProductQtyLines(models.Model):
    _name = "product.qty.lines"
    _description = 'Product Qty Lines'

    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    product_qty = fields.Float(_('Quantity'))
    product_box_id = fields.Many2one(comodel_name="product.box.configuration", string="Product Configuration")


class ProductProduct(models.Model):
    _inherit = 'product.product'

    pallet_count = fields.Float(string="Pallet Count", compute="_get_pallet_count")
    volume = fields.Float('Volume', digits='Volume', compute="_compute_volume_by_volume", store=True)
    pallet_volume = fields.Float('Pallet Volume', digits='Volume', compute="_compute_pallet_volume_by_volume",
                                 store=True)

    @api.depends("product_height", "product_width", "product_length")
    def _compute_volume_by_volume(self):
        for rec in self:
            if all([rec.product_length, rec.product_width, rec.product_height]):
                rec.volume = (rec.product_length * rec.product_width * rec.product_height) / 1728
            else:
                rec.volume = rec.volume

    @api.depends('pallet_height', 'pallet_width', 'pallet_length')
    def _compute_pallet_volume_by_volume(self):
        for rec in self:
            if all([rec.pallet_height, rec.pallet_width, rec.pallet_length]):
                rec.pallet_volume = (rec.pallet_length * rec.pallet_width * rec.pallet_height) / 1728
            else:
                rec.pallet_volume = 0.0

    def _get_pallet_count(self):
        for rec in self:
            rec.pallet_count = rec.product_per_pallet and rec.qty_available / rec.product_per_pallet or 0
            # rec.pallet_count = len(self._get_related_pallets())

    @api.model
    def _get_related_pallets(self):
        return self.env['pallet.product.line'].search([('product_id', '=', self.id)]).mapped('pallet_id').ids

    def show_product_pallets(self):
        self.ensure_one()
        pallet_ids = self._get_related_pallets()
        if len(pallet_ids):
            return {
                'name': _("Pallets"),
                'type': 'ir.actions.act_window',
                'res_model': 'pallet.batch.tus',
                'view_mode': 'tree, form',
                'views': [(False, 'list'), (self.env.ref('warefor_3pl_tus.form_view_pallet_batch_tus').id, 'form')],
                'domain': [('id', 'in', list(pallet_ids))],
                'target': 'current',
            }

    def name_get(self):
        res = super(ProductProduct, self).name_get()
        if self._context.get('is_ops_model'):
            res = [(product.id, product.default_code) for product in self]
        return res

    @api.constrains('default_code')
    def _check_default_code(self):
        for rec in self:
            if self.search([('default_code', '=', rec.default_code)]).__len__() > 1:
                raise ValidationError(_("Record already exists with this MFG SKU {}".format(rec.default_code)))
        return True

    def _get_domain_locations_new(self, location_ids):
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = super(ProductProduct,
                                                                          self)._get_domain_locations_new(location_ids)
        virtual_location = self.env['stock.location'].search(
            [('company_id', 'in', self.env.companies.ids), ('is_virtual_location', '=', True)])
        if virtual_location:
            domain_quant_loc = expression.OR([domain_quant_loc, [('location_id', 'in', virtual_location.ids)]])
        return (
            domain_quant_loc,
            domain_move_in_loc,
            domain_move_out_loc
        )

    def _compute_quantities_dict_a(self, lot_id, owner_id, package_id, from_date=False, to_date=False):
        Warehouse = self.env['stock.warehouse']
        warehouse_ids = Warehouse.search([])
        res = super(ProductProduct, self.with_context(warehouse=warehouse_ids.ids))._compute_quantities_dict(lot_id, owner_id, package_id, from_date=from_date,
                                                                   to_date=to_date)
        Move = self.env['stock.move'].sudo().with_context(active_test=False)


        location_ids = self.env['stock.location'].search(
            [('usage', '=', 'supplier')])

        sl_location_ids = self.env['stock.location'].sudo().search([('usage', '=', 'internal'), ('is_omit_on_source_location', '=', True)])

        sl_dest_location_ids = self.env['stock.location'].search([('usage', '=', 'customer')])
        # return res
        for rec in self:
            dest_location_ids = self.env['stock.location'].sudo().search(
                [('usage', '=', 'transit'), ('company_id', 'in', rec.company_ids.ids),
                 ('is_virtual_location', '=', True)])
            if location_ids and dest_location_ids:
                move_ids = Move.search(
                    [('location_id', 'in', location_ids.ids), ('location_dest_id', 'in', dest_location_ids.ids),
                     ('product_id', '=', rec.id), ('state', '=', 'assigned'), ('picking_code', '=', 'incoming')])

                osd_transfer_ids = move_ids.picking_id.purchase_id.freight_record.osd_transfer_ids.filtered(
                    lambda o: o.is_osd_inventory_transfered and o.sku_id.id in move_ids.product_id.ids)

                incoming_qty = sum(move_ids.mapped('product_uom_qty'))

                if osd_transfer_ids and self.env.company.is_logistics:
                    incoming_qty = sum(move_ids.mapped('product_uom_qty')) - sum(osd_transfer_ids.mapped('quantity'))

                res[rec.id]['incoming_qty'] = res[rec.id]['incoming_qty'] + incoming_qty
                res[rec.id]['virtual_available'] = res[rec.id]['virtual_available'] + incoming_qty

            if sl_location_ids and sl_dest_location_ids and self.env.companies.filtered(lambda l: l.is_oxford):
                sl_move_ids = Move.search(
                    [('location_id', 'in', sl_location_ids.ids), ('location_dest_id', 'in', sl_dest_location_ids.ids),
                     ('product_id', '=', rec.id), ('state', '=', 'assigned'), ('picking_code', '=', 'outgoing')])
                res[rec.id]['outgoing_qty'] = res[rec.id]['outgoing_qty'] + sum(sl_move_ids.mapped('product_uom_qty'))
                res[rec.id]['virtual_available'] = res[rec.id]['virtual_available'] - sum(sl_move_ids.mapped('product_uom_qty'))

            sl_location_ids = self.env['stock.location'].sudo().search(
                [('usage', '=', 'internal'), ('company_id.is_logistics', '=', True)])

            sl_dest_location_ids = self.env['stock.location'].sudo().search(
                [('usage', '=', 'internal'), ('is_omit_on_source_location', '=', True), ('company_id.is_logistics', '=', True)])

            if sl_location_ids and sl_dest_location_ids and self.env.companies.filtered(lambda l: l.is_oxford):
                sl_move_ids = Move.sudo().search(
                    [('location_id', 'in', sl_location_ids.ids), ('location_dest_id', 'in', sl_dest_location_ids.ids),
                     ('product_id', '=', rec.id), ('state', '=', 'assigned'), ('picking_code', '=', 'internal')])
                res[rec.id]['outgoing_qty'] = res[rec.id]['outgoing_qty'] + sum(sl_move_ids.mapped('product_uom_qty'))
                res[rec.id]['virtual_available'] = res[rec.id]['virtual_available'] - sum(sl_move_ids.mapped('product_uom_qty'))

        return res

    @api.model
    def get_views(self, views, options=None):
        if self.env.user.has_group('user_warehouse_restriction.user_carote_restriction_group_user'):
            if options:
                options['toolbar'] = False
        res = super().get_views(views, options)
        # if self.env.user.id in BLOCK_USER and res.get('views'):
        #     if res.get('views', {}).get('list', {}).get('arch', "") and 'tree' in res.get('views', {}).get('list',
        #                                                                                                    {}).get(
        #             'arch', ""):
        #         data = res['views']['list']['arch']
        #         data = data.replace("tree", 'tree create="false"', 1)
        #         res['views']['list']['arch'] = data
        #     if res.get('views', {}).get('form', {}).get('arch', "") and 'form' in res.get('views', {}).get('form',
        #                                                                                                    {}).get(
        #             'arch', ""):
        #         data = res['views']['form']['arch']
        #         data = data.replace("form", 'form create="false"', 1)
        #         res['views']['form']['arch'] = data
        #     if res.get('views', {}).get('kanban', {}).get('arch', "") and 'kanban' in res.get('views', {}).get('kanban',
        #                                                                                                        {}).get(
        #             'arch', ""):
        #         data = res['views']['kanban']['arch']
        #         data = data.replace("kanban", 'kanban create="false"', 1)
        #         res['views']['kanban']['arch'] = data
        return res

    # def write(self, vals):
    #     if self.env.user.has_group('user_warehouse_restriction.user_carote_restriction_group_user'):
    #         raise UserError(_("You don't have enough access, Please contact your system administrator."))
    #     res = super(ProductProduct, self).write(vals)
    #     return res
