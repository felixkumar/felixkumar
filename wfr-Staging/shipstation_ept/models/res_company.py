from odoo import models


class Respartner(models.Model):
    _inherit = 'res.partner'

    def _find_partner_ept(self, vals, key_list=[], extra_domain=[]):
        """
        This function find the partner based on domain.
        This function map the keys of the key_list with the dictionary and create domain and
        if you have given the extra_domain, then it will merge with _domain (i.e _domain = _domain + extra_domain).
        @requires: vals, key_list
        @param vals: i.e {'name': 'emipro', 'street': 'address', 'street2': 'address',
        'email': 'test@test.com'...}
        @param key_list: i.e ['name', 'street', 'street2', 'email',...]
        @param extra_domain: This domain for you can pass your own custom domain.
        i.e [('name', '!=', 'test')...]
        @return: partner object or False
        """
        if key_list and vals:
            _domain = [] + extra_domain
            for key in key_list:
                if not vals.get(key):
                    continue
                if (key in vals) and isinstance(vals.get(key), str):
                    _domain.append((key, '=ilike', vals.get(key)))
                else:
                    _domain.append((key, '=', vals.get(key)))
            partner = self.search(_domain, limit=1) if _domain else False
            return partner
        return False


class ResCompany(models.Model):
    """
    Inherit the res.company class for add new method
    """
    _inherit = "res.company"

    def get_weight_uom_id(self):
        """
        Get the weight UOM id
        """
        product_weight_in_lbs_param = self.env['ir.config_parameter'].sudo().get_param('product.weight_in_lbs')
        if product_weight_in_lbs_param == '1':
            return self.env.ref('uom.product_uom_lb', raise_if_not_found=False)
        else:
            return self.env.ref('uom.product_uom_kgm', raise_if_not_found=False)
