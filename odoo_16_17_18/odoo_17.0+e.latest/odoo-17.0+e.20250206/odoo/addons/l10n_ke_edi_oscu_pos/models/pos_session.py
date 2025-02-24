from odoo import models


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_product_product(self):
        """ This function add new fields on the product model in pos app. """
        result = super()._loader_params_product_product()
        result['search_params']['fields'].extend((
            'l10n_ke_item_code',
            'l10n_ke_packaging_unit_id',
            'l10n_ke_packaging_quantity',
            'l10n_ke_origin_country_id',
            'l10n_ke_product_type_code',
            'unspsc_code_id',
        ))
        return result
