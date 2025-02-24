# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import traceback
import ftplib

from odoo import api, fields, models, registry, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

class SyncDocumentType(models.Model):
    '''
    EDI Document list https://en.wikipedia.org/wiki/X12_Document_List
    We do not make X12 rather, we create XML and intermidiate service
    will convert those XML to X12 or any desire format.
    '''
    _name = 'sync.document.type'
    _description = 'EDI Sync Document Type'

    name = fields.Char('Name', required=True, translate=True, index=True, copy=False)
    active = fields.Boolean(string='Active', default=True)
    op_type = fields.Selection(selection=[
                                ('in', 'Import Documents'),
                                ('in-mv', 'Import Documents and Move files'),
                                ('out', 'Export Documents'),
                            ], string='Operation Type', required=True, copy=False)
    doc_code = fields.Selection(selection=[('none', 'No Document')], string='Document Code (EDI)', required=True, copy=False)

    xsd_id = fields.Many2one(comodel_name='xml.xsd', string='XSD')

    def _do_none(self, conn, sync_action_id, values):
        '''
        This is dummy demo method.
        @param conn : sftp/ftp connection class.
        @param sync_action_id: recordset of type `edi.sync.action`
        @param values:dict of values that may be useful to various methods

        @return bool : return bool (True|False)
        '''
        conn._connect()
        conn.ls()
        conn._disconnect()
        return True

    def configure_default_mapping(self):
        self.ensure_one()
        return self.xsd_id


class EDIConfig(models.Model):
    _name = 'edi.config'
    _description = 'EDI Configurations'
    _order = 'sequence, id'

    name = fields.Char('EDI Title', required=True, translate=True, index=True, copy=False)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(help='Determine the processing order', default=24)
    debug_logging = fields.Boolean('Debug logging', help='Log requests in order to ease debugging')
    company_id = fields.Many2one('res.company', string='Company',
                            default=lambda self: self.env.user.company_id.id, required=True)
    ftp_host = fields.Char(string='Host', required=True)
    ftp_port = fields.Integer(string='Port', required=True, default=22)
    ftp_protocol = fields.Selection(selection=[
                                ('ftp', 'FTP - File Transfer Protocol'),
                                ('sftp', 'SFTP - SSH File Transfer Protocol')
                            ], string='Protocol', required=True, default='ftp')
    ftp_login = fields.Char(string='Username', required=True)
    ftp_password = fields.Char(string='Password', required=True)
    sync_action_ids = fields.One2many(comodel_name='edi.sync.action',
                                inverse_name='config_id',
                                string='Synchronization Actions')
    note = fields.Html(string='Notes')
    message_count = fields.Integer(string='Messages from Sync Actions', compute='_compute_message_count')

    @api.depends('sync_action_ids.message_ids')
    def _compute_message_count(self):
        for config in self:
            config.message_count = len(config.sync_action_ids.message_ids)

    def debug_logging(self):
        for config in self:
            config.debug_logging = not config.debug_logging

    def _get_provider_config(self, config=None):
        if not config:
            config = {}
        config.update({
            'host': self.ftp_host,
            'port': self.ftp_port,
            'login': self.ftp_login,
            'password': self.ftp_password,
            'repin': '/',
        })
        return config

    def _get_provider_connection(self):
        config = self._get_provider_config()
        from importlib import import_module
        connector = import_module('odoo.addons.base_edi.models.%s' % ('%s_connection' % self.ftp_protocol))
        return getattr(connector, '%sConnection' % self.ftp_protocol.upper())(config=config)

    def test_provider_connection(self):
        files = []
        for server in self:
            ftp_connection = server._get_provider_connection()
            try:
                ftp_connection._connect()
            except ftplib.all_errors as ftpe:
                raise ValidationError('Connection Test Failed! Here is what we got instead:\n %s' % (ftpe))
            finally:
                ftp_connection._disconnect()
        raise UserError(_('Connection Test Succeeded! Everything seems properly set up!'))

    def do_document_sync(self):
        for config in self:
            config.sync_action_ids.do_doc_sync_user()
        return True

    def action_view_messages(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'model': 'edi.log.message',
            'view_mode': 'tree,form',
            'domain': [('action_id', 'in', self.sync_action_ids.ids)]
        }


