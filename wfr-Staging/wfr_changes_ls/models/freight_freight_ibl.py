from odoo import api, fields, models
from dateutil.relativedelta import relativedelta, MO
from odoo.exceptions import ValidationError


class FreightFreightIBLInherit(models.Model):
    _inherit = 'freight.freight'

    shipping_info_etd = fields.Date("ETD")
    available_to_order = fields.Date("Available to Order Date")
    hide_transfers_btn = fields.Boolean("Hide Transfer Button", compute="_compute_hide_transfers")

    plan_production_scheduled_date = fields.Datetime("Production Scheduled Date")
    plan_expected_completion_date = fields.Datetime("Expected Completion Date")
    plan_actual_completion_date = fields.Datetime("Actual Completion Date")

    import_id = fields.Many2one('res.partner', copy=False, string="Supplier")

    def copy_freight_data(self):
        default = {
            'partner_id': self.partner_id.id
        }
        res = super().copy(default=default)
        return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': res.id,
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'current',
                }

    @api.onchange('shipping_info_etd')
    def _onchange_shipping_info_etd(self):
        if self.shipping_info_etd:
            self.estimated_arrival_date = self.shipping_info_etd + relativedelta(days=30)

    @api.onchange('estimated_arrival_date')
    def _onchange_estimated_arrival_date(self):
        if self.estimated_arrival_date:
            self.pickup_schedule_date = self.estimated_arrival_date + relativedelta(days=7)

    def action_planned_production(self):
        for rec in self:
            if self.env.user.has_group('user_warehouse_restriction.user_carote_restriction_group_user'):
                return True
            if not rec.freight_order_line_ids:
                raise ValidationError("Please enter at least one product in the Order Lines Table")
            for line in rec.osd_transfer_ids:
                line.ibl_create_transfers()
            planned_production_stage = self.env['freight.stage'].search([('name', '=', 'Planned Production')], limit=1)
            rec.stage_id = planned_production_stage.id

    @api.onchange('pickup_schedule_date')
    def _onchange_pickup_schedule_date(self):
        if self.pickup_schedule_date:
            self.available_to_order = self.pickup_schedule_date + relativedelta(days=+1, weekday=MO(+1))

    def _compute_hide_transfers(self):
        self.hide_transfers_btn = False
        check_in_stage = self.env['freight.stage'].search([('name', '=', 'Checked In')], limit=1)
        if self.stage_id and self.stage_id.sequence < check_in_stage.sequence:
            self.hide_transfers_btn = True

    @api.constrains('pickup_schedule_date')
    def _set_transfers_scheduled_date(self):
        if self.picking_ids:
            for pick in self.picking_ids.filtered(lambda x: x.state != 'done'):
                pick.write({"scheduled_date": self.pickup_schedule_date})


    def sync_osd_freight_lines(self):
        # Updates the Freight Order Lines with the Pallet Type, Sub Pallet and the SSCC-18 barcode
        # from the OSD Transfer Lines in Warehouse Ops
        for rec in self:
            throw_error = False
            if rec.is_outbound:
                for line in rec.osd_transfer_ids:
                    if not line.freight_order_line_id and line.po_number:
                        line.freight_order_line_id = line.po_number
                    if line.freight_order_line_id:
                        vals = {
                            'sscc_18_char': line.sscc_18_char,
                            'sub_pallet': line.sub_pallet,
                            'pallet_type': line.pallet_type,
                        }
                        if line.freight_order_line_id.total_quantity != line.quantity:
                            vals['total_quantity'] = line.quantity
                            vals['is_processed'] = False
                        if line.freight_order_line_id.goods.id != line.sku_id.id:
                            vals['goods'] = line.sku_id.id
                        line.freight_order_line_id.write(vals)
                    else:
                        throw_error = True
                if throw_error:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Missing Freight Association!',
                            'message': "Some or all OSD Lines did not have Freight Lines associated with it",
                            'type': 'warning',
                            'sticky': False
                        },
                    }
