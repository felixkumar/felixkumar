from . import models


def _create_sale_import_xsd(cr, registry):
    from base64 import b64encode
    from os.path import join as join_path
    from odoo import api, SUPERUSER_ID
    from odoo.modules import get_module_path

    env = api.Environment(cr, SUPERUSER_ID, {})
    module_path = get_module_path('edi_import_sale')
    # using rb rather than r because then the read() method returns a bytes-like object that b64encode expects
    with open(join_path(module_path, 'data/Orders_850.xsd'), 'rb') as xsd_file:
        contents = xsd_file.read()
        action = env['xml.xsd.import'].create({
            'name': '850 Import Sale Order',
            'file': b64encode(contents),
        }).action_create_xsd()
        xsd = env['xml.xsd'].browse(action['res_id'])

        trading_partner_id_line = xsd.xsd_line_ids.filtered(lambda x: x.path == 'TradingPartnerId')
        if trading_partner_id_line:
            trading_partner_id_line.is_trading_partner_field = True

        env.ref('edi_import_sale.sync_document_import_sale').xsd_id = xsd
