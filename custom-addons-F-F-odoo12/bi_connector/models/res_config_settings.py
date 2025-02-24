# -*- coding: utf-8 -*-

from odoo import api, models, fields


class XetechsBISettings(models.TransientModel):
    _inherit = 'res.config.settings'

    xetechs_bi_connector_enable = fields.Boolean(string="Enable Xetechs BI Connector", default=False)
    xetechs_bi_uuid = fields.Char(string="Source ID")
    xetechs_bi_secret = fields.Char(string="Secret")

    @api.model
    def set_values(self):
        res = super(XetechsBISettings, self).set_values()
        self.env['ir.config_parameter'].set_param('bi_connector.xetechs_bi_connector_enable',
                                                  self.xetechs_bi_connector_enable)
        self.env['ir.config_parameter'].set_param('bi_connector.xetechs_bi_uuid', self.xetechs_bi_uuid.strip())
        self.env['ir.config_parameter'].set_param('bi_connector.xetechs_bi_secret', self.xetechs_bi_secret.strip())
        return res

    @api.model
    def get_values(self):
        res = super(XetechsBISettings, self).get_values()
        icp_sudo = self.env['ir.config_parameter'].sudo()
        connector_enable = icp_sudo.get_param('bi_connector.xetechs_bi_connector_enable')
        uuid = icp_sudo.get_param('bi_connector.xetechs_bi_uuid')
        secret = icp_sudo.get_param('bi_connector.xetechs_bi_secret')
        res.update(
            xetechs_bi_connector_enable=connector_enable,
            xetechs_bi_uuid=uuid,
            xetechs_bi_secret=secret,
        )
        return res

