# -*- coding: utf-8 -*-

import logging

from odoo.osv import expression
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    is_3pl_warehouse = fields.Boolean(string="3PL Warehouse?", default=False)
    bulk_route_id = fields.Many2one('stock.route', string='Bulk Route')
    ecommerce_route_id = fields.Many2one('stock.route', string='eCommerce Route')

    def configure_3d_rack(self):
        rack_3d = self.env['racks.configuration'].search([('warehouse_id', '=', self.id)])
        if not rack_3d:
            raise ValidationError(_('There is no Rack Configuration.Please configure it first.'))

        if not rack_3d.limit:
            raise ValidationError(_('Limit is not defined.Please configure it first.'))

        _logger.info("Configuring rack limit is:{}".format(rack_3d.limit))

        racks = self.env['stock.location'].search([('company_id', '=', self.company_id.id), ('is_rack', '=', True)],
                                                  order='id')
        # racks.write({'warehouse_id': self.id})
        if not racks:
            raise ValidationError(_('There is no Rack Locations.Please Configure it first.'))

        rack_in_location = self.company_id.rack_in_location
        if not self.company_id.rack_in_location:
            raise ValidationError(_('There is not configured racks in setting, please first configure it.'))

        racks.write(
            {
                'posx': 0,
                'posy': 0,
                'posz': 0,
                'sizex': 0,
                'sizey': 0,
                'sizez': 0,
            }
        )
        racks = racks[:rack_3d.limit]
        rows = rack_3d.row
        columns = rack_3d.column

        total_fil_racks = rows * columns

        other_rack = len(racks) % rack_in_location
        total_rack = len(racks) / rack_in_location
        total_rack += other_rack and 1 or 0
        if int(total_rack) > total_fil_racks:
            raise ValidationError(_('Rack is more than size of pallet.'))
        else:
            _logger.info("Total processing racks: {}".format(racks.ids))
            spx = rack_3d.starting_position_x
            size_x = rack_3d.size_x
            size_y = rack_3d.size_y
            size_z = rack_3d.size_z
            row_space = rack_3d.row_space
            column_space = rack_3d.column_space
            rack_space = rack_3d.rack_space
            toggle_row = rack_3d.toggle_row
            toggle_column = rack_3d.toggle_column
            for column in range(1, columns + 1):
                spy = rack_3d.starting_position_y
                for row in range(1, rows + 1):
                    move_rack = racks[:self.company_id.rack_in_location]
                    racks -= move_rack
                    spz = rack_3d.starting_position_z
                    for rack in move_rack:
                        rack.posx = spx
                        rack.posy = spy
                        rack.posz = spz
                        rack.sizex = size_x
                        rack.sizey = size_y
                        rack.sizez = size_z

                        spz += size_z + rack_space
                    if toggle_row:
                        if (row % 2) == 0:
                            spy += row_space
                        spy += size_y
                    else:
                        spy += size_y + row_space
                if toggle_column:
                    if (column % 2) == 0:
                        spx += column_space
                    spx += size_x
                else:
                    spx += size_x + column_space


