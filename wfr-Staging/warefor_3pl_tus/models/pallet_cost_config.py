# -*- coding: utf-8 -*-

from odoo import fields, models, _


class PalletCostConfig(models.Model):
    _name = 'pallet.cost.config'
    _description = 'Pallet Cost Configuration'
    _rec_name = 'reference'

    reference = fields.Char(string=_('Reference'))
    cost_for = fields.Selection(string=_("Costs For"), selection=[('vendor', 'Vendor'), ('country', 'Country')],
                                default='vendor')
    vendor_ids = fields.Many2many('res.partner', string=_("Vendors"))
    country_ids = fields.Many2many('res.country', string=_("Country"))
    packaging_qty = fields.Float(_('Packaging Quantity'), default=48.0,
                                 help=_("Pallet package should be W=3, D=4, H=4"))
    import_cost_ids = fields.One2many(comodel_name="pallet.import.cost", inverse_name="pallet_cost_config_id",
                                      string=_("Import Cost"))
    storage_cost_ids = fields.One2many(comodel_name="pallet.storage.cost", inverse_name="pallet_cost_config_id",
                                       string=_("Storage Fees"))
    vas_cost_ids = fields.One2many(comodel_name="pallet.vas.cost", inverse_name="pallet_cost_config_id",
                                   string=_("Value Added Service"))
    fob_cost_ids = fields.One2many(comodel_name="pallet.fob.cost", inverse_name="pallet_cost_config_id",
                                   string=_("Calculated against FOB"))
