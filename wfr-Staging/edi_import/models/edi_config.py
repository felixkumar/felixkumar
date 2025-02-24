import logging

from odoo import models, fields
import traceback
from lxml import etree as ET

_logger = logging.getLogger(__name__)


class EdiErrorLog(models.Model):
    _name = 'edi.error.log'
    _description = 'EDI Error Log'

    error_id = fields.Char('Error ID')
    timestamp = fields.Datetime('Timestamp')
    error_code = fields.Char('Error Code')
    description = fields.Text('Description')
    edi_data = fields.Text(string="EDI Data")
    type = fields.Selection(selection=[
        ('error', 'Error'),
        ('unmapped_fields', 'Unmapped Fields')], string='Type')


class SyncDocumentType(models.Model):
    _inherit = 'sync.document.type'

    def _do_in(self, conn, sync_action_id, values):
        '''
        Performs the document synchronization for the new document code
        @param conn : sftp/ftp connection class.
        @param sync_action_id: recordset of type `edi.sync.action`
        @param values:dict of values that may be useful to various methods

        @return bool : return bool (True|False)
        '''
        with conn:
            conn.cd(sync_action_id.dir_path)
            files = conn.ls()
            if 'processed' not in files:
                conn.mkd('processed')
            if not files:
                _logger.warning('Directory on host is empty')
            for file in files:
                try:
                    if not file.endswith('.xml'):
                        continue
                    partner_element = sync_action_id.doc_type_id.xsd_id.xsd_line_ids.filtered('is_trading_partner_field')
                    file_data = conn.download_file(file)
                    xml_records = ET.fromstring(file_data)
                    partner_element_xpath = f'.//{partner_element.full_path.split("/")[-1]}'
                    trading_partnerid = xml_records.find(partner_element_xpath, xml_records.nsmap).text if partner_element.full_path else ''
                    partner = self.env['res.partner'].sudo().search([('trading_partnerid', '=', trading_partnerid)], limit=1)
                    mapping = sync_action_id._get_mapping(partner)
                    succeeded = self.env['edi.import'].sudo().create([{
                        'xml_doc': file_data,
                        'mapping_id': mapping.id,
                        'trading_partnerid': trading_partnerid,
                    }]).with_company(values.get('company_id')).action_import()
                    if succeeded:
                        conn.rename(file, 'processed/' + file)
                except Exception as error:
                    if traceback.format_exc():
                        self.env['edi.error.log'].sudo().create([{
                            'type':'error',
                            'error_id': mapping.sync_action_doc_type,
                            'timestamp': fields.Datetime.now(),
                            'description': traceback.format_exc(),
                        }])
                    _logger.error("************************************ {} {}".format(error, traceback.format_exc()))

        return True
