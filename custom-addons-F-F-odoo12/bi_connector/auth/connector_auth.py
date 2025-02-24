from odoo import SUPERUSER_ID, exceptions, http, models, tools
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _auth_method_connector_bi(cls):
        httprequest = request.httprequest
        httprequest.session.db = 'slm'
        icp_sudo = request.env['ir.config_parameter'].sudo()
        connector_enable = icp_sudo.get_param('bi_connector.xetechs_bi_connector_enable')
        uuid = icp_sudo.get_param('bi_connector.xetechs_bi_uuid')
        secret = icp_sudo.get_param('bi_connector.xetechs_bi_secret')
        auth_header_source_id = request.httprequest.headers.get('SourceID')
        auth_header_secret = request.httprequest.headers.get('Secret')
        if connector_enable and auth_header_source_id and auth_header_secret and \
                tools.consteq(auth_header_source_id, uuid) and tools.consteq(auth_header_secret, secret):
            if not request.session.uid:
                request.uid = SUPERUSER_ID
            # Valid user session exists, decide what to do here.
            else:
                request.uid = request.session.uid
        else:
            raise exceptions.AccessDenied()
