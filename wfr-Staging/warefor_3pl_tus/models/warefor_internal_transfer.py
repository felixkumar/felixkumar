from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError

import logging
_logger = logging.getLogger('Transferring Internal Transfer Line')

class WareforInternalTransfer(models.Model):
    _name = 'warefor.internal.transfer'
    _description = 'Warefor Internal Transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name")
    freight_id = fields.Many2one(comodel_name="freight.freight", string="Logistics Records")
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse", tracking=True)
    date = fields.Datetime(string="Date", default=fields.Datetime.now)
    # picking_id = fields.Many2one(comodel_name="stock.picking", string=_("Transfer"))
    internal_transfer_ids = fields.One2many(comodel_name="internal.transfer.line", inverse_name="internal_transfer_id",
                                       string="Transfer Inventory")
    # status_id = fields.Many2one(related="picking_id.state", string="Status")
    picking_ids = fields.Many2many("stock.picking", string="Transfer Record", copy=False)
    warefor_internal_transfers_count = fields.Integer(string='Transfers Count', copy=False)
    internal_transfer_stage_id = fields.Selection(string="Stage", tracking=True,
                                    selection=[('draft', 'Draft'), ('in_progress', 'IN PROGRESS'),
                                               ('done', 'Done'), ('cancel', 'Cancel')], default='draft')
    active = fields.Boolean(_('Active'), default=True)
    validate_user_ids = fields.Many2many('res.users', string="Validate User")
    validate_user_name = fields.Char(string="Name", compute="_compute_validate_user_name")

    @api.depends('validate_user_ids')
    def _compute_validate_user_name(self):
        for record in self:
            name = ""
            validate_user = record.validate_user_ids.mapped('name')
            if validate_user:
                name = " | ".join(validate_user)
            record.validate_user_name = name

    # @api.onchange('warehouse_id')
    # def onchange_warehouse_id(self):
    #     for rec in self:
    #         if rec.warehouse_id and rec.name and len(rec.name.split('/')) >= 2:
    #             name = rec.name.split('/')
    #             rec.name = "{}/INT/{}".format(rec.warehouse_id.code, name[-1])

    # @api.onchange('picking_ids')
    # def onchange_picking_ids_internal_transfer(self):
    #     for record in self:
    #         states = record.picking_ids.mapped('state')
    #         if 'done' in states:
    #             record.active = False

    def action_transfer_cancel(self):
        for rec in self:
            rec.internal_transfer_stage_id = "cancel"
            rec.picking_ids.action_cancel()
            # rec.

    def button_warefor_internal_transfers(self):
        picking_ids = self.picking_ids.ids
        return {
            'name': _('Transfers'),
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', picking_ids)],
        }

    # @api.depends('picking_ids')
    # def _compute_internal_transfer_picking_ids(self):
    #     for record in self:
    #         record.warefor_internal_transfers_count = len(record.picking_ids)
    #         # name = "/"
    #         # transfer = record.picking_ids.mapped('name')
    #         # if transfer:
    #         #     name = " | ".join(transfer)
    #         # record.name = name
    #         for picking_id in record.picking_ids:
    #             picking_id.custom_internal_transfer_id = record.id

    @api.model
    def default_get(self, fields):
        int_transfer_list =[]
        res = super(WareforInternalTransfer, self).default_get(fields)
        active_id = self._context.get('active_id')
        freight_id = self.env['freight.freight'].browse(active_id)
        for line in freight_id.osd_transfer_ids:
            line_val = (0, 0, {
                'sku_id': line.sku_id and line.sku_id.id or None,
                'quantity': line.quantity,
                'lot_id': line.lot_id,
                'location_id': line.location_id,
                'destination_location_id': line.destination_location_id,
                'destination_location_on_hand_qty': line.on_hand_qty,
            })
            int_transfer_list.append(line_val)
        res.update({'freight_id': freight_id,"internal_transfer_ids": int_transfer_list, 'warehouse_id': freight_id.warehouse_id})
        return res


    def create_warehouse_internal_transfer(self):
        internal_transfer_id = self.internal_transfer_ids
        if not internal_transfer_id.destination_location_id:
            raise ValidationError("Please select the Destination location for transfer the inventory!")
        if not internal_transfer_id.location_id:
            raise ValidationError("Please select the Source location for transfer the inventory!")
        if not internal_transfer_id.sku_id:
            raise ValidationError("Product not found in record!")
        for line in self.internal_transfer_ids:
            pick_picking_id = self.env['stock.picking'].create({
                'location_id': line.location_id.id,
                'location_dest_id': line.destination_location_id.id,
                'move_type': 'direct',
                'immediate_transfer': True,
                'picking_type_id': self.warehouse_id.int_type_id.id,
                'is_locked': True,
                'company_id': line.location_id.company_id.id,
                'freight_record_id': self.freight_id.id,
                'custom_internal_transfer_id': line.internal_transfer_id.id,
            })
            self.write({'picking_ids': [(4, pick_picking_id.id)]})
            self.freight_id.write({'picking_ids': [(4, pick_picking_id.id)]})
            line.picking_id = pick_picking_id.id
            line_vals = {
                'name': line.sku_id.name,
                'location_id': pick_picking_id.location_id.id,
                'location_dest_id': pick_picking_id.location_dest_id.id,
                'picking_id': pick_picking_id.id,
                'product_id': line.sku_id.id,
                'product_uom': line.sku_id.uom_id.id,
                'quantity_done': line.quantity,
                'product_uom_qty': line.quantity,
                'company_id': pick_picking_id.company_id.id,
                'lot_ids': [(6, 0, line.lot_id.ids)]
            }
            move_id = self.env['stock.move'].create(line_vals)
            if pick_picking_id.picking_type_id.is_default_mark_todo:
                pick_picking_id.action_assign()
                if line.lot_id:
                    pick_picking_id.move_line_ids.write({'lot_id': line.lot_id.id})
                move_line_ids = pick_picking_id.move_line_ids[1:]
                move_line_ids.unlink()
                pick_picking_id.action_confirm()
            self.internal_transfer_stage_id = 'in_progress'
            _logger.info("1] Created Move: {}, move ids: {}, move qty: {}".
                         format(move_id.id, pick_picking_id.move_line_ids.ids,
                                pick_picking_id.move_line_ids.mapped('qty_done')))
        self.warefor_internal_transfers_count = len(self.picking_ids)

    @api.model
    def create(self, val):
        if not val.get("name"):
            sequence = self.env['ir.sequence'].next_by_code('warefor.internal.transfer')
            val["name"] = sequence
            # if val.get('warehouse_id'):
            #     warehouse_id = self.env['stock.warehouse'].search([('id', '=', val.get('warehouse_id'))])
            #     if warehouse_id:
            #         val["name"] = warehouse_id.code + '/' + sequence
            #     else:
            #         val["name"] = sequence
            # else:
            #     val["name"] = sequence
        res = super(WareforInternalTransfer, self).create(val)
        return res


    def write(self, vals):
        # if vals.get('warehouse_id'):
        #     if self.warehouse_id and self.name and len(self.name.split('/')) >= 2:
        #         name = self.name.split('/')
        #         vals['name'] = "{}/INT/{}".format(self.warehouse_id.code, name[-1])
        result = super(WareforInternalTransfer, self).write(vals)
        self.internal_transfer_ids.onchange_location_id_internal_transfer()
        self.internal_transfer_ids.onchange_destination_location_id_internal_transfer()
        return result

