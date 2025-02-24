import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

class EdiLogMessage(models.Model):
    _name = 'edi.log.message'
    _description = 'EDI Log Message'

    action_id = fields.Many2one(string='Action', comodel_name='edi.sync.action')
    type = fields.Selection(string='Log Type', selection=[('info', 'Info'), ('warning', 'Warning'), ('error', 'Error')], required=True)
    message = fields.Char(string='Message', required=True)

    @api.model
    def log(self, action, type, message):
        log_message = '%s (%s) %s: %s' % (action.config_id.name, action.doc_type_id.name, type, message)
        if type == 'info':
            _logger.info(log_message)
        elif type == 'warning':
            _logger.warning(log_message)
        elif type == 'error':
            _logger.error(log_message)
        else:
            _logger.warning('log type %s not found', type)
            return None
        return self.create([{
            'action_id': action.id,
            'type': type,
            'message': message
        }])
