import logging
import os

from odoo import fields, models, _

from lxml import etree as ET


_logger = logging.getLogger(__name__)

class SyncDocumentAction(models.Model):
    _inherit = 'sync.document.type'

    def _do_out(self, conn, sync_action_id, values):
        with conn:
            conn.cd(sync_action_id.dir_path)
            for record in values.get('records') or sync_action_id._get_documents_to_export():
                partner = record._get_edi_partner()
                mapping = sync_action_id._get_mapping(partner)
                data = self.env['edi.export.wizard'].create({'mapping_id': mapping.id}).action_do_export(record)
                data_for_att = data
                filename = '%s_%s.xml' % (sync_action_id._get_export_name(), record.get_edi_name())

                if record._name == 'stock.picking' and getattr(record, 'edi_backorder_origin'):
                    sale_id = getattr(record, 'sale_id')
                    if sale_id and hasattr(sale_id, 'freight_id'):
                        freight_id = getattr(sale_id, 'freight_id')
                        if freight_id:
                            att_id = self.env['ir.attachment'].create(
                                {'name': filename, 'raw': data_for_att or "",
                                 'mimetype': 'application/xml', 'res_model': 'freight.freight', 'res_id': freight_id.id,
                                 'res_name': filename})

                with open(filename, 'wb+') as file:
                    file.write(data)

                filename = filename.strip()
                try:
                    with open(filename, 'rb') as file:
                        conn.upload_file(filename, file)
                    record.write({'edi_status': 'sent', 'edi_date': fields.Datetime.now()})
                    record.sudo().message_post(body=_('Document file created on the EDI server %s' % filename))
                    _logger.info(
                        'Document file created on the server path of %s/%s' % (sync_action_id.dir_path, filename))
                except Exception as e:
                    record.write({'edi_status': 'fail'})
                    _logger.error('file not uploaded %s' % e)
                os.remove(filename)
        return True


class EdiSyncAction(models.Model):
    _inherit = 'edi.sync.action'

    def _get_documents_to_export(self):
        self.ensure_one()
        return []

    def _get_export_name(self):
        self.ensure_one()
        return self.op_type