class InternalTransferLine(models.Model):
    _name = 'internal.transfer.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Warefor Internal Transfer Line'

    freight_id = fields.Many2one(comodel_name="freight.freight", string="PL Record", tracking=True)
    warehouse_id = fields.Many2one(related="internal_transfer_id.warehouse_id", string="Warehouse", store=True)
    internal_transfer_id = fields.Many2one(comodel_name="warefor.internal.transfer", string="Internal Record", tracking=True)
    sku_id = fields.Many2one(comodel_name="product.product", string="SKU", tracking=True)
    description = fields.Char(related="sku_id.name", string="Description", tracking=True)
    quantity = fields.Float(string="QTY", digits=(999, 0), tracking=True)
    lot_id = fields.Many2one('stock.lot', 'Lot #', domain="[('product_id', '=', sku_id)]")
    location_id = fields.Many2one("stock.location", string="Location")
    source_location_on_hand_qty = fields.Float(string="QTY on Hand")
    destination_location_id = fields.Many2one(comodel_name="stock.location", string="Location")
    destination_location_on_hand_qty = fields.Float(string="QTY on Hand")
    is_validated = fields.Boolean(string="Is Validated")
    is_created = fields.Boolean(string="Is Created")
    picking_id = fields.Many2one("stock.picking", string="Transfer")


    @api.onchange('destination_location_id')
    def onchange_destination_location_id_internal_transfer(self):
        for rec in self:
            if rec.sku_id and rec.destination_location_id:
                rec.destination_location_on_hand_qty = self.env['stock.quant']._get_available_quantity(rec.sku_id, rec.destination_location_id)

    @api.onchange('location_id')
    def onchange_location_id_internal_transfer(self):
        for rec in self:
            if rec.sku_id and rec.location_id:
                rec.source_location_on_hand_qty = self.env['stock.quant']._get_available_quantity(rec.sku_id, rec.location_id)

    def create_warehouse_internal_transfer_button(self):
        # internal_transfer_id = self.internal_transfer_ids
        if not self.destination_location_id:
            raise ValidationError("Please select the Destination location for transfer the inventory!")
        if not self.location_id:
            raise ValidationError("Please select the Source location for transfer the inventory!")
        if not self.sku_id:
            raise ValidationError("Product not found in record!")
        for line in self:
            pick_picking_id = self.env['stock.picking'].create({
                'location_id': line.location_id.id,
                'location_dest_id': line.destination_location_id.id,
                'move_type': 'direct',
                'immediate_transfer': True,
                'picking_type_id': self.warehouse_id.int_type_id.id,
                'is_locked': True,
                'company_id': line.location_id.company_id.id,
                'freight_record_id': self.freight_id.id,
                'custom_internal_transfer_id': line.internal_transfer_id.id,
            })
            self.internal_transfer_id.write({'picking_ids': [(4, pick_picking_id.id)]})
            self.internal_transfer_id.freight_id.write({'picking_ids': [(4, pick_picking_id.id)]})
            line.picking_id = pick_picking_id.id
            line_vals = {
                'name': line.sku_id.name,
                'location_id': pick_picking_id.location_id.id,
                'location_dest_id': pick_picking_id.location_dest_id.id,
                'picking_id': pick_picking_id.id,
                'product_id': line.sku_id.id,
                'product_uom': line.sku_id.uom_id.id,
                'quantity_done': line.quantity,
                'product_uom_qty': line.quantity,
                'company_id': pick_picking_id.company_id.id,
                'lot_ids': [(6, 0, line.lot_id.ids)]
            }
            move_id = self.env['stock.move'].create(line_vals)
            if pick_picking_id.picking_type_id.is_default_mark_todo:
                pick_picking_id.action_assign()
                if line.lot_id:
                    pick_picking_id.move_line_ids.write({'lot_id': line.lot_id.id})
                move_line_ids = pick_picking_id.move_line_ids[1:]
                move_line_ids.unlink()
                pick_picking_id.action_confirm()
            self.internal_transfer_id.internal_transfer_stage_id = 'in_progress'
            _logger.info("1] Created Move: {}, move ids: {}, move qty: {}".
                         format(move_id.id, pick_picking_id.move_line_ids.ids,
                                pick_picking_id.move_line_ids.mapped('qty_done')))
        self.internal_transfer_id.warefor_internal_transfers_count = len(self.internal_transfer_id.picking_ids)
        self.is_created = True

    def validate_internal_transfer(self):
        picking_id = self.picking_id

        if picking_id.state not in ['draft', 'waiting']:
            picking_id.action_assign()
            if self.lot_id:
                picking_id.move_line_ids.write({'lot_id': self.lot_id.id})

        if picking_id.state == 'confirmed':
            picking_id.action_confirm()

        picking_id.button_validate()
        self.is_validated = True
        self.onchange_location_id_internal_transfer()
        self.onchange_destination_location_id_internal_transfer()
        # self.internal_transfer_id.active = False
        self.internal_transfer_id.validate_user_ids = [(4, self.env.uid)]

        if picking_id.state == 'done':
            self.internal_transfer_id.internal_transfer_stage_id = 'done'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': 'Internal Transfer Has been Validated.',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }}
    #
    # def write(self, vals):
    #     self.onchange_location_id_internal_transfer()
    #     self.onchange_destination_location_id_internal_transfer()
