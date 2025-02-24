from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountAssetAsset(models.Model):
    """
    Account Asset Asset Inherits
    """
    _inherit = 'account.asset.asset'

    multi_vendor_ids = fields.One2many('account.asset.multi.vendor.line', 'asset_id', string='Vendors')
    sell_or_dispose = fields.Boolean(default=False, string="Sell OR Dispose")

    # @api.onchange('multi_vendor_ids')
    # def onchange_amount(self):
    #     for rec in self:
    #         print('================')

    @api.depends('depreciation_line_ids.move_id')
    def _entry_count(self):
        """
        This method compute entry_count field value
        """
        for asset in self:
            move_ids = self.env['account.move'].search([('asset_id', '=', asset.id)])
            asset.entry_count = len(move_ids) or 0

    def set_to_close(self):
        """
        rtype: dict
        """
        move_ids = self._get_disposal_moves()
        move_ids = self.env['account.move'].browse(move_ids)
        self.sell_or_dispose = True
        if move_ids:
            move_ids.update({'asset_id': self.id})
            return self._return_disposal_view(move_ids.ids)
        # Fallback, as if we just clicked on the smartbutton
        return self.open_entries()

    def open_entries(self):
        """
        rtype: dict
        """
        move_ids = self.env['account.move'].search([('asset_id', '=', self.id)])
        return {
            'name': _('Journal Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', move_ids.ids)],
        }

    @api.depends('value', 'salvage_value', 'depreciation_line_ids.move_check',
                 'depreciation_line_ids.amount')
    def _amount_residual(self):
        """
        This method compute value_residual field value
        """
        for rec in self:
            total_amount = 0.0
            for line in rec.depreciation_line_ids:
                if line.move_check:
                    total_amount += line.amount
            rec.value_residual = rec.value - total_amount - rec.salvage_value
            if rec.multi_vendor_ids:
                move_ids = self.env['account.move'].search([('asset_id', '=', rec.id),
                                                            ('state', '=', 'posted')])
                rec.value_residual = rec.value - sum(move_ids.mapped('amount_total_signed'))

    def multi_vendor_bill(self):
        """
        This method create for 'SELL OR DISPOSE' Button
        """
        if self.multi_vendor_ids:
            for rec in self.multi_vendor_ids:
                if self.value_residual >= rec.amount and self.depreciation_line_ids:
                    move_vals = self.depreciation_line_ids[-1]._prepare_move(self.depreciation_line_ids[-1])
                    if move_vals.get('line_ids')[0][2].get('debit') > 0:
                        move_vals.get('line_ids')[0][2].update({'debit': rec.amount,
                                                                'partner_id': rec.vendor_id.id})
                    else:
                        move_vals.get('line_ids')[0][2].update({'credit': rec.amount,
                                                                'partner_id': rec.vendor_id.id})
                    if move_vals.get('line_ids')[1][2].get('debit') > 0:
                        move_vals.get('line_ids')[1][2].update({'debit': rec.amount,
                                                                'partner_id': rec.vendor_id.id})
                    else:
                        move_vals.get('line_ids')[1][2].update({'credit': rec.amount,
                                                                'partner_id': rec.vendor_id.id})
                    move_vals.update({'asset_id': self.id})
                    self.env['account.move'].create(move_vals)
                else:
                    raise UserError(_(f'There is no residual value for {rec.vendor_id.name} vendor'))
        else:
            raise UserError(_('Please Set Multi Vendor'))


class MultiVendorLine(models.Model):
    """
    Account Asset Multi Vendor
    """
    _name = 'account.asset.multi.vendor.line'
    _description = 'Account Asset Multi Vendor'

    asset_id = fields.Many2one(comodel_name="account.asset.asset")
    vendor_id = fields.Many2one(comodel_name="res.partner", string="Vendor")
    amount = fields.Float(string="Amount", required=False)

    @api.onchange('amount')
    def onchange_amount(self):
        """
        This method will execute when we are make changes inside the 'amount' field value
        """
        for rec in self:
            amount = sum(rec.asset_id.multi_vendor_ids.mapped('amount'))
            if amount > rec.asset_id.value_residual:
                raise UserError(_('Total value of amount is always less then residual amount'))


class AccountMove(models.Model):
    """
    Account Move Inherits
    """
    _inherit = 'account.move'

    asset_id = fields.Many2one(comodel_name="account.asset.asset")
