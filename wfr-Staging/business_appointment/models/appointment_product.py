#coding: utf-8

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_round
from odoo.tools.safe_eval import safe_eval

DURATION_ERROR = _("The minimum duration should be less than the maxumum duration. Both should be positive")
DURATION_NEGATIVE_ERROR = _("The duration should be positive")
STEP_DURATION_NEGATIVE_ERROR = _("The step duration should be positive")
MULTIPLE_DURATION_ERROR = _("The multiple should be positive and less than the maximum")
ROUND_RULE_ERROR = _("The round rule should be positive")
ROUND_RULE_DAY_ERROR = _("The start time should be between 0:00 and 23:59")
CHECKOUT_TIME_ERROR = _("The checkout time should not be less than the duration and minimum duration")

def _round_for_multiplier(duration, multiple_duration, max=False):
    """
    The method to round for multiplier

    Args:
     * duration - float
     * multiple_duration - float

    Returns:
     * float
    """
    new_duration = duration
    residual = duration % multiple_duration
    if residual != 0:
        multiple_duration = not max and multiple_duration or 0
        new_duration = duration - residual + multiple_duration
    return new_duration


class appointment_product(models.Model):
    """
    Appointment Service
    """
    _name = "appointment.product"
    _inherit = ["mail.thread", "mail.activity.mixin", "resource.mixin", "image.mixin"]
    _description = "Service"

    @api.depends("appointment_ids.service_id", "appointment_ids.state")
    def _compute_appointment_len(self):
        """
        Compute method for appointment_len & planned_appointment_len
        """
        for service in self:
            service.appointment_len = len(service.appointment_ids)
            service.planned_appointment_len = len(service.appointment_ids.filtered(lambda ap: ap.state == "reserved"))

    @api.depends("rating_ids.rating", "rating_ids.parent_res_id")
    def _compute_rating_satisfaction(self):
        """
        Compute method for rating_satisfaction

        Methods:
         * _calculate_satisfaction_rate of rating.rating
        """
        for service in self:
            rate_final = -1
            if service.rating_ids:
                rate = self.env["rating.rating"]._calculate_satisfaction_rate(service)
                rate_final = rate[service.id]
            service.rating_satisfaction = rate_final

    @api.constrains(
        "manual_duration", "duration_uom", "min_manual_duration", "max_manual_duration", "min_manual_duration_days", 
        "max_manual_duration_days", "appointment_duration", "appointment_duration_days", "multiple_manual_duration",
        "multiple_manual_duration_days", "start_round_rule", "start_round_rule_days", "checkout_time","step_duration", 
        "step_duration_days",
    )
    def constrains_durations(self):
        """
        Constrain method for duration and start settings
        """
        for record in self:
            if record.duration_uom == "hours":
                if record.appointment_duration <= 0:
                    raise ValidationError(DURATION_NEGATIVE_ERROR)
                if record.step_duration <=0:
                    raise ValidationError(STEP_DURATION_NEGATIVE_ERROR)
                if record.appointment_duration <= record.checkout_time:
                    raise ValidationError(CHECKOUT_TIME_ERROR)
                if record.start_round_rule <= 0:
                    raise ValidationError(ROUND_RULE_ERROR)
                if record.manual_duration:
                    if record.min_manual_duration <= 0 or record.min_manual_duration > record.max_manual_duration:
                        raise ValidationError(DURATION_ERROR)
                    if record.multiple_manual_duration <= 0 \
                            or record.multiple_manual_duration > record.max_manual_duration:
                        raise ValidationError(MULTIPLE_DURATION_ERROR)
                    if record.checkout_time >= record.min_manual_duration:
                        raise ValidationError(CHECKOUT_TIME_ERROR)
            else:
                if record.appointment_duration_days <= 0:
                    raise ValidationError(DURATION_NEGATIVE_ERROR)
                if record.step_duration_days <=0:
                    raise ValidationError(STEP_DURATION_NEGATIVE_ERROR)
                if record.appointment_duration_days * 24 <= record.checkout_time:
                    raise ValidationError(CHECKOUT_TIME_ERROR)
                if record.start_round_rule_days < 0 or record.start_round_rule_days >= 24:
                    raise ValidationError(ROUND_RULE_DAY_ERROR)
                if record.manual_duration:
                    if record.min_manual_duration_days <= 0 \
                            or record.min_manual_duration_days > record.max_manual_duration_days:
                        raise ValidationError(DURATION_ERROR)
                    if record.multiple_manual_duration_days <= 0 \
                            or record.multiple_manual_duration_days > record.max_manual_duration_days:
                        raise ValidationError(MULTIPLE_DURATION_ERROR)
                    if record.checkout_time >= record.min_manual_duration_days * 24:
                        raise ValidationError(CHECKOUT_TIME_ERROR)

    name = fields.Char(string="Service Name", translate=True)
    product_id = fields.Many2one("product.product", string="Related Product", required=True)
    duration_uom = fields.Selection(
        [("hours", "hours"), ("days", "days"),],
        string="Duration UoM",
        default="hours",
        help="Define whether appointments should be scheduled for hours or for days. In the latter case, make sure\
working calendars allow 24-hour periods (should start at 00:00 and end at 24:00)"
    )
    appointment_duration = fields.Float(string="Appointment Default Duration", default=1.0)
    appointment_duration_days = fields.Integer(string="Duration of Appointment", default=1)
    appointment_ids = fields.One2many("business.appointment", "service_id", string="Appointments")
    ba_description = fields.Text(string="Appointment Description", translate=True, default="")
    step_duration = fields.Float(
        string="Slots Step (h.)",
        help="Based on that figure, the app will try to prepare all possible time slots. For example, 09:00-12:00;\
10:00-13:00; 11:00-14:00 for the service with the step 1 hour and actual duration 3 hours. Make the step equal to the\
duration to fit the whole day without intersections (09:00-12:00;12:00-15:00)",
        default=1.0,
    )
    step_duration_days = fields.Float(
        string="Slots Step (d.)",
        help="Based on that figure, the app will try to prepare all possible time slots. For example, 01.08-3.08;\
02.08-4.08; 03.08-04.08 for the service with the step 1 day and actual duration 3 days. Make the step equal the\
duration to avoid intersections (01.08-03.08;03.08-05.08)",
        default=1,
    )
    manual_duration = fields.Boolean(
        string="Allow Manual Duration",
        help="Allow users to define appointment duration. Otherwise, it will always equal the default duration",
    )
    min_manual_duration = fields.Float(string="Min Duration Hours", default=0.5)
    max_manual_duration = fields.Float(string="Max Duration Hours", default=2)
    multiple_manual_duration = fields.Float(
        string="Multiple for Hours",
        default=0.5,
        help="How the manual duration should be rounded. For example, 0:15 means rounding for 15 minutes: 0:17 > 0:30",
    )
    min_manual_duration_days = fields.Integer(string="Min Duration Days", default=1)
    max_manual_duration_days = fields.Integer(string="Max Duration Days", default=1)
    multiple_manual_duration_days = fields.Integer(
        string="Multiple for Days",
        default=1,
        help="How the manual duration should be rounded. For example, 2 means rounding for 2 days: 3 > 4",
    )    
    start_round_rule = fields.Float(
        string="Start Round",
        default=0.5,        
        help="""Define how the appointment start time should be rounded. For example, appointments are available now\
from 14:12 tomorrow. Then:
* 0:05 - rounding for 5 minutes - will round the start to 14:15
* 0:10 - rounding for 10 minutes - will round the start to 14:20
* 0:30 - rounding for 30 minutes - will round the start to 14:30
* 1:00 - rounding for an hour - will round the start to 15:00
* 02:00 - rounding for 2 hours - will round the start to 16:00
* 24:00 - rounding for a day - will round the start to 00:00
* 32:00 - rounding for a day and 8 hours - will round the start to 08:00 the next day
Take into account: ROUNDING IS DONE IN WORKING CALENDAR TIMEZONE""",
    )
    start_round_rule_days = fields.Float(
        string="Start Time",
        help="At which time daily services should start (defined in the working calendar time zone)"
    )
    extra_working_calendar_id = fields.Many2one(
        "resource.calendar",
        string="Extra Calendar Restriction",
        help="If defined, this service will be available only in the intervals that simultaneously suit this calendar\
and an appointment resource calendar",
    )
    extra_resource_ids = fields.One2many(
        "business.resource.extra",
        "service_id",
        string="Extra Resources Required",
        copy=True,
        help="Define the resources, that are required to provide this service. If defined, calendars of those\
resources will be taken into account to show available slots",
    )
    start_limit_rule_id = fields.Many2one(
        "appointment.day.limit",
        string="Start Day Restriction",
        help="Restrict possible reservation start times for specific days. For example, forbid appointments to start on\
Sundays. The rule regulates only start but it does not prohibit reservations on particular days. So, Saturday-Monda\
will be suitable while Sunday-Monday will not be suitable"
    )
    end_limit_rule_id = fields.Many2one(
        "appointment.day.limit",
        string="End Day Restriction",
        help="Restrict possible reservation end times for specific days. For example, forbid appointments to finish on\
Sundays. The rule regulates only end but it does not prohibit reservations on particular days. So, Saturday-Monday will\
be suitable while Saturday-Sunday will not be suitable"
    )
    checkout_time = fields.Float(
        string="Checkout Period (h.)",
        default=0,
        help="Define the time period that is required to fulfill the reservation without a customer (e.g. room\
cleaning). Then, the reservation time will include the whole period (e.g. 10:00 - 14:00), while the customer will be\
shown the period with substracted checkout time (e.g. 10:00 - 13:30 for a 30-minutes checkout)"
    )
    location = fields.Char(string="Location", translate=True)  
    color = fields.Integer(string="Color")
    suggested_product_ids = fields.Many2many(
        "product.product",
        "product_product_appointment_product_ba_rel_table",
        "product_product_id",
        "appointment_product_id",
        string="Complementary Products",
        check_company=True,
    )
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company, required=False)
    appointment_ids = fields.One2many("business.appointment", "service_id", string="Appointments")
    appointment_len = fields.Integer(string="Number of appointments", compute=_compute_appointment_len, store=True)
    planned_appointment_len = fields.Integer(
        string="Planned appointments",
        compute=_compute_appointment_len,
        store=True,
    )
    rating_ids = fields.One2many("rating.rating", "service_id", string="Ratings", auto_join=True)
    rating_satisfaction = fields.Integer(
        string="Average Rating",
        compute=_compute_rating_satisfaction,
        store=True, 
        default=-1,
    )
    active = fields.Boolean(string="Active", default=True)
    sequence = fields.Integer(string="Sequence")

    def _return_min_max_duration(self):
        """
        The method to return min, max and multiple duration

        Methods:
         * _round_for_multiplier

        Returns:
         * float, float, float

        Extra info:
         * Expected singleton
        """
        duration_uom = self.duration_uom
        multiple_duration = duration_uom == "hours" and self.multiple_manual_duration \
            or self.multiple_manual_duration_days
        min_duration = duration_uom == "hours" and self.min_manual_duration or self.min_manual_duration_days
        max_duration = duration_uom == "hours" and self.max_manual_duration or self.max_manual_duration_days
        return _round_for_multiplier(min_duration, multiple_duration),\
            _round_for_multiplier(max_duration,multiple_duration, True), multiple_duration

    def _return_available_choices(self):
        """
        The method to contruct all options for choices (if not too long)

        Methods:
         * _return_min_max_duration
         * _round_for_multiplier

        Returns:
         * list (of available option) or empty list

        Extra info:
         * Expected singleton
        """
        duration_choices = []
        min_duration, max_duration, multiple_duration = self._return_min_max_duration()
        itera = _round_for_multiplier(min_duration, multiple_duration)
        while itera <= _round_for_multiplier(max_duration, multiple_duration, True):
            duration_choices.append(itera)
            itera += multiple_duration
        return duration_choices

    def _get_suggested_products(self, from_website_id=False, appointment_id=False, pricelist_id=False):
        """
        The method to calculated offered to this service products

        Args:
         * from_website_id - int or False
         * appointment_id - int (in case of re-scheduling) or False
         * pricelist_id - int or False
        
        Methods:
         * action_calculate_price

        Returns:
         * list of dicts:
           ** id - int
           ** name - str
           ** qty - int 
           ** price - str
           ** image_small - binary
           
        Extra info:
         * Expected singleton
        """
        self = self.sudo()
        force_suggested = False
        if from_website_id:
            force_suggested = self.env["website"].browse(from_website_id).ba_extra_products_frontend
        else:
            ICPSudo = self.env["ir.config_parameter"].sudo()
            force_suggested = safe_eval(ICPSudo.get_param("ba_extra_products_backend", default="False"))
        suggested_products = []
        done_products = []
        if appointment_id:
            # if appointment is passed, we should show its already saved suggested products (even if no complementaries)
            appointment = self.env["business.appointment"].browse(appointment_id)
            if appointment.exists():
                for extra in appointment.extra_product_ids:
                    product = extra.product_id
                    suggested_products.append({
                        "id": product.id,
                        "name": product.name,
                        "qty": extra.product_uom_qty,
                        "price": self.action_calculate_price(product, pricelist_id, qty=extra.product_uom_qty),
                        "image_small": product.image_128,
                    })
                    done_products.append(product.id)
        if force_suggested and self.suggested_product_ids:
            for product in self.suggested_product_ids:
                if product.id not in done_products:
                    suggested_products.append({
                        "id": product.id,
                        "name": product.name,
                        "qty": 0,
                        "price": self.action_calculate_price(product, pricelist_id, qty=1),
                        "image_small": product.image_128,
                    })
        return suggested_products or False

    @api.model
    def action_calculate_price(self, product_id, pricelist_id=False, qty=1):
        """
        The method to calculate price for this product

        Args:
         * product_id - product.product object or int
         * pricelist_id
         * qty - int            

        Methods:
         * _get_product_price of product.product
         * precision_get of decimal.precision

        Returns:
         * str
        """
        res = ""
        lang = self._context.get("lang") or self.env.user.lang
        self = self.sudo()
        product = product_id
        if isinstance(product_id, int):
            product = self.env["product.product"].browse(product_id)
        if product.exists():
            pricelist = pricelist_id and self.env["product.pricelist"].browse(pricelist_id).exists() or False
            if not pricelist:
                pricelist = self.env.company.ba_pricelist_id
            if pricelist:
                price = pricelist._get_product_price(product, qty or 1.00)
                decimal_points = self.env["decimal.precision"].precision_get("Product Price")
                price = round(float_round(price, decimal_points), decimal_points)
                uom_name = product.uom_name
                currency = pricelist.currency_id
                symbol = currency.symbol
                res = currency.position == "after" and "{}{}".format(price, symbol) or u"{}{}".format(symbol, price)
                res = _(u"{} per {}".format(res, uom_name))
        return res

    def _get_all_extra_resource_titles(self):
        """
        The method to represent extra resources in the form of string 

        Methods:
         * _get_extra_resource_titles of business.resource.extra

        Returns:
         * Char

        Extra info:
         * Expected singleton
        """
        res = ""
        self = self.sudo()
        lang = self._context.get("lang") or self.env.user.lang
        self = self.with_context(lang=lang)
        if self.extra_resource_ids:   
            extra_line_titles = self.extra_resource_ids.mapped(lambda re: re._get_extra_resource_titles())
            if extra_line_titles:
                res = "".join(extra_line_titles)
            else:
                res = _("The service requires extra resources that are not possible to select!")
        return res        

