# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CompanyExtend(models.Model):
    _inherit = "res.company"

    # def _default_mail_template(self):
    #     try:
    #         return self.env.ref('warefor_3pl_tus.mail_template_pallet_batch_done').id
    #     except ValueError:
    #         return False

    pallet_batch_email_validation = fields.Boolean("Email Confirmation Pallet Batch", default=False)
    pallet_batch_user_id = fields.Many2one('res.users', string="Email user",
                                           help="Email sent to the selected user once the pallet batch is done.")
    is_logistics = fields.Boolean(string="Is Logistics Company?")
    company_code = fields.Char(string="Company Code")
    pallet_in_location = fields.Integer(string="Pallets in Rack", help="How many pallet should store in rack?",
                                        default=2)
    rack_in_location = fields.Integer(string="Rack in Location", help="How many rack should store in location?",
                                      default=1)
    gs1_prefix = fields.Char(string="GS1 Prefix")
    gs1_company_prefix = fields.Char(string="GS1 Company Prefix")
    is_oxford = fields.Boolean(string="Is eCommerce?")
    use_virtual_location = fields.Boolean(string="Use Virtual Location?")

    def write(self, values):
        if 'rack_in_location' in values.keys() and values.get('rack_in_location') != self.rack_in_location:
            location_ids = self.env["stock.location"].search(
                [('building', '!=', False), ('is_rack', '!=', True),('company_id', 'in', self.ids)])
            rack_in_location = values.get('rack_in_location')
            stored_location = location_ids.filtered(lambda l: l.stored_rack and l.stored_rack < self.rack_in_location)
            if stored_location:
                raise ValidationError(
                    _("First need to move the stored racks from the locations:{}".format(
                        stored_location.mapped("name"))))
            _logger.info("Creating rack locations in floor locations: FL {}".format(location_ids.ids))
            created_location = []
            for location in location_ids:
                stored_rack = len(location.rack_ids)
                create_location = rack_in_location - stored_rack
                for location_number in range(1, create_location + 1):
                    location_value = {
                        "building": "",
                        "sub_inventory": "",
                        "aisle_location": "",
                        "level_configuration": "",
                        "pallet_positions_area": "",
                        "location_id": location.id,
                        "is_rack": True,
                        "name": "RACK-{}-{}".format(location.name, location_number)
                    }
                    rack_location_id = location.copy(default=location_value)
                    created_location.append(rack_location_id.id)
            _logger.info("Rack locations are created in floor locations: RL{}".format(created_location))
        res = super(CompanyExtend, self).write(values)
        return res
