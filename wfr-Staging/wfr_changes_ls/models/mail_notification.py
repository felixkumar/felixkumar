from odoo import fields, models, api


class MailNotificationInherit(models.Model):
    _inherit = 'mail.notification'

    @api.model_create_multi
    def create(self, vals_list):
        """
        Inherits the create function to enable notifications for recipients in Odoo
        :param vals_list: Values for the creation of Mail Notification
        :return: the created records
        """
        for vals in vals_list:
            if vals.get('is_read'):
                vals['is_read'] = False
        res = super(MailNotificationInherit, self).create(vals_list)
        return res
