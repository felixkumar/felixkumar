# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tests import Form

_logger = logging.getLogger(__name__)


class StockPickingToBatch(models.TransientModel):
    _inherit = 'stock.picking.to.batch'

    validate_and_create_all_batch = fields.Boolean(string="Process Pick, Pack and Ship In Group?",
                                                   help='When checked, create the batch and validate it automatically',
                                                   default=True)
    mode = fields.Selection(selection_add=[('existing_group', 'an existing batch transfer group')])
    batch_group_id = fields.Many2one("stock.picking.batch.group", "Batch Group",
                                     domain=[("create_date", ">=", fields.Date.today())])

    def attach_pickings(self):
        if self.validate_and_create_all_batch:
            self.ensure_one()
            batch_group = False
            pickings = self.env['stock.picking'].browse(self.env.context.get('active_ids'))
            if self.mode in ['new', 'existing_group']:
                pack_batch = False
                company = pickings.company_id
                if len(company) > 1:
                    raise UserError(_("The selected pickings should belong to an unique company."))

                today = fields.Date.context_today(self)  # Get today's date

                total_batch = self.env['stock.picking.batch.group'].search_count(
                    [('create_date', '>=', str(today) + ' 00:00:00'), ('create_date', '<=', str(today) + ' 23:59:59')])

                total_batch += 1

                total_batch = "{}{}".format((3 - len(str(total_batch))) * "0", total_batch)

                # group_name = self.env['ir.sequence'].next_by_code('picking.batch.group') or '/'
                group_name = "{}/{}".format(today, total_batch)

                warehouse_id = False
                if pickings:
                    warehouse_id = pickings[0].location_id.warehouse_id
                if warehouse_id:
                    group_name = "{}/{}/{}".format(warehouse_id.name, today, total_batch)

                user_id = self.user_id.id or warehouse_id and warehouse_id.user_id.id

                if self.mode == 'new':
                    batch_group = self.env['stock.picking.batch.group'].create({
                        'name': group_name,
                        'user_id': user_id,
                        'warehouse_id': warehouse_id and warehouse_id.id,
                    })
                else:
                    batch_group = self.batch_group_id

                if not batch_group:
                    raise UserError("Didn't find a batch group record!")

                if self.mode == 'new':
                    pick_batch = self.env['stock.picking.batch'].create({
                        'user_id': user_id,
                        'company_id': company.id,
                        'is_pick_batch': True,
                        'picking_type_id': pickings[0].picking_type_id.id,
                        'batch_group_id': batch_group.id,
                    })
                    pick_batch.name = "PICK-{}".format(pick_batch.name)
                else:
                    pick_batch = batch_group.batch_ids.filtered(lambda b: b.is_pick_batch)
                    if not pick_batch:
                        pick_batch = self.env['stock.picking.batch'].create({
                            'user_id': user_id,
                            'company_id': company.id,
                            'is_pick_batch': True,
                            'picking_type_id': pickings[0].picking_type_id.id,
                            'batch_group_id': batch_group.id,
                        })
                        pick_batch.name = "PICK-{}".format(pick_batch.name)

                pack_ids = self.env['stock.picking'].search(
                    [('group_id', 'in', pickings.group_id.ids), ('name', 'ilike', 'PACK')])
                if pack_ids:
                    if self.mode == 'new':
                        pack_batch = self.env['stock.picking.batch'].create({
                            'user_id': user_id,
                            'company_id': company.id,
                            'picking_type_id': pack_ids[0].picking_type_id.id,
                            'parent_batch_id': pick_batch.id,
                            'is_pack_batch': True,
                            'batch_group_id': batch_group.id,
                        })
                        pack_batch.name = "PACK-{}".format(pack_batch.name)
                    else:
                        pack_batch = batch_group.batch_ids.filtered(lambda b: b.is_pack_batch)
                        if not pack_batch:
                            pack_batch = self.env['stock.picking.batch'].create({
                                'user_id': user_id,
                                'company_id': company.id,
                                'picking_type_id': pack_ids[0].picking_type_id.id,
                                'parent_batch_id': pick_batch.id,
                                'is_pack_batch': True,
                                'batch_group_id': batch_group.id,
                            })
                            pack_batch.name = "PACK-{}".format(pack_batch.name)
                    pack_ids.write({'batch_id': pack_batch.id})
                out_ids = self.env['stock.picking'].search(
                    [('group_id', 'in', pickings.group_id.ids), ('picking_type_code', '=', 'outgoing')])
                if out_ids and pack_batch:
                    if self.mode == 'new':
                        out_batch = self.env['stock.picking.batch'].create({
                            'user_id': user_id,
                            'company_id': company.id,
                            'picking_type_id': out_ids[0].picking_type_id.id,
                            'parent_batch_id': pack_batch.id,
                            # 'process_from_cron': True,
                            'is_ship_batch': True,
                            'batch_group_id': batch_group.id,
                        })
                        out_batch.name = "SHIP-{}".format(out_batch.name)
                    else:
                        out_batch = batch_group.batch_ids.filtered(lambda b: b.is_ship_batch)
                        if not out_batch:
                            out_batch = self.env['stock.picking.batch'].create({
                                'user_id': user_id,
                                'company_id': company.id,
                                'picking_type_id': out_ids[0].picking_type_id.id,
                                'parent_batch_id': pack_batch.id,
                                # 'process_from_cron': True,
                                'is_ship_batch': True,
                                'batch_group_id': batch_group.id,
                            })
                            out_batch.name = "SHIP-{}".format(out_batch.name)
                    out_ids.write({'batch_id': out_batch.id})
            else:
                pick_batch = self.batch_id

            pickings.write({'batch_id': pick_batch.id})
            # you have to set some pickings to batch before confirm it.
            if self.mode in ['new', 'existing_group'] and not self.is_create_draft and batch_group:
                if pick_batch.state == 'draft':
                    pick_batch.action_confirm()
                batch_group.batch_stock_line_ids.unlink()
                batch_group.batch_product_line_ids.unlink()
                if pick_batch.move_line_ids:
                    bs_lines = self.env['batch.stock.line']
                    bp_lines = self.env['batch.product.line']
                    for move_line in pick_batch.move_line_ids:
                        t_bs_line = bs_lines.filtered(lambda
                                                          bl: bl.product_id.id == move_line.product_id.id and bl.location_id.id == move_line.location_id.id)
                        if t_bs_line:
                            t_bs_line.quantity = t_bs_line.quantity + move_line.reserved_uom_qty
                        else:
                            vals = {
                                'product_id': move_line.product_id.id,
                                'location_id': move_line.location_id.id,
                                'quantity': move_line.reserved_uom_qty,
                                'batch_group_id': batch_group.id
                            }
                            bs_lines |= bs_lines.create(vals)
                        t_bp_line = bp_lines.filtered(lambda bp: bp.product_id.id == move_line.product_id.id)
                        if t_bp_line:
                            t_bp_line.quantity = t_bp_line.quantity + move_line.reserved_uom_qty
                        else:
                            vals = {
                                'product_id': move_line.product_id.id,
                                'quantity': move_line.reserved_uom_qty,
                                'batch_group_id': batch_group.id
                            }
                            bp_lines |= bp_lines.create(vals)

                # wiz = pick_batch.action_done()
                # if wiz and isinstance(wiz, dict) and wiz.get('res_model', False) == 'stock.immediate.transfer':
                #     try:
                #         wiz = Form(self.env['stock.immediate.transfer'].with_context(wiz['context'])).save()
                #         wiz = wiz.process()
                #     except Exception as exception:
                #         _logger.info("stock.immediate.transfer : Error {} comes at the time of "
                #                      "creating back order in picking".format(exception))

                return {
                    'name': batch_group.name,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.picking.batch.group',
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                    'res_id': batch_group.id,
                }
                # return {
                #     'effect': {
                #         'fadeout': 'slow',
                #         'message': "Yeah! Batch Group Created!",
                #         'img_url': '/web/static/img/smile.svg',
                #         'type': 'rainbow_man',
                #     }
                # }
        else:
            return super(StockPickingToBatch, self).attach_pickings()
