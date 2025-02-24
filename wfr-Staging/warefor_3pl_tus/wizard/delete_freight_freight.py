# -*- coding: utf-8 -*-

import calendar
from odoo import models, fields, api, _


class Freight2StepDelete(models.TransientModel):
    _name = 'freight.2step.delete'
    _description = 'Delete Freight With 2Step '

    freight_id = fields.Many2one("freight.freight")

    def not_delete_record(self):
        self.freight_id.is_deleted = True
        is_outbound = self.freight_id.is_outbound
        temp_id = self.env['freight.freight'].search(
            [('id', '>', self.freight_id.id), ('is_outbound', '=', is_outbound)], limit=1)

        if temp_id and not is_outbound:
            action = self.env["ir.actions.act_window"]._for_xml_id("warefor_3pl_tus.menu_freight_freights_ibl_action")
            action["res_id"] = temp_id.id
            action["views"] = [(False, "form")]
            return action
        elif temp_id and is_outbound:
            action = self.env["ir.actions.act_window"]._for_xml_id("warefor_3pl_tus.menu_freight_freights_outbound_action")
            action["views"] = [(False, "form")]
            action["res_id"] = temp_id.id
            return action
        elif not is_outbound:
            return self.env["ir.actions.act_window"]._for_xml_id("warefor_3pl_tus.menu_freight_freights_ibl_action")
        else:
            return self.env["ir.actions.act_window"]._for_xml_id("warefor_3pl_tus.menu_freight_freights_outbound_action")

    def delete_record(self):
        if self.freight_id and not self._context.get('deletion_approved'):
            name = _('Re-Confirm')
            view = self.env.ref('warefor_3pl_tus.freight_2step_delete_view_form')
            return {
                'name': name,
                'type': 'ir.actions.act_window',
                'res_model': 'freight.2step.delete',
                'views': [(view.id, 'form')],
                'view_mode': 'form',
                'view_id': view.id,
                'target': 'new',
                'context': {'default_freight_id': self.freight_id.id, 'deletion_approved': True}
            }
        is_outbound = self.freight_id.is_outbound
        temp_id = self.env['freight.freight'].search(
            [('id', '>', self.freight_id.id), ('is_outbound', '=', is_outbound)], limit=1)
        self.freight_id.unlink()
        if temp_id and not is_outbound:
            action = self.env["ir.actions.act_window"]._for_xml_id("warefor_3pl_tus.menu_freight_freights_ibl_action")
            action["res_id"] = temp_id.id
            action["views"] = [(False, "form")]
            return action
        elif temp_id and is_outbound:
            action = self.env["ir.actions.act_window"]._for_xml_id("warefor_3pl_tus.menu_freight_freights_outbound_action")
            action["views"] = [(False, "form")]
            action["res_id"] = temp_id.id
            return action
        elif not is_outbound:
            return self.env["ir.actions.act_window"]._for_xml_id("warefor_3pl_tus.menu_freight_freights_ibl_action")
        else:
            return self.env["ir.actions.act_window"]._for_xml_id("warefor_3pl_tus.menu_freight_freights_outbound_action")

