
from odoo import api, models


class ThemeClarico(models.AbstractModel):
    _inherit = 'theme.utils'

    @api.model
    def _reset_default_config(self):

        self.disable_view('theme_clarico_vega.template_header_style_1')
        self.disable_view('theme_clarico_vega.template_header_style_2')
        self.disable_view('theme_clarico_vega.template_header_style_3')

        super(ThemeClarico, self)._reset_default_config()
