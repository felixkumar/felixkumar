from odoo import _, models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def l10n_ke_action_open_products_view(self, product_ids):
        return {
            'name': _("Products"),
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'domain': [('id', 'in', product_ids)],
            'views': [
                (self.env.ref('l10n_ke_edi_oscu_pos.l10n_ke_pos_kra_product_tree').id, 'tree'),
            ],
            'context': {'create': False, 'delete': False},
            'target': 'new',
        }


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    l10n_ke_validation_message = fields.Char(compute='_compute_l10n_ke_validation_message')

    @api.depends('available_in_pos')
    def _compute_l10n_ke_validation_message(self):
        for product in self:
            product.l10n_ke_validation_message = ""
            if product.available_in_pos:
                if self.env.company.country_code != 'KE':
                    continue

                messages = {}

                for variant in product.product_variant_ids:
                    messages = {
                        **variant._l10n_ke_get_validation_messages(),
                        **variant.uom_id._l10n_ke_get_validation_messages(),
                    }

                for message in messages.values():
                    product.l10n_ke_validation_message += f"{message['message']}\n"
