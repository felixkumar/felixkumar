from odoo import models, fields, api


class DeliveryRate(models.Model):
    _inherit = 'delivery.rate.ept'

    def set_service(self):
        """
        This method set the service selected from delivery rate lines into the picking.
        @return: If package of picking and selected service's package both are not equal then
        shipstation.package_id is updated else existing flow will work
        """
        return super(DeliveryRate, self.sudo()).set_service()
