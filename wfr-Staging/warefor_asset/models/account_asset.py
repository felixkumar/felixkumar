# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountAssetCategory(models.Model):
    """Added custom fields in asset model"""
    _inherit = 'account.asset.asset'

    def _internal_user_partner(self):
        """

        :return:
        """
        partner = self.env['res.partner'].search([])
        partner_ids = partner.filtered(lambda p: p.user_ids)
        domain = [('id', 'in', partner_ids.ids)]
        return domain

    asset_tag = fields.Char(string="Asset Tag")
    assigned_to = fields.Many2one(comodel_name="res.partner", string="Assigned To", domain=_internal_user_partner)
    serial_number = fields.Char(string="Serial Number")
    location_id = fields.Many2one(comodel_name="stock.location", string="Location")
    leased_owned = fields.Selection(string="Leased/Owned", selection=[('leased', 'Leased'), ('owned', 'Owned')],
                                    default='owned')
    date = fields.Date(string='Date', required=True, readonly=False, default=fields.Date.context_today)
    active = fields.Boolean(default=True, help="Set active to false to hide the Account Tag without removing it.")
    rental_agreement = fields.Char(string="Rental Agreement")
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", tracking=True)


class AccountAssetDepreciationLine(models.Model):
    _inherit = 'account.asset.depreciation.line'

    def _prepare_move(self, line):
        res = super(AccountAssetDepreciationLine, self)._prepare_move(line)
        res['warehouse_id'] = line.asset_id.warehouse_id.id
        return res