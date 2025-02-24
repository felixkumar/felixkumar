# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from threading import Thread
import time
import logging

from odoo import api, fields, models, _, registry, SUPERUSER_ID
from odoo.tests import Form
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockPickingBatch(models.Model):
    _name = "stock.picking.batch.group"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Group of picking batch"

    name = fields.Char("Name")
    batch_ids = fields.One2many("stock.picking.batch", 'batch_group_id', string="Batches")
    is_validated_pick = fields.Boolean("Is Validated Pick?")
    is_validated_pack = fields.Boolean("Is Validated Pack?")
    is_validated_ship = fields.Boolean("Is Validated Ship?")
    state = fields.Selection(
        [('draft', 'Draft'), ('in_progress', 'In Progress'), ('done', 'Done'), ('cancel', 'Cancelled')], 'Status',
        required=True, copy=False, default='draft')
    processed_time = fields.Char("Processed Time", compute="compute_restricted_weekdays")
    user_id = fields.Many2one("res.users", string="Responsible")
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse")
    batch_stock_line_ids = fields.One2many("batch.stock.line", 'batch_group_id', string="Stock Line")
    batch_product_line_ids = fields.One2many("batch.product.line", 'batch_group_id', string="Stock Line")

    @api.depends("write_date")
    def compute_restricted_weekdays(self):
        for rec in self:
            start = rec.create_date
            end = rec.write_date
            duration = (end - start).total_seconds() / 3600  # Convert seconds to hours
            rec.processed_time = "{} Hours".format(round(duration, 2))

    def validate_pick_batch(self):
        pick_batch = self.batch_ids.filtered(lambda b: b.is_pick_batch and b.state in ['draft', 'in_progress'])
        if pick_batch:
            self.state = 'in_progress'
            if pick_batch.state == 'draft':
                pick_batch.action_confirm()
            wiz = pick_batch.action_done()
            if isinstance(wiz, bool):
                if wiz:
                    self.is_validated_pick = True
                return wiz
            if wiz and isinstance(wiz, dict) and wiz.get('res_model', False) == 'stock.immediate.transfer':
                try:
                    wiz = Form(self.env['stock.immediate.transfer'].with_context(wiz['context'])).save()
                    wiz = wiz.process()
                except Exception as exception:
                    _logger.info("stock.immediate.transfer : Error {} comes at the time of "
                                 "creating back order in picking".format(exception))
                self.is_validated_pick = True
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': "Yeah! Pick Batch Process Started!",
                        'img_url': '/web/static/img/smile.svg',
                        'type': 'rainbow_man',
                    }
                }
            if wiz and isinstance(wiz, dict) and wiz.get('res_model', False) == 'stock.backorder.confirmation':
                return wiz
            raise UserError(_("Unable to process Pick Batch, Please contact an Administrator."))

    def validate_pack_batch(self):
        pack_batch = self.batch_ids.filtered(lambda b: b.is_pack_batch and b.state in ['draft', 'in_progress'])
        if pack_batch:
            self.state = 'in_progress'
            if pack_batch.state == 'draft':
                pack_batch.action_confirm()
            wiz = pack_batch.action_done()
            if isinstance(wiz, bool):
                if wiz:
                    self.is_validated_pack = True
                return wiz
            if wiz and isinstance(wiz, dict) and wiz.get('res_model', False) == 'stock.immediate.transfer':
                try:
                    wiz = Form(self.env['stock.immediate.transfer'].with_context(wiz['context'])).save()
                    wiz = wiz.process()
                except Exception as exception:
                    _logger.info("stock.immediate.transfer : Error {} comes at the time of "
                                 "creating back order in picking".format(exception))
                self.is_validated_pack = True
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': "Yeah! Pack Batch Process Started!",
                        'img_url': '/web/static/img/smile.svg',
                        'type': 'rainbow_man',
                    }
                }
            if wiz and isinstance(wiz, dict) and wiz.get('res_model', False) == 'stock.backorder.confirmation':
                return wiz
            raise UserError(_("Unable to process Pack Batch, Please contact an Administrator."))

    def validate_ship_batch(self):
        ship_batch = self.batch_ids.filtered(lambda b: b.is_ship_batch and b.state in ['draft', 'in_progress'])
        if ship_batch:
            self.state = 'in_progress'
            if ship_batch.state == 'draft':
                ship_batch.action_confirm()
            wiz = ship_batch.action_done()
            if isinstance(wiz, bool):
                if wiz:
                    self.is_validated_ship = True
                return wiz
            if wiz and isinstance(wiz, dict) and wiz.get('res_model', False) == 'stock.immediate.transfer':
                try:
                    wiz = Form(self.env['stock.immediate.transfer'].with_context(wiz['context'])).save()
                    wiz = wiz.process()
                except Exception as exception:
                    _logger.info("stock.immediate.transfer : Error {} comes at the time of "
                                 "creating back order in picking".format(exception))
                self.is_validated_ship = True
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': "Yeah! Ship Batch Process Started!",
                        'img_url': '/web/static/img/smile.svg',
                        'type': 'rainbow_man',
                    }
                }
            if wiz and isinstance(wiz, dict) and wiz.get('res_model', False) == 'stock.backorder.confirmation':
                return wiz
            raise UserError(_("Unable to process Ship Batch, Please contact an Administrator."))

    def validate_all_batch(self):
        pick_batch = self.batch_ids.filtered(lambda b: b.is_pick_batch and b.state in ['draft', 'in_progress'])
        if pick_batch:
            self.state = 'in_progress'
            if pick_batch.state == 'draft':
                pick_batch.action_confirm()
            wiz = pick_batch.action_done()
            if isinstance(wiz, bool):
                if wiz:
                    all_batch = self.batch_ids - pick_batch
                    all_batch.write({'process_from_cron': True})
                    self.write({'is_validated_ship': True, 'is_validated_pick': True, 'is_validated_pack': True})
                return wiz
            if wiz and isinstance(wiz, dict) and wiz.get('res_model', False) == 'stock.immediate.transfer':
                try:
                    wiz = Form(self.env['stock.immediate.transfer'].with_context(wiz['context'])).save()
                    wiz = wiz.process()
                except Exception as exception:
                    _logger.info("stock.immediate.transfer : Error {} comes at the time of "
                                 "creating back order in picking".format(exception))
                all_batch = self.batch_ids - pick_batch
                all_batch.write({'process_from_cron': True})
                self.write({'is_validated_ship': True, 'is_validated_pick': True, 'is_validated_pack': True})
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': "Yeah! All Batch Process Started!",
                        'img_url': '/web/static/img/smile.svg',
                        'type': 'rainbow_man',
                    }
                }
            if wiz and isinstance(wiz, dict) and wiz.get('res_model', False) == 'stock.backorder.confirmation':
                return wiz
            raise UserError(_("Unable to process All Batch, Please contact an Administrator."))
        else:
            pick_batch = self.batch_ids.filtered(lambda b: b.is_pick_batch and b.state == 'done')
            if pick_batch:
                all_batch = self.batch_ids - pick_batch
                all_batch.write({'process_from_cron': True})
                self.write({'is_validated_ship': True, 'is_validated_pick': True, 'is_validated_pack': True})
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': "Yeah! All Batch Process Started!",
                        'img_url': '/web/static/img/smile.svg',
                        'type': 'rainbow_man',
                    }
                }

    def cancel_batch_action(self):
        """
        Cancel the batch group when click on cancel button
        """
        self.write({'state': 'cancel'})

    def action_mark_as_done(self):
        """
        Done the batch group when click on mark as done button
        """
        self.write({'state': 'done'})

    def auto_create_batch_group(self):
        company_ids = self.env['res.company'].search([('is_logistics', '=', True)])
        self = self.with_company(company_ids)
        warehouse_ids = self.env['stock.warehouse'].search(
            [('is_3pl_warehouse', '=', True), ('number_of_batch_group', '>=', 1)])
        stock_picking_batch_group_obj = self.env['stock.picking.batch.group']
        today = fields.Date.context_today(self)  # Get today's date

        for warehouse in warehouse_ids:
            t_ids = stock_picking_batch_group_obj.search(
                [('warehouse_id', '=', warehouse.id), ('create_date', '>=', today)])
            if not t_ids:
                for b_count in range(1, warehouse.number_of_batch_group + 1):
                    total_batch = b_count
                    total_batch = "{}{}".format((3 - len(str(total_batch))) * "0", total_batch)
                    group_name = "{}/{}/{}".format(warehouse.name, today, total_batch)
                    batch_group = self.env['stock.picking.batch.group'].create({
                        'name': group_name,
                        'user_id': warehouse.user_id.id,
                        'warehouse_id': warehouse.id,
                    })
        return True


class BatchStockLine(models.Model):
    _name = "batch.stock.line"
    _rec_name = "product_id"

    product_id = fields.Many2one("product.product", string="Product")
    location_id = fields.Many2one("stock.location", string="Location")
    quantity = fields.Float(string="Quantity", digits=(8, 2))
    batch_group_id = fields.Many2one("stock.picking.batch.group", string="Batch Group")


class BatchProductLine(models.Model):
    _name = "batch.product.line"
    _rec_name = "product_id"

    product_id = fields.Many2one("product.product", string="Product")
    quantity = fields.Float(string="Quantity", digits=(8, 2))
    batch_group_id = fields.Many2one("stock.picking.batch.group", string="Batch Group")
