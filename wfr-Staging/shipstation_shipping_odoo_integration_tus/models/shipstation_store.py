# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ShipstationStore(models.Model):
    _inherit = 'shipstation.store.vts'

    edi_store_id = fields.Many2one("edi.customer.store", string="EDI Store ID")
    is_locked_date = fields.Boolean("Is Locked From Date?")
    locked_from_date = fields.Datetime("Locked From Date")

    @api.onchange('last_modification_date')
    def _onchange_last_modification_date(self):
        for record in self:
            if record.locked_from_date and record.is_locked_date:
                if record.last_modification_date < record.locked_from_date:
                    raise ValidationError(_("From date is always greater than locked date"))
