from odoo import models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"

    is_walmart_customer = fields.Boolean(string="Walmart Customer", default=False)
    walmart_instance_id = fields.Many2one(comodel_name="walmart.marketplace.ept",
                                          string="Walmart Instance id")

    def walmart_prepare_partner_vals(self, vals):
        """
        This method used to prepare a partner vals.
        @param : self,vals
        @return: partner_vals
        @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 29 August 2020 .
        Task_id: 165956
        """
        partner_obj = self.env["res.partner"]
        name = vals.get('name')

        zipcode = vals.get("postalCode")
        state_code = vals.get("state")

        country_code = vals.get("country")
        country = partner_obj.get_country(country_code)

        state = partner_obj.create_or_update_state_ept(country_code, state_code, zipcode, country)

        partner_vals = {
            "email": vals.get("email") or False,
            "name": name,
            "phone": vals.get("phone"),
            "street": vals.get("address1"),
            "street2": vals.get("address2"),
            "city": vals.get("city"),
            "zip": zipcode,
            "state_id": state and state.id or False,
            "country_id": country and country.id or False,
            "is_company": False
        }
        return partner_vals
