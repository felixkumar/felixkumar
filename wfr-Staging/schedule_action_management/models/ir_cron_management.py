from odoo import api, fields, models, _


class IrCronManagement(models.Model):
    _name = "ir.cron.management"
    _description = "Schedule Action Management"

    name = fields.Char("Name")
    code = fields.Char("Code")
    ir_cron_ids = fields.One2many("ir.cron.line", "ir_cron_mngt_id", "Schedule Actions")

    def _run_action(self):
        if self.ir_cron_ids:
            cron_id = self.ir_cron_ids.sorted('priority').filtered(lambda i: not i.is_processed)
            if cron_id:
                cron_id = cron_id[0]
                cron_id.ir_cron_id.method_direct_trigger()
                cron_id.ir_cron_id.is_processed = True
            if not cron_id:
                self.ir_cron_ids.write({'is_processed': False})
                cron_id = self.ir_cron_ids.filtered(lambda i: not i.is_processed)
                if cron_id:
                    cron_id = cron_id[0]
                    cron_id.ir_cron_id.method_direct_trigger()
                    cron_id.ir_cron_id.is_processed = True


class IrCronLine(models.Model):
    _name = "ir.cron.line"
    _description = "Schedule Action Line"
    _rec_name = "ir_cron_id"

    ir_cron_id = fields.Many2one("ir.cron", "Schedule Action", domain=[('active', 'in', [True, False])])
    priority = fields.Integer("Priority", related="ir_cron_id.priority", store=True, readonly=False)
    is_processed = fields.Boolean("Is Processed", related="ir_cron_id.is_processed", store=True, readonly=False)
    ir_cron_mngt_id = fields.Many2one("ir.cron.management", "Schedule Actions")
