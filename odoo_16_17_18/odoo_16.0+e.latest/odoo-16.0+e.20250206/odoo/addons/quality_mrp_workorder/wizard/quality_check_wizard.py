# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class QualityCheckWizard(models.TransientModel):
    _inherit = 'quality.check.wizard'

    def confirm_measure(self):
        if self.current_check_id.workorder_id:
            self.current_check_id.workorder_id._change_quality_check(position='next')
        return super().confirm_measure()
