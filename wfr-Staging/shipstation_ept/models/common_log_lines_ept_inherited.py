import logging
from odoo import models, fields
_logger = logging.getLogger(__name__)


class CommonLogLinesEpt(models.Model):
    """
    Inherit common.log.lines.ept for create shipstation log
    """
    _inherit = "common.log.lines.ept"

    module = fields.Selection(selection_add=[("shipstation_ept", "Shipstation")],
                              ondelete={'shipstation_ept': 'cascade'})
