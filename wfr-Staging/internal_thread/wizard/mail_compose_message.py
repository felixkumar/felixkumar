# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class mail_compose_message(models.TransientModel):
    """
    Overwrite to pass param send only internally
    """
    _inherit = "mail.compose.message"

    def _inverse_send_only_internal(self):
        """
        Inverse method for send_only_internal to put our subtype
        """
        for wiz in self:
            if wiz.send_only_internal:
                try:
                    wiz.subtype_id = self.env.ref("internal_thread.mt_internal_mes")
                except:
                    _logger.error("Message subtype 'Private Messages' is not found")

    @api.onchange("send_only_internal")
    def _onchange_send_only_internal(self):
        """
        Onchange method for send_only_internal
        """
        for wiz in self:
            if wiz.send_only_internal:
                if wiz.model and wiz.res_id:
                    document = self.env[wiz.model].browse(wiz.res_id)
                    wiz.partner_ids = wiz.partner_ids + document.message_partner_ids

    def onchange_template_id(self, template_id, composition_mode, model, res_id):
        """
        Re-write to make sure followers are applied
        """
        values = super(mail_compose_message, self).onchange_template_id(
            template_id=template_id,
            composition_mode=composition_mode,
            model=model,
            res_id=res_id,
        )
        value = values.get("value")
        if self.send_only_internal and self.model and self.res_id:
            partner_ids = self.env[self.model].browse(self.res_id).message_partner_ids.ids
            if value.get("partner_ids"):
                try:
                    partner_ids = partner_ids + value.get("partner_ids")[0][2]
                except:
                    partner_ids = partner_ids + value.get("partner_ids")
            value.update({"partner_ids": [(6, 0, partner_ids)]})
        return {"value": value}

    send_only_internal = fields.Boolean(
        string="Send private",
        inverse=_inverse_send_only_internal,
        help="The message will be sent only to the recipients below. It will not be sent for other documents followers",
    )