class EDISyncAction(models.Model):
    _name = 'edi.sync.action'
    _description = 'EDI Synchronization Actions'
    _order = 'sequence, doc_type_id'
    _rec_name = 'doc_type_id'

    active = fields.Boolean(string='Active', default=True)
    sequence = fields.Integer(string='Sequence', help='Determine the action processing order', default=10)
    config_id = fields.Many2one(comodel_name='edi.config', string='EDI Configuration', ondelete='restrict', required=True, index=True, copy=False)
    doc_type_id = fields.Many2one(comodel_name='sync.document.type', string='Document Action', required=True, index=True, copy=False)
    op_type = fields.Selection(related='doc_type_id.op_type', string='Action Operation Type', store=True, readonly=True)
    xsd_id = fields.Many2one(comodel_name='xml.xsd', related='doc_type_id.xsd_id')
    dir_path = fields.Char(string='Directory Path', required=True, default='/',
                           help="Directory path on FTP host, used for importing or expoerting files. '/' is root path in ftp host and path should always start with same")
    dir_mv_path = fields.Char(string='Move Directory Path', default='/',
                              help="Directory path on FTP host, used for moving file to after importing files. '/' is root path in ftp host and path should always start with same.")
    last_sync_date = fields.Datetime(string='Last Synchronized On')
    action_defaults = fields.Text('Default Values', required=True, default='{}',
                                  help="A Python dictionary that will be evaluated to provide default values when creating new records for this alias. or can be used to pass defaults for exporting files")
    mapping_ids = fields.One2many(string='Mappings', comodel_name='edi.mapping', inverse_name='sync_action_id')
    message_ids = fields.One2many(string='Messages', comodel_name='edi.log.message', inverse_name='action_id')

    @api.constrains('action_defaults')
    def _check_action_defaults(self):
        for rec in self:
            try:
                dict(safe_eval(rec.action_defaults))
            except Exception:
                raise ValidationError(_('Invalid expression, it must be a literal python dictionary definition e.g. "{\'field\': \'value\'}"'))

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res._create_mappings()
        return res

    def write(self, vals):
        res = super().write(vals)
        self._create_mappings()
        return res

    def _create_mappings(self):
        for action in self:
            mapping = action._get_mapping()
            if (not mapping and action.op_type) or (mapping and mapping.xsd_id != action.xsd_id):
                # Don't actually delete the mappings in case this was a mistake
                action.mapping_ids.write({
                    'sync_action_id': False,
                })
                new_mappings = self.env['edi.mapping'].search([('sync_action_id', '=', False), ('xsd_id', '=', action.xsd_id.id)])
                if new_mappings and any(not new_mapping.partner_id for new_mapping in new_mappings):
                    new_mappings.write({
                        'sync_action_id': action.id
                    })
                else:
                    new_mapping = self.env['edi.mapping'].create({
                        'sync_action_id': action.id,
                        'xsd_id': action.xsd_id.id,
                    })
                    # new_mapping.configure()

    def do_doc_sync_user(self, use_new_cursor=False, company_id=False):
        self._do_doc_sync_cron(self, True)
        return True

    @api.model
    def _do_doc_sync_cron(self, sync_action_id=False, use_new_cursor=False, company_id=False, records=False):
        '''
        Call the document code method added by the modules.
        '''
        sync_action_todo = self
        if sync_action_id:
            if isinstance(sync_action_id, (list, tuple, int)):
                sync_action_todo |= self.browse(sync_action_id)
            elif isinstance(sync_action_id, models.BaseModel):
                sync_action_todo |= sync_action_id
            else:
                _logger.error('Invalid sync_action_id param  passed (hint: pass <list>, <tuple> or recordset of type <EDISyncAction|BaseModel>).')
        else:
            sync_action_todo = self.search(['|', ('last_sync_date', '<', fields.Datetime.now()), ('last_sync_date', '=', False)])
        for sync_action in sync_action_todo:
            try:
                if use_new_cursor:
                    cr = registry(self._cr.dbname).cursor()
                    self = self.with_env(self.env(cr=cr))
                values = {
                    'company_id': company_id or sync_action.config_id.company_id,
                    'records': records,
                }
                values.update(dict(safe_eval(sync_action.action_defaults)))
                doc_action = sync_action.op_type
                sync_method = '_do_%s' % doc_action
                conn = sync_action.config_id._get_provider_connection()
                if hasattr(sync_action.doc_type_id, sync_method) and conn:
                    _logger.info('running method `%s` for the synchronization action: %d.' % (sync_method, sync_action.id))
                    with self._cr.savepoint():
                        result = getattr(sync_action.doc_type_id, sync_method)(conn, sync_action, values)
                        if result:
                            sync_action.last_sync_date = fields.Datetime.now()
                    if use_new_cursor:
                        cr.commit()
                else:
                    _logger.warning('The method `%s` does not exist on synchronization action: %d.' % (sync_method, sync_action.id))
            except Exception:
                if use_new_cursor:
                    cr.rollback()
                traceback_message = traceback.format_exc()
                _logger.error(traceback_message)
            finally:
                if use_new_cursor:
                    try:
                        self._cr.close()
                    except Exception:
                        pass
        return True

    def _get_mapping(self, partner=None):
        self.ensure_one()
        default_mapping = self.mapping_ids.filtered_domain([('partner_id', '=', False)])
        if partner:
            return self.mapping_ids.filtered_domain([('partner_id', '=', partner.id)]) or default_mapping
        return default_mapping
