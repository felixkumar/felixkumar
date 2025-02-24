# -*- coding: utf-8 -*-

from odoo import api, fields, models, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    customize_theme_has_started = fields.Boolean(default=False)
    previous_theme = fields.Text()

    # Main Odoo Menu
    main_odoo_menu_background_image = fields.Binary(string="Home Menu Background Image", attachment=True)

    # Main Navbar
    main_navbar_uni_color = fields.Char('Navbar Color', default='#714B67')
    main_navbar_has_gradient = fields.Boolean('Gradient', default=True,
                                              help='Check this box if you want a gradient color for your navbar')
    main_navbar_gradient_1 = fields.Char('Gradient Color 1', default='#714B67')
    main_navbar_gradient_2 = fields.Char('Gradient Color 2', default='#5e4a59')
    main_navbar_gradient_deg = fields.Integer('Gradient Degree', default=45)

    # Primary Colors
    btn_primary_text_color = fields.Char('Primary Text Color')
    btn_primary_bg_color = fields.Char('Primary Background Color')
    btn_primary_border_color = fields.Char('Primary Border Color')
    btn_primary_hover_text_color = fields.Char('Primary Text Hover')
    btn_primary_hover_bg_color = fields.Char('Primary Background Hover')
    btn_primary_hover_border_color = fields.Char('Primary Border Hover')

    # Secondary Colors
    btn_secondary_text_color = fields.Char('Secondary Text Color')
    btn_secondary_bg_color = fields.Char('Secondary Background Color')
    btn_secondary_border_color = fields.Char('Secondary Border Color')
    btn_secondary_hover_text_color = fields.Char('Secondary Text Hover')
    btn_secondary_hover_bg_color = fields.Char('Secondary Background Hover')
    btn_secondary_hover_border_color = fields.Char('Secondary Border Hover')

    is_enterprise = fields.Boolean(string='Odoo Enterprise', compute='_compute_is_enterprise')

    def _compute_is_enterprise(self):
        for company in self:
            web_enterprise_module = self.env.ref('base.module_web_enterprise', raise_if_not_found=False)
            company.is_enterprise = web_enterprise_module and web_enterprise_module.state == 'installed'

    @api.onchange('main_navbar_has_gradient')
    def _onchange_has_gradient(self):
        if self.main_navbar_has_gradient and not self.main_navbar_gradient_1 and not self.main_navbar_gradient_2:
            self.write({
                'main_navbar_gradient_1': '#714B67',
                'main_navbar_gradient_2': '#5e4a59',
                'main_navbar_gradient_deg': 45,
            })

    def reset_to_default(self):
        self.write({
            'customize_theme_has_started': True,
            'main_navbar_has_gradient': True,
            'main_navbar_gradient_1': '#714B67',
            'main_navbar_gradient_2': '#5e4a59',
            'main_navbar_gradient_deg': 45,
            'btn_primary_text_color': '#FFF',
            'btn_primary_bg_color': '#017e84',
            'btn_primary_border_color': '#017e84',
            'btn_secondary_text_color': '#FFF',
            'btn_secondary_bg_color': '#714B67',
            'btn_secondary_border_color': '#714B67',
            'btn_primary_hover_text_color': '#FFF',
            'btn_primary_hover_bg_color': '#016b70',
            'btn_primary_hover_border_color': '#01656a',
            'btn_secondary_hover_text_color': '#FFF',
            'btn_secondary_hover_bg_color': '#604058',
            'btn_secondary_hover_border_color': '#5a3c52',
            'main_odoo_menu_background_image': False
        })

    def apply_customizations(self):

        ir_ui_view = self.get_and_set_standard_view_noupdate()
        arch_db = ir_ui_view.arch_db

        key_start_text = '<body t-att-class="body_classname">'
        key_end_text = '<t t-out="0"/>'
        start_text = arch_db.split(key_start_text)[0] + key_start_text + '\n'
        end_text = key_end_text + arch_db.split(key_end_text)[1]

        if self.main_navbar_has_gradient:
            background = f'background: linear-gradient({str(self.main_navbar_gradient_deg)}deg, {self.main_navbar_gradient_1}, {self.main_navbar_gradient_2}) !important;'
        else:
            background = f'background: linear-gradient(45deg, {self.main_navbar_uni_color}, {self.main_navbar_uni_color}) !important;'

        if self.is_enterprise:
            if self.main_odoo_menu_background_image:
                url = f'/web/image?id={self.id}&amp;model=res.company&amp;field=main_odoo_menu_background_image'
            else:
                url = '/web_enterprise/static/img/home-menu-bg-overlay.svg'
            home_menu_background = f"background-image: url('{url}') !important;"
        else:
            home_menu_background = ''

        style_text = """<style>
        .o_home_menu_background, .o_web_client.o_home_menu_background {
            background-size: cover;
            background-attachment: fixed;
            """ + home_menu_background + """
        }
        .o_main_navbar {
            """ + background + """
        }
        .btn-fill-primary, .btn-primary:not(.btn-link) {
            color: """ + self.btn_primary_text_color + """ !important;
            background: """ + self.btn_primary_bg_color + """ !important;
            border-color: """ + self.btn_primary_border_color + """ !important;
        }
        .btn-fill-primary:hover, .btn-primary:hover:not(.btn-link) {
            color: """ + self.btn_primary_hover_text_color + """ !important;
            background-color: """ + self.btn_primary_hover_bg_color + """ !important;
            border-color: """ + self.btn_primary_hover_border_color + """ !important;
        }
        .o_field_statusbar > .o_statusbar_status > .o_arrow_button.o_arrow_button_current.disabled::after,
        .o_field_statusbar > .o_statusbar_status > .o_arrow_button.o_arrow_button_current.disabled::before {
            border-left-color: """ + self.btn_primary_bg_color + """ !important;
        }
        .btn-outline-primary {
            color: """ + self.btn_primary_bg_color + """ !important;
            border-color: """ + self.btn_primary_bg_color + """ !important;
        }
        .btn-outline-primary:hover {
            color: """ + self.btn_primary_text_color + """ !important;
            background-color: """ + self.btn_primary_bg_color + """ !important;
        }
        .btn-fill-odoo, .btn-odoo {
            color: """ + self.btn_secondary_text_color + """ !important;
            background-color: """ + self.btn_secondary_bg_color + """ !important;
            border-color: """ + self.btn_secondary_border_color + """ !important;
        }
        .btn-fill-odoo:hover, .btn-odoo:hover {
            color: """ + self.btn_secondary_hover_text_color + """ !important;
            background-color: """ + self.btn_secondary_hover_bg_color + """ !important;
            border-color: """ + self.btn_secondary_hover_border_color + """ !important;
        }
        .btn-secondary {
            color: """ + self.btn_secondary_bg_color + """ !important;
        }
        .btn-secondary:hover {
            color: """ + self.btn_secondary_bg_color + """ !important;
        }
        .o_field_statusbar > .o_statusbar_status > .o_arrow_button.o_arrow_button_current.disabled {
            color: """ + self.btn_primary_text_color + """ !important;
            background-color: """ + self.btn_primary_bg_color + """ !important;
        }
        .form-check-input:checked {
            border-color: """ + self.btn_primary_bg_color + """ !important;
            background-color: """ + self.btn_primary_bg_color + """ !important;
        }
        </style>
        """

        new_arch = start_text + style_text + end_text

        ir_ui_view.write({
            'arch_db': new_arch
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def get_and_set_standard_view_noupdate(self):
        ir_ui_view = self.env.ref('web.layout')
        model_data = self.env['ir.model.data'].sudo().search(
            [('model', '=', 'ir.ui.view'), ('module', '=', 'web'), ('res_id', '=', ir_ui_view.id)])
        model_data.noupdate = True

        return ir_ui_view
