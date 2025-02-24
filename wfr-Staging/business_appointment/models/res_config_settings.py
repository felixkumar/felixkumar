# -*- coding: utf-8 -*-

from odoo import api, fields, models


class res_config_settings(models.TransientModel):
    """
    The model to keep settings of business appointments
    """
    _inherit = "res.config.settings"

    @api.onchange("module_business_appointment_website")
    def _onchange_module_business_appointment_website(self):
        """
        Onchange method for module_business_appointment_website
        """
        for conf in self:
            if not conf.module_business_appointment_website:
                conf.ba_approval_type = "no"
                conf.module_business_appointment_custom_fields_website = False
                conf.module_business_appointment_website_sale = False

    @api.onchange("module_business_appointment_sale")
    def _onchange_module_business_appointment_sale(self):
        """
        Onchange method for module_business_appointment_sale
        """
        for conf in self:
            if conf.module_business_appointment_sale:
                conf.group_uom = True
            else:
                conf.ba_auto_sale_order = "no"
                conf.module_business_appointment_website_sale = False

    @api.onchange("module_business_appointment_custom_fields")
    def _onchange_module_business_appointment_custom_fields(self):
        """
        Onchange method for module_business_appointment_website
        """
        for conf in self:
            if not conf.module_business_appointment_custom_fields:
                conf.module_business_appointment_custom_fields_website = False

    @api.onchange("ba_multi_scheduling")
    def _onchange_ba_multi_scheduling(self):
        """
        Onchange method for ba_multi_scheduling
        """
        for conf in self:
            if not conf.ba_multi_scheduling:
                conf.ba_max_multi_scheduling = 1

    module_business_appointment_website = fields.Boolean(string="Appointments in Portal and Website")
    module_business_appointment_custom_fields = fields.Boolean(string="Custom Fields")
    module_business_appointment_custom_fields_website = fields.Boolean("Portal and Website Custom Fields")
    module_business_appointment_sale = fields.Boolean("Link Appointments to Sale Orders")
    module_business_appointment_website_sale = fields.Boolean("Website Sales")    
    module_business_appointment_hr = fields.Boolean(string="Employees as Resources")
    module_business_appointment_time_tracking = fields.Boolean(string="Time Tracking")
    module_business_appointment_gantt = fields.Boolean(string="Gantt View")
    group_business_appointment_rating = fields.Boolean(
        "Use Rating for Appointments", 
        implied_group="business_appointment.group_business_appointment_rating",
    )
    group_business_appointment_video_calls = fields.Boolean(
        "Integrate Odoo Video Calls", 
        implied_group="business_appointment.group_business_appointment_video_calls",
        group="base.group_portal,base.group_user,base.group_public",
    )
    ba_multi_scheduling = fields.Boolean(
        string="Multi Scheduling",
        config_parameter="ba_multi_scheduling",
    )
    ba_max_multi_scheduling = fields.Integer(
        string="Maximum Appointments (Backend)",
        config_parameter="ba_max_multi_scheduling",
        help="This setting is applied only to the backend. For portal and website maximum number, please look at\
website-specific options",
        default=1,
    )
    ba_approval_type = fields.Selection(
        [("no", "No Confirmation"), ("email", "Email Confirmation"), ("sms", "SMS Confirmation"),],
        string="Website / Portal Confirmation",
        config_parameter="ba_approval_type",
        help="If the SMS confirmation is chosen but not available, then email confirmation will be used",
    )
    ba_max_approval_time = fields.Float(
        string="Maximum Period for Confirmation (h.)",
        config_parameter="ba_max_approval_time",
        help="After this period, not confirmed appointments will be canceled",
        default=2.0,
    )
    ba_max_approval_trials = fields.Integer(
        string="Maximum Number of Attempts to Confirm",
        config_parameter="ba_max_approval_trials",
        help="After exceeding this number, all steps will be canceled and should be started from scratch",
        default=5,
    )
    ba_confirmation_retry_period = fields.Integer(
        string="New Confirmation Code Minimum Period (s.)",
        config_parameter="ba_confirmation_retry_period",
        help="After this period, it will be possible to resend the confirmation code",
        default=60,
    )
    ba_confirmation_retry_trials = fields.Integer(
        string="Maximum Number of Code Refreshing",
        config_parameter="ba_confirmation_retry_trials",
        help="After exceeding, the button 'Resend Code' will be not anymore shown",
        default=3,
    )
    ba_max_preresevation_time = fields.Float(
        string="Maximum Period for Prereservation",
        config_parameter="ba_max_preresevation_time",
        default="0.5",
    )
    ba_auto_sale_order = fields.Selection(
        [
            ("no", "No Auto Creation"),
            ("draft", "Auto Draft Sale Order"),
            ("sent", "Sent Quotation (ready to accept and pay)"),
            ("confirmed", "Auto Confirmed Sale Order"),
        ],
        string="Auto Sale Order",
        config_parameter="ba_auto_sale_order",
        help="Define whether a sale order should be auto-created/confirmed when an appointment is confirmed",
    )
    ba_extra_products_backend = fields.Boolean(
        "Offer Complementary Products",
        config_parameter="ba_extra_products_backend",
    )
    ba_sale_appointment_description = fields.Boolean(
        "Appointment reference in sales",
        config_parameter="ba_sale_appointment_description",
    )
    ba_required_phone_validation = fields.Boolean(
        "Required phone validation",
         config_parameter="ba_required_phone_validation",
    )
    # Company-specific settings
    ba_company_id = fields.Many2one(
        "res.company",
        string="Company (Universal Appointments)",
        default=lambda self: self.env.company,
        required=True,
    )
    ba_pricelist_id = fields.Many2one(related="ba_company_id.ba_pricelist_id", readonly=False)
    ba_timezone_option = fields.Boolean(related="ba_company_id.ba_timezone_option", readonly=False) 
    appoin_comp_tz = fields.Selection(related="ba_company_id.partner_id.tz", readonly=False)

