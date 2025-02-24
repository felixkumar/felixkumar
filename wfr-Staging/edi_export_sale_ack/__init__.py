from . import models


def _create_order_ack_export_xsd(cr, registry):
    from base64 import b64encode
    from os.path import join as join_path
    from odoo import api, SUPERUSER_ID
    from odoo.modules import get_module_path

    env = api.Environment(cr, SUPERUSER_ID, {})
    module_path = get_module_path('edi_export_sale_ack')
    # using rb rather than r because then the read() method returns a bytes-like object that b64encode expects
    with open(join_path(module_path, 'data/OrderAcks_855.xsd'), 'rb') as xsd_file:
        contents = xsd_file.read()
        action = env['xml.xsd.import'].create({
            'name': '855 Export Sale Order Acknowledgement',
            'file': b64encode(contents),
        }).action_create_xsd()
        xsd = env['xml.xsd'].browse(action['res_id'])
        env.ref('edi_export_sale_ack.sync_document_export_order_ack').xsd_id = xsd