class StockLocation(models.Model):
    _inherit = 'stock.location'

    building = fields.Char(string="Building")
    sub_inventory = fields.Char(string="Sub Inventory")
    aisle_location = fields.Char(string="Aisle Location")
    level_configuration = fields.Char(string="Level Configuration")
    pallet_positions_area = fields.Char(string="Pallet Positions Area")
    stored_pallet = fields.Float(string="Stored Pallets", default=0.0)
    outbound_stored_pallet = fields.Float(string="# of Pallets", default=0.0, compute="_compute_outbound_stored_pallet")
    stored_rack = fields.Float(string="Stored Racks", compute="_compute_stored_rack")
    is_rack = fields.Boolean("Is Rack Location?", default=False)
    rack_ids = fields.One2many(comodel_name="stock.location", inverse_name="location_id", string="Rack Ids")
    is_inventory_adjustment_location = fields.Boolean("Is Inventory Adjustment Location?", default=False)
    is_outbound_location = fields.Boolean("Is Outbound Location?", default=False)
    available_stock = fields.Float(string="Available Stock", compute="_compute_available_stock", default=0.0)
    product_per_pallet = fields.Float(string="Product per Pallet", compute="_compute_product_per_pallet", default=0.0)
    is_destination_location = fields.Boolean("Is Destination Location?", default=False)
    is_omit_on_source_location = fields.Boolean("Is Omit On Source Location?", default=False)
    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse", copy=False)
    is_pallet = fields.Boolean(string="Is Pallet")
    is_virtual_location = fields.Boolean("Is Virtual Location?", default=False)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if 'complete_name' in str(domain):
            len = str(domain).count('complete_name')
            if len:
                name_domain = domain[len-1]
                barcode = name_domain[-1]
                domain = expression.OR([[['barcode', '=', barcode]], domain])
        return super(StockLocation, self).search_read(domain, fields, offset, limit, order)

    def get_empty_location(self):
        location_ids = self.env['stock.location'].search(
            [('outbound_stored_pallet', '<=', 0), ('usage', '=', 'internal')])
        return location_ids

    @api.onchange('building', 'sub_inventory', 'aisle_location', 'level_configuration', 'pallet_positions_area')
    def onchange_location_name(self):
        for record in self:
            if record.building:
                name = "{}{}{}{}{}".format(record.building and record.building + "-" or "",
                                           record.sub_inventory and record.sub_inventory + "-" or "",
                                           record.aisle_location and record.aisle_location + "-" or "",
                                           record.pallet_positions_area and record.pallet_positions_area or "",
                                           record.level_configuration and record.level_configuration + "-" or "")
                record.name = name

    @api.depends("rack_ids")
    def _compute_stored_rack(self):
        for rec in self:
            rec.stored_rack = 0
            if not rec.is_rack:
                rack_ids = rec.rack_ids
                rec.stored_rack = len(rack_ids.filtered(lambda l: l.stored_pallet))
                rec.stored_pallet = sum(rack_ids.mapped('stored_pallet'))

    @api.depends("quant_ids")
    def _compute_available_stock(self):
        for rec in self:
            quant_id = self.env['stock.quant'].search(
                [('location_id', 'child_of', rec.ids), ('company_id', 'in', self.env.company.ids)])
            if quant_id:
                rec.available_stock = sum(quant_id.mapped('quantity'))
            else:
                rec.available_stock = 0
    @api.depends("quant_ids")
    def _compute_product_per_pallet(self):
        for rec in self:
            quant_id = self.env['stock.quant'].search(
                [('location_id', 'child_of', rec.ids), ('company_id', 'in', self.env.company.ids)])
            if quant_id:
                rec.product_per_pallet = sum(quant_id.mapped('product_id').mapped('product_per_pallet'))
            else:
                rec.product_per_pallet = 0
    @api.depends("quant_ids")
    def _compute_outbound_stored_pallet(self):
        for rec in self:
            quant_id = self.env['stock.quant'].search([('location_id', 'child_of', rec.ids), ('company_id', 'in', self.env.company.ids)])
            if sum(quant_id.mapped('product_id').mapped('product_per_pallet')):
                rec.outbound_stored_pallet = sum(quant_id.mapped('quantity')) / sum(quant_id.mapped('product_id').mapped('product_per_pallet'))
            else:
                rec.outbound_stored_pallet = 0.0


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    is_inventory_adjustment = fields.Boolean("Transfer Without PO?", default=False, copy=False)
    is_default_mark_todo = fields.Boolean("Mark as ToDo By Default?", default=False, copy=False)

    def name_get(self):
        """ Display 'Warehouse_name: PickingType_name'

        OVERRIDE FOR MULTI-WAREHOUSE SECURITY MANAGEMENT
        """
        res = []
        for picking_type in self.sudo():
            if picking_type.warehouse_id:
                name = picking_type.warehouse_id.name + ': ' + picking_type.name
            else:
                name = picking_type.name
            res.append((picking_type.id, name))
        return res
