from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    import_edi_po = fields.Boolean(string='Inbound 850 PO',
                                   help='True if the contact receives inbound Sale Orders from the EDI.')

    def create_partner_so(self, val, xml_val=None, nsmap=None):
        if val is not None:
            if str(type(val)) == "<class 'lxml.etree._Element'>":
                val = val.text
            return self.create(
                {'name': val, 'trading_partnerid': val, 'company_id': self.env.company.id, 'outbound_edi_asn': True,
                 'send_edi_inv': True}).id
        return self
