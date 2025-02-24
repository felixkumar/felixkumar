#coding: utf-8

import itertools

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pytz import all_timezones, timezone

from odoo import _, api, fields, models

from odoo.addons.base.models.res_partner import _tzs
from odoo.addons.resource.models.resource import datetime_to_string, Intervals, string_to_datetime
from odoo.exceptions import ValidationError
from odoo.osv.expression import OR
from odoo.tools.safe_eval import safe_eval

UTCTZ = timezone("UTC")
MAXINTERVALS_NOTTOSPLITBYMONTHS = 14

def get_possible_timezones_by_offset(tz_offset):
    """
    The method to retrieve a possible timezone by its offset (we return the first found)

    Args:
     * tz_offset - int (offset in minutes)

    Returns:
     * char
    """
    offset_days, offset_seconds = 0, int(tz_offset * 60)
    if offset_seconds < 0:
        offset_days = -1
        offset_seconds += 24 * 60
    desired_delta = timedelta(offset_days, offset_seconds)
    null_delta = timedelta(0, 0)
    result = "UTC"
    for tz_name in all_timezones:
        tz = timezone(tz_name)
        non_dst_offset = getattr(tz, "_transition_info", [[null_delta]])[-1]
        if desired_delta == non_dst_offset[0]:
            result = tz_name
            break
    return result

def localize_day_to_resource_datetime(dt, tz):
    """
    The method to calculate day based on given tz

    Args:
     * dt - naive datetime (expressed as UTC)
     * tz - pytz.timezone object
    """
    dt = fields.Datetime.from_string(dt)
    return tz.localize(dt)


class business_resource(models.Model):
    """
    The model to keep settings of who / what should be occupied. E.g. a doctor, a room, etc.
    """
    _name = "business.resource"
    _inherit = ["mail.thread", "mail.activity.mixin", "resource.mixin", "image.mixin"]
    _description = "Business Resource"

    @api.depends(
        "main_resource_id", "main_resource_id.user_id", "main_resource_id.resource_calendar_id", "user_id", 
        "resource_calendar_id",
    )
    def _compute_info_resource_id(self):
        """
        Compute method for info_resource_id
        """
        for resource in self:
            info_resource_id = resource.main_resource_id or resource
            resource.info_resource_id = info_resource_id
            resource.info_info_user_id = info_resource_id.user_id
            resource.info_resource_calendar_id = info_resource_id.resource_calendar_id

    @api.depends("resource_type_id.service_ids")
    def _compute_type_available_service_ids(self):
        """
        Compute method for type_available_service_ids
        """
        for resource in self:
            service_ids = resource.resource_type_id.service_ids.ids
            resource.type_available_service_ids = [(6, 0, service_ids)]

    @api.depends("resource_type_id.service_method", "service_ids", "resource_type_id.always_service_id")
    def _compute_final_service_ids(self):
        """
        Compute method for final_service_ids
        """
        for resource in self:
            if resource.service_method == "single":
                resource.final_service_ids = [(6, 0, [resource.resource_type_id.always_service_id.id])]
            elif resource.service_method == "multiple":
                resource.final_service_ids = [(6, 0, resource.service_ids.ids)]

    @api.depends(
        "appointment_ids.resource_id", "appointment_ids.state", "extra_appointment_ids.resource_id",
        "extra_appointment_ids.state"
    )
    def _compute_appointment_len(self):
        """
        Compute method for appointment_len & planned_appointment_len
        """
        for resource in self:
            all_appointment_ids = resource.appointment_ids + resource.extra_appointment_ids
            resource.appointment_len = len(all_appointment_ids)
            resource.planned_appointment_len = len(all_appointment_ids.filtered(lambda ap: ap.state == "reserved"))

    @api.depends(
        "resource_type_id.allocation_method", "appointment_ids.resource_id", "appointment_ids.state", 
        "appointment_ids.duration", "appointment_ids.datetime_start", "appointment_ids.datetime_end", 
        "appointment_ids.service_id.duration_uom", "extra_appointment_ids.resource_id", "extra_appointment_ids.state", 
        "extra_appointment_ids.duration", "extra_appointment_ids.datetime_start", "extra_appointment_ids.datetime_end",
        "extra_appointment_ids.service_id.duration_uom",
    )
    def _compute_allocation_factor(self):
        """
        Compute method for allocation_factor
        """
        for resource in self:
            allocation_factor = 0
            allocation_method = resource.resource_type_id.allocation_method
            if allocation_method == "by_order":
                allocation_factor = resource.sequence
            elif allocation_method == "by_number":
                allocation_factor = resource.planned_appointment_len
            elif allocation_method == "by_workload":
                all_appointment_ids = resource.appointment_ids + resource.extra_appointment_ids
                allocation_factor = sum(
                    all_appointment_ids.filtered(lambda ap: ap.state == "reserved").mapped("duration")
                )
            resource.allocation_factor = allocation_factor

    @api.depends("rating_ids.rating", "rating_ids.parent_res_id")
    def _compute_rating_satisfaction(self):
        """
        Compute method for rating_satisfaction

        Methods:
         * _calculate_satisfaction_rate of rating.rating
        """
        for resource in self:
            rate_final = -1
            if resource.rating_ids:
                rate = self.env["rating.rating"]._calculate_satisfaction_rate(resource)
                rate_final = rate[resource.id]
            resource.rating_satisfaction = rate_final

    def _inverse_name(self):
        """
        Inverse method for name
        """
        for resource in self:
            resource.resource_id.name = resource.name

    def _inverse_resource_type_id(self):
        """
        Inverse method for resource_type_id
        It is for the case of not manual form onchange. For details look at onchange
        """
        for resource in self:
            resource.service_ids = [(6, 0, resource.resource_type_id.service_ids.ids)]
            if resource.resource_type_id.company_id != resource.company_id:
                resource.company_id = resource.resource_type_id.company_id

    @api.constrains("main_resource_id", "domain_resource_ids")
    def _constrains_info_resources(self):
        """
        Constraint method for main_resource_id and domain_resource_ids
        The resource cannot be simultaneously prime and alias
        """
        for resource in self:
            if resource.main_resource_id and resource.domain_resource_ids:
                raise ValidationError(_("An alias resource cannot be prime for other aliases"))

    @api.onchange("resource_type_id")
    def _onchange_resource_type_id(self):
        """
        Onchange method for resource_type_id
        If it is changed we should replace previous services with new ones, and after that remove excess
        Services of resources are alsways subset of resource types
        """
        for resource in self:
            resource.service_ids = [(6, 0, resource.resource_type_id.service_ids.ids)]
            resource.company_id = resource.resource_type_id.company_id

    resource_id = fields.Many2one(copy=False)
    resource_calendar_id = fields.Many2one(required=False)
    name = fields.Char(string="Name", required=True, translate=True, inverse=_inverse_name)
    resource_type_id = fields.Many2one(
        "business.resource.type",
        string="Type",
        required=True,
        ondelete="cascade",
        inverse=_inverse_resource_type_id,
    )
    main_resource_id = fields.Many2one(
        "business.resource",
        string="Alias for",
        ondelete="cascade",
        help="If chosen, this resource will be considered an alias for another resource. So, it will not have its own\
calendar and responsible user. Usually, used when the same employee/equipment might relate to a few resource types\
simultaneously",
    )
    info_resource_id = fields.Many2one(
        "business.resource",
        string="Real Resource",
        compute=_compute_info_resource_id,
        compute_sudo=True,
        store=True,
    )
    domain_resource_ids = fields.One2many(
        "business.resource",
        "main_resource_id",
        string="Aliases",
        context={"active_test": False},
    )
    appointment_ids = fields.One2many("business.appointment", "resource_id", string="Appointments")
    extra_appointment_ids = fields.Many2many(
        "business.appointment",
        "business_resource_business_appoinment_extra_rel_table",
        "business_appointment_rel_id",
        "business_resource_rel_id",
        string="Extra Appointments",
    )
    service_method = fields.Selection(related="resource_type_id.service_method", store=True, compute_sudo=True)
    service_ids = fields.Many2many(
        "appointment.product",
        "appointment_product_business_resource_rel_table",
        "appointment_product_id",
        "business_resource_id",
        string="Available Services",
        copy=True,
    )
    final_service_ids = fields.Many2many(
        "appointment.product",
        "appointment_product_business_resource_rel_final_table",
        "appointment_product_final_id",
        "business_resource_final_id",
        string="Services",
        compute=_compute_final_service_ids,
        store=True,
    )
    type_available_service_ids = fields.Many2many(
        "appointment.product",
        "appointment_product_business_resource_rel_table_available",
        "product_id_available",
        "business_resource_id_available",
        string="Type Services",
        compute=_compute_type_available_service_ids,
        store=True,
    )
    appointment_len = fields.Integer(string="Number of appointments", compute=_compute_appointment_len, store=True)
    planned_appointment_len = fields.Integer(
        string="Planned appointments",
        compute=_compute_appointment_len,
        store=True,
    )
    allocation_factor = fields.Float(
        string="Allocation Factor",
        compute=_compute_allocation_factor,
        compute_sudo=True,
        store=True,
    )
    resource_type = fields.Selection(
        related="resource_id.resource_type",
        index=True,
        store=True,
        readonly=False,
        string="Resource Kind",
        default="material",
        required=True,
        copy=True,
    )
    user_id = fields.Many2one(
        "res.users",
        "Responsible",
        related="resource_id.user_id",
        store=True,
        readonly=False,
        tracking=3,
    )
    info_info_user_id = fields.Many2one(
        "res.users",
        string="Info responsible",
        compute=_compute_info_resource_id,
        compute_sudo=True,
        store=True,        
    )
    extra_user_ids = fields.Many2many(
        "res.users",
        "res_users_business_resource_extra_managers",
        "res_users_rel_id",
        "business_resource_rel_id",
        string="Extra Managers",
    )
    info_resource_calendar_id = fields.Many2one(
        "resource.calendar",
        string="Info Resource Calendar",
        compute=_compute_info_resource_id,
        compute_sudo=True,
        store=True,        
    )
    location = fields.Char(string="Location", translate=True)    
    color = fields.Integer(string="Color")
    description = fields.Text(string="Description", translate=True, default="")
    rating_ids = fields.One2many("rating.rating", "resource_id", string="Ratings", auto_join=True)
    rating_satisfaction = fields.Integer(
        string="Average Rating",
        compute=_compute_rating_satisfaction,
        store=True, 
        default=-1,
    )
    active = fields.Boolean(
        "Active",
        related="resource_id.active",
        default=True,
        store=True,
        readonly=False,
    )
    sequence = fields.Integer(string="Sequence")
    sucess_email_partner_ids = fields.Many2many(
        "res.partner",
        "res_partner_business_resource_success_rel_table",
        "res_partner_id",
        "business_resource_id",
        string="Success emails CC",
        help="Success emails will be sent to those partners as a copy of client success emails",
    )

    _order = "sequence, id"

    def action_open_appointments(self):
        """
        The method to open appointments (introduced for kanban to pass context)

        Returns:
         * dict

        Extra info:
         * Expected singleton
        """
        action_id = self.sudo().env.ref("business_appointment.business_appointment_action").read()[0]
        action_id["context"] = {
            "default_resource_id": self.id, "default_resource_type_id": self.resource_type_id.id,
        }
        return action_id

    def action_construct_time_slots(
        self, resource_type_id, service_id, duration, date_start, date_end, active_month=False, active_year=False,
        tz_info={}, chosen_cores=[],
    ):
        """
        The method to calculate time slots for these resources and params (used in JavaScript)
        IT IS THE CORE METHOD OF THE APP

        Args:
         * resource_type_id - int - ID of business.resource.type
         * service_id - int - ID of appointment.product
         * duration - float
         * date_start - str
         * date_end -ste
         * active_month - str (date) or False
         * active_year - str (int)
         * tz_info - dict.
            EITHER (if timezone is manually selected):
             ** targetTz - name of chosen timezone
            OR (if timezone is )
             ** timeZoneOffset - int - difference of time from UTC in browser
             ** timeZoneName - char - name of timezone
         * chosen_cores - list of dicts

        Methods:
         * _find_tz_options
         * _retrieve_extra_resources_intervals  
         * _retrieve_resource_intervals
         * _calculate_switcher
         * _split_intervals_to_slots
         * _prepare_js_dict_of_slots

        Returns:
         * dict of
          ** day_slots - list of dicts
            *** day: str
            *** slots: - list of dicts: day_to_sort (datetime.date), day (str), start (str), end (str), resource_ids
                        (list of resources IDS), resource resource_names (char)
          ** tz_options - list of typles
          ** default_tz - str
          ** unique_months - list of available months (str - the first month day)
          ** unique_years - list of available years
          ** active_month - str - which month is active
        """
        resource_type_id = self.env["business.resource.type"].browse(resource_type_id)
        resource_ids = self or resource_type_id.resource_ids
        if len(resource_ids) > 1:
            resource_ids = resource_ids.sorted(key=lambda reso: reso.allocation_factor)
        service_id = self.env["appointment.product"].browse(service_id)
        service_id = service_id.sudo()
        duration_uom = service_id.duration_uom or "hours"
        if not duration or duration <= 0:
            duration = duration_uom == "hours" and service_id.appointment_duration \
                or service_id.appointment_duration_days*24 or 1
        resource_ids = resource_ids.filtered(lambda re: service_id.id in re.final_service_ids.ids)
        tz_options, default_tz = self._find_tz_options(tz_info=tz_info)
        target_tz = default_tz and timezone(default_tz) or UTCTZ
        date_start = date_start and target_tz.localize(fields.Datetime.from_string(date_start)) or False
        date_end = date_end and target_tz.localize(fields.Datetime.from_string(date_end)) or False
        date_end = date_end and (date_end + relativedelta(days=1)) or False
        # retrieve required service values to optimize read
        extra_working_calendar_id = service_id.extra_working_calendar_id
        start_round = duration_uom == "hours" and int(service_id.start_round_rule * 60) \
            or int(service_id.start_round_rule_days * 60)
        extra_lines = service_id.extra_resource_ids
        start_limit_rule_id = service_id.start_limit_rule_id
        end_limit_rule_id = service_id.end_limit_rule_id
        checkout_time = service_id.checkout_time
        step_duration = duration_uom == "hours" and service_id.step_duration or service_id.step_duration_days * 24
        already_chosen_domain = []
        if chosen_cores:
            already_chosen_ids = [ch_id.get("id") for ch_id in chosen_cores]
            already_chosen_domain = [("id", "in", already_chosen_ids)]
        # get extra resources possible intervals
        restricted_intervals = resource_ids._retrieve_extra_resources_intervals(
            extra_lines=extra_lines,
            start_dt=date_start, 
            end_dt=date_end,
            extra_service_calendar_id=extra_working_calendar_id,
            chosen_domain=already_chosen_domain,
        )
        # get main resources interval adapted for restrictions
        intervals_dict = resource_ids._retrieve_resource_intervals(
            start_dt=date_start, 
            end_dt=date_end,
            extra_service_calendar_id=extra_working_calendar_id,
            extra_intervals=restricted_intervals,
            chosen_domain=already_chosen_domain,
        )
        # calculate months where intervals are present
        unique_months, to_remove_intervals, current_month, unique_years = self._calculate_switcher(
            interv_dict=intervals_dict,
            duration=duration,
            default_tz=target_tz,
            active_month=active_month,
            active_year=active_year,
        )
        # prepare real time slots adapted for all left restrictions and rounding
        slots = []
        for resource in resource_ids:
            intervals = intervals_dict.get(resource.id)
            if to_remove_intervals:
                intervals -= to_remove_intervals
            slots += resource._split_intervals_to_slots(
                intervals=intervals,
                duration=duration,
                step_duration=step_duration,
                default_tz=target_tz,
                duration_uom=duration_uom,
                start_round=start_round,
                extra_intervals=restricted_intervals,
                start_limit_rule_id=start_limit_rule_id,
                end_limit_rule_id=end_limit_rule_id,
                checkout_time=checkout_time,
            )
        # make time slots formatted for the UI
        day_slots = self._prepare_js_dict_of_slots(slots)
        return {
            "day_slots": day_slots,
            "tz_options": tz_options,
            "default_tz": default_tz,
            "unique_months": unique_months,
            "active_month": current_month,
            "unique_years": unique_years,
            "chosen_cores": self._retrieve_appointment_values(chosen_cores, target_tz),
        }

    def action_open_leaves(self):
        """
        The method to open leaves related to this resource and calendar

        Returns:
         * dict of act_window

        Extra info:
         * We have a function since we can't place "resource_id" on a form due to related specifics
         * Expected singleton
        """
        action = self.sudo().env.ref("resource.action_resource_calendar_leave_tree").read()[0]
        action["context"] = {
            "default_resource_id": self.resource_id.id, "search_default_resource_id": self.resource_id.id,
        }
        return action

    @api.model
    def _find_tz_options(self, tz_info):
        """
        The method to return timezone option
         1. If receive target_tz we use it
            [It also means that the option of tz is turned on (since selection is shown) --> we do not need to check
            configuration]
         2. Otherwise we just take tz received from js
         3. In case default timezone received from JS is not among pytz timezones (an extreme option)--> get try to get
            any with the same offset
         4. If selection is not assumed at all we pass an empty list and as default tz and company time zone as default

        Args:
         * tz_info - dict.
            EITHER (if timezone is manually selected):
             ** targetTz - name of chosen timezone
            OR (if timezone is )
             ** timeZoneOffset - int - difference of time from UTC in browser
             ** timeZoneName - char - name of timezone

        Methods:
         * get_possible_timezones_by_offset

        Returns:
         * list of timezones, char - timezone
        """
        tz_options = _tzs
        default_tz = tz_info.get("targetTz")
        # 1
        if not default_tz:
            timezone_requried = self.env.company.ba_timezone_option
            if timezone_requried:
                # 2
                tz_name = tz_info.get("timeZoneName")
                for tz in tz_options:
                    if tz_name == tz[0]:
                        default_tz = tz_name
                        break
                else:
                    # 3
                    tz_offset = tz_info.get("timeZoneOffset") or 0
                    default_tz = get_possible_timezones_by_offset(tz_offset)
            else:
                # 4
                tz_options = []
                default_tz = self.env.user.sudo().company_id.partner_id.tz or self._context.get("tz") or "UTC"
        return tz_options, default_tz

    def _retrieve_resource_intervals_single(
        self, start_dt=None, end_dt=None, extra_service_calendar_id=None, extra_intervals=None, chosen_domain=[],
    ):
        """
        The method to calculate intervals for a resource

        Args:
         * start_dt - starting datetime to search slots
         * end_dt - ending datetime to search slots
         * extra_service_calendar_id - resource.calendar of service - as an extra restriction
         * extra_intervals - dict of list (extra resources ints) and Intervals or None
         * chosen_domain - list (RPR)

        Methods:
         * _return_timeframes of business.resource.type
         * _ba_work_intervals of resource.calendar
         * _amend_intervals_for_already_occupied
         * _get_empty_interval of resource.calendar

        Returns:
         * Interval object
        
        Extra info:
         * We do not check extra_intervals for already occupied (_amend_intervals_for_already_occupied), since each
           extra resource was already checked for that during their calculation
         * Expected singleton
        """
        info_resource_id = self.info_resource_id
        res_start, res_end = self.resource_type_id._return_timeframes(start_dt=start_dt, end_dt=end_dt)
        intervals = info_resource_id.resource_calendar_id._ba_work_intervals(
            start_dt=res_start,
            end_dt=res_end,
            resource=info_resource_id.resource_id,
            extra_service_calendar_id=extra_service_calendar_id,
        )
        # for self, not info_resource_id since rtype needed and to prepare correct data
        busy_intervals = self._amend_intervals_for_already_occupied(
            start_dt=res_start, end_dt=res_end, chosen_domain=chosen_domain
        )
        intervals -= busy_intervals
        if extra_intervals:
            restriction = False 
            for resources, e_intervals in extra_intervals.items():
                if info_resource_id.id not in resources:
                    if restriction:
                        restriction = restriction | e_intervals
                    else:
                        restriction = e_intervals
            if restriction:
                intervals = restriction & intervals
            else:
                intervals = self.resource_calendar_id._get_empty_interval()
        return intervals

    def _retrieve_resource_intervals(
        self, start_dt=None, end_dt=None, extra_service_calendar_id=None, extra_intervals=None, chosen_domain=[],
    ):
        """
        The method to calculate intervals for resources
         IMPORTANT NOTE: do not merge intervals by various resources, since it is not logically correct: 13:20-13:30;
         13:25-13:50 would result in a single slot 13:20-13:50

        Args:
         * start_dt - starting datetime to search slots
         * end_dt - ending datetime to search slots
         * extra_service_calendar_id - resource.calendar of service - as an extra restriction
         * extra_intervals - dict of list (extra resources ints) and Intervals, might be also False (no viable options)
           or None (no restriction)
         * chosen_domain - list (RPR)  

        Methods:
         * _retrieve_resource_intervals_single
         * _get_empty_interval of resource.calendar

        Returns:
         * dict of int (resource id) and Intervals object
        """
        self = self.sudo()
        res_intervals = {}
        for resource in self:           
            if extra_intervals is None:
                intervals = resource._retrieve_resource_intervals_single(
                    start_dt=start_dt, 
                    end_dt=end_dt, 
                    extra_service_calendar_id=extra_service_calendar_id,
                    chosen_domain=chosen_domain,
                )
            elif extra_intervals is False:
                intervals = self.resource_calendar_id._get_empty_interval()
            else:
                intervals = resource._retrieve_resource_intervals_single(
                    start_dt=start_dt, 
                    end_dt=end_dt, 
                    extra_service_calendar_id=extra_service_calendar_id,
                    extra_intervals=extra_intervals,
                    chosen_domain=chosen_domain,
                )
            res_intervals.update({resource.id: intervals})
        return res_intervals

    def _retrieve_extra_resources_intervals(
        self, extra_lines=None, start_dt=None, end_dt=None, extra_service_calendar_id=None, chosen_domain=[],
    ):
        """
        The method to calculate intervals for extra resources

        Args:
         * extra_lines - appointment.product.line recordset
         * start_dt - starting datetime to search slots
         * end_dt - ending datetime to search slots
         * extra_service_calendar_id - resource.calendar of service - as an extra restriction
         * chosen_domain - list (RPR)

        Methods:
         * _get_all_extra_resources of business.resource extra
         * _retrieve_resource_intervals_single

        Returns:
          * dict - if something is fine
            ** key - list of ints - business.resource
            ** value - Interval object
          * None - if no extra resources are assumed
          * False - if extra resources do not assume viable intervals
        """
        def allUnique(checked_list):
            """
            The method to check that a list is unique

            Args:
             * checked_list - list

            Returns:
             * bool

            Extra info:
             * based on https://stackoverflow.com/a/5281641
            """
            seen = set()
            return not any(i in seen or seen.add(i) for i in checked_list)

        if not extra_lines:
            # no lines > no restrictions on a calendar
            return None

        # Prepare the list of resources per each line and retrieve viable intervals for resources
        full_extras_list = [] # would be a list of list to get 
        resource_intervals = {} # the dict to efficiently get intervals for a required resource
        for extra_line in extra_lines:
            extra_resources = extra_line._get_all_extra_resources()
            extra_resources_list = []
            for resource in extra_resources:    
                intervals = resource_intervals.get(resource.id)
                if intervals is None:
                    # The condition is added not to calculate intervals for repeated resources
                    intervals = resource._retrieve_resource_intervals_single(
                        start_dt=start_dt, 
                        end_dt=end_dt, 
                        extra_service_calendar_id=extra_service_calendar_id,
                        chosen_domain=chosen_domain,
                    )
                    resource_intervals.update({resource.id: intervals})
                if intervals: 
                    # No sense to add resource if it has no viable intervals
                    extra_resources_list.append(resource.id)
            if extra_resources_list:
                full_extras_list.append(extra_resources_list)
            else:
                # If a specifi extra line of service does not assume any viable resource > can break the method
                return False
        # Prepare all possible combinations resources:intervals
        result = {}
        # Also make sure combinations are unique (but with kept order)
        all_combinations = list(dict.fromkeys(itertools.product(*full_extras_list))) 
        for extra_combination in all_combinations:
            if allUnique(extra_combination):
                # otherwise it would be (John, John) what is not good since John cannot be both dentist and assistant
                intersected_intervals = False
                for resource_int in extra_combination:
                    this_resource_intervals = resource_intervals.get(resource_int)
                    if not intersected_intervals:
                        intersected_intervals = this_resource_intervals
                    else:
                        intersected_intervals = intersected_intervals & this_resource_intervals
                    if not intersected_intervals:
                        # no sense to iterate if the current combination is not already viable
                        break
                else:
                    result.update({extra_combination: intersected_intervals})
        return result or False

    @api.model
    def _calculate_switcher(self, interv_dict, duration=1.0, default_tz=UTCTZ, active_month=False, active_year=False):
        """
        The method goal is to increase performance of slots calculation by spliting slots into months if a period is too
        big
         1. Get all possible intervals (months) which have enough duration
         2. Get unique months, but only in case there are many shifts (no sense to split "10" shifts on 3 pages)
         3. Get intervals which should not be shown (all times not in this month).

        Args:
         * interv_dict - dict of {resource: Interval objects} (look at resource > resource.py)
         * duration - float
         * default_tz - timezone
         * active_month - str (date) or False - currently chosen month
         * active_year - str (date) or False - currently chosen year

        Returns:
         * unique_months - list of dates or False (if splitting to months is not necessary)
         * Interval Object - intervals which time slots should NOT be shown
         * current_month - str - date
         * unique_years - list of unique years or False (if splitting to months is not necessary)
        """
        # 1
        all_shifts = []
        potential_shifts_len = 0
        duration_seconds = duration * 3600
        for key, intervals in interv_dict.items():
            for interval in intervals:
                interval_start, interval_end = interval[0], interval[1]
                potential_shifts_len += int((interval_end - interval_start).total_seconds() // duration_seconds)
                start = interval_start
                while True:
                    if start.year != interval_end.year or start.month < interval_end.month:
                        if (interval_end - start).total_seconds() >= duration_seconds:
                            all_shifts.append(fields.Date.from_string(start.strftime("%Y-%m-01")))
                        start = default_tz.localize(
                            fields.Datetime.from_string((start + relativedelta(months=1)).strftime("%Y-%m-01"))
                        )
                    else:
                        if (interval_end - start).total_seconds() >= duration_seconds:
                            all_shifts.append(fields.Date.from_string(start.strftime("%Y-%m-01")))
                        break
        # 2
        unique_months = False
        unique_years = False
        if all_shifts and potential_shifts_len >= MAXINTERVALS_NOTTOSPLITBYMONTHS:
            unique_months = sorted(list(set(all_shifts)))
            unique_months = len(unique_months) > 1 and unique_months or False
            if unique_months:
                unique_years = sorted(list(set([mo.year for mo in unique_months])))
                unique_years = len(unique_years) > 1 and unique_years or False
        # 3
        to_remove_intervals = False
        current_month = False
        if unique_months:
            if active_month and fields.Date.from_string(active_month) in unique_months:
                current_month = active_month
            elif active_year:
                for this_month in unique_months:
                    if str(this_month.year) == active_year:
                        current_month = this_month
                        break
            if not current_month:
                current_month = unique_months[0]
            month_start = default_tz.localize(fields.Datetime.from_string(current_month))
            to_remove_previous = (datetime.min.replace(tzinfo=default_tz), month_start - relativedelta(seconds=1), self)
            to_remove_further = (month_start + relativedelta(months=1), datetime.max.replace(tzinfo=default_tz), self)
            to_remove_intervals = Intervals([to_remove_previous, to_remove_further])
        return unique_months, to_remove_intervals, current_month, unique_years

    def _split_intervals_to_slots(
        self, intervals, duration=1.0, step_duration=None, default_tz=UTCTZ, duration_uom="hours", start_round=False, 
        extra_intervals=None, start_limit_rule_id=None, end_limit_rule_id=None, checkout_time=0.0,
    ):
        """
        The method to split available intervals by required service duration

        Args:
         * intervals - Interval object
         * duration - float
         * default_tz - timezone
         * duration_uom - char - hours or days
         * start_round - int - how start should be rounded
         * extra_intervals - dict of list (extra resources ints) and Intervals, might be also False (no viable options)
           or None (no restriction)
         * start_limit_rule_id - appointment.day.limit object
         * end_limit_rule_id - appointment.day.limit object 
         * checkout_time - float

        Methods:
         * _round_time_by_conf
         * _return_lang_date_format
         * _check_day of appointment.day.limit

        Returns:
         * list of dicts: day_to_sort (datetime.date), day (str), start (str), end (str), list of resources IDS,
           resource name, extra_ids (list of lists), e.g.:
            [
                {
                    "day_to_sort": 22-05-2020,
                    "day": "22-05-2020 Tue",
                    "start": "10:00",
                    "end": "10:30",
                    "resource_ids": [17],
                    "resource_names: "John Brown",
                    "extra_ids": [[1,2],[7,12],[1,3,5]],
                },
                {
                    "day_to_sort": 24-05-2020,
                    "day": "24-05-2020 Wed",
                    "start": "13:00",
                    "end": "13:30",
                    "resource_ids": [(17, John Brown)],
                    "resource_names: "John Brown",
                    "extra_ids": [[1,2],[7,12],[1,3,5]],
                }
            ]

        Extra info:
         * Expected singleton
        """
        lang_date_format = self._return_lang_date_format()
        slots = []
        for interval in intervals:
            resource_tz = interval[0].tzinfo
            start = self._round_time_by_conf(interval[0], default_tz=default_tz, duration_uom=duration_uom, 
                start_round=start_round)
            end = interval[1]
            end_slot = start + relativedelta(hours=duration)
            while end_slot <= end:
                day_to_sort = start.date()
                day = day_to_sort.strftime(lang_date_format)
                start_title = start.strftime("%I:%M %p")
                end_title = (end_slot-relativedelta(hours=checkout_time)).strftime("%I:%M %p")
                if duration_uom == "days":
                    # make sure that start and end are possible by days if not > move for a day
                    restriction_in_place = False
                    if start_limit_rule_id:
                        restriction_in_place = start_limit_rule_id._check_day(start, resource_tz=resource_tz)
                    if not restriction_in_place and end_limit_rule_id:
                        # substract one second, so if 00:00 the next day is not considered as a new weekday
                        restriction_in_place = end_limit_rule_id._check_day(
                            end_slot-relativedelta(seconds=1), resource_tz=resource_tz
                        )
                    if restriction_in_place:                    
                        start += relativedelta(hours=24)
                        end_slot += relativedelta(hours=24)                        
                        continue
                    # format days to include day if start and end
                    start_title = "{} {}".format(day, start_title)
                    end_title = "{} {}".format(end_slot.date().strftime(lang_date_format), end_title)
                
                if extra_intervals is not False:
                    # this condition seems excess since we already ammend intervals for all possible requisits
                    # hovewer, we keep it to avoid dramatic sudden effects
                    slot = {
                        "day_to_sort": day_to_sort,
                        "real_start_utc": start.astimezone(UTCTZ),
                        "day": day,
                        "start": start_title,
                        "end": end_title,
                        "resource_ids": [self.id],
                        "resource_names": self.name,
                        "title": "{}{} - {}".format(
                            duration_uom == "hours" and day + " " or "", start_title, end_title
                        ),
                    }                    
                    if extra_intervals is None:
                        slots.append(slot)
                    else:
                        extra_ids = []
                        for e_resources, e_intervals in extra_intervals.items():
                            if self.info_resource_id.id in e_resources:
                                # main resource equals extra resource > dentist and assistant cannot coincide
                                continue
                            for extra_interval in e_intervals:
                                extra_start = extra_interval[0]
                                extra_end = extra_interval[1]
                                if extra_start <= start and extra_end >= end_slot:
                                    extra_ids.append([er for er in e_resources])
                                    break
                        if extra_ids:
                            # otherwise
                            slot.update({"extra_ids": extra_ids})
                            slots.append(slot)
                start += relativedelta(hours=step_duration)
                end_slot += relativedelta(hours=step_duration)
        return slots

    def _amend_intervals_for_already_occupied(self, start_dt=None, end_dt=None, chosen_domain=[]):
        """
        The method to remove from intervals already occupied slots
         0. Prepare resource domain. We assume that any main or extra resource appointment lead to be busy
            The very special case is for appointments from website under portal users. Here we know the partner and
            can check hist reservations as well
         1. Check ready slots
         2. Check temporary reservation
         3. Check calendar events if it is set up in resource type

        Args:
         * start_dt - starting datetime to search slots
         * end_dt - ending datetime to search slots
         * chosen_domain - list (RPR)

        Methods:
         * _take_expiration_limits of business.appointment.core
         * localize_day_to_resource_datetime

        Returns:
         * Interval objects (look at resource > resource.py)

        Extra info:
         * We consiously do not restrict slots by required date, since we then would substract intervals, while
           search becomes faster + no tz issues. We rely only upon rough separator, since appointments are possible
           only for the future
         * An object is considered busy, in case its resource or extra_resource_ids equal to the currently considered
           resource 
         * Expected singleton
        """
        info_resource_id = self.sudo().info_resource_id
        tz = timezone(info_resource_id.resource_calendar_id.tz)
        start_dt = start_dt.astimezone(tz)
        end_dt = end_dt.astimezone(tz)
        result = []
        start_compare = datetime_to_string(start_dt)
        end_compare = datetime_to_string(end_dt)
        rough_separator = fields.Datetime.now()-relativedelta(days=1)
        # 0
        resource_domain = OR([
            [("info_resource_id", "=", info_resource_id.id)], [("extra_resource_ids", "=", info_resource_id.id)]
        ])
        if self.env.context.get("website_id") and not self.env.user._is_public():
            resource_domain = OR([resource_domain, [("partner_id", "=", self.env.user.partner_id.id)]])
        if chosen_domain:
            resource_domain = OR([resource_domain, chosen_domain])
        # 1
        busy_slots = self.env["business.appointment"].search(resource_domain +[
            ("datetime_start", ">", rough_separator), ("state", "in", ["reserved"]),
        ])
        for slot in busy_slots:
            dt0 = string_to_datetime(slot.datetime_start).astimezone(tz)
            dt1 = string_to_datetime(slot.datetime_end).astimezone(tz)
            result.append((max(start_dt, dt0), min(end_dt, dt1), self.resource_id))
        # 2     
        preresrvation_datetime, schedule_datetime = self.env["business.appointment.core"]._take_expiration_limits()
        temp_busy_slots = self.env["business.appointment.core"].search(resource_domain + [
            ("datetime_start", ">", rough_separator),
            "|",
                "&",
                    ("state", "=", "draft"), ("create_date", ">=", preresrvation_datetime),
                "&",
                    ("state", "=", "need_approval"), ("schedule_datetime", ">=", schedule_datetime),
        ])
        for slot in temp_busy_slots:
            dt0 = string_to_datetime(slot.datetime_start).astimezone(tz)
            dt1 = string_to_datetime(slot.datetime_end).astimezone(tz)
            result.append((max(start_dt, dt0), min(end_dt, dt1), self.resource_id))
        # 3
        calendar_event_workload = self.resource_type_id.calendar_event_workload
        if calendar_event_workload:
            partner_id = info_resource_id.user_id.partner_id.id
            event_ids = self.env["calendar.event"].search([
                ("partner_ids", "=", partner_id), ("start", ">", rough_separator),
            ])
            for slot in event_ids:
                if slot.allday:
                    dt0 = localize_day_to_resource_datetime(slot.start_date, tz)
                    dt1 = localize_day_to_resource_datetime(slot.stop_date+relativedelta(days=1), tz)
                    result.append((max(start_dt, dt0), min(end_dt, dt1), self.resource_id))
                else:
                    dt0 = string_to_datetime(slot.start).astimezone(tz)
                    dt1 = string_to_datetime(slot.stop).astimezone(tz)
                    result.append((max(start_dt, dt0), min(end_dt, dt1), self.resource_id))
        return Intervals(result)

    @api.model
    def _round_time_by_conf(self, appoin_time, default_tz, duration_uom="hours", start_round=False):
        """
        The method to round time for a required precision based on configs

        Args:
         * appoin_time - datetime.datetime (with resource calendar tz)
         * default_tz - timezone
         * duration_uom - char - hours or days
         * start_round - int - how start should be rounded

        Returns:
         * datetime.datetime

        Extra info:
         * rounding is done in "absolute" calendar days, since it should be done according to resource calendar tz
         * we do not care of seconds, considering that 14:22:57 is fine as 14:22:00
        """
        res_datetime = appoin_time.replace(second=0)
        minutes_to_compare = res_datetime.hour * 60 + res_datetime.minute   
        if duration_uom == "hours":
            start_round = start_round or 1
            division_factor = minutes_to_compare // start_round
            if (minutes_to_compare % start_round) != 0:
                division_factor += 1
            to_add_minutes = division_factor * start_round - minutes_to_compare
            res_datetime += relativedelta(minutes=to_add_minutes)
        else:
            start_round = start_round or 0
            if minutes_to_compare > start_round:
                res_datetime += relativedelta(days=1)
            res_datetime += relativedelta(minutes=start_round-minutes_to_compare) 
        return res_datetime.astimezone(default_tz)

    @api.model
    def _prepare_js_dict_of_slots(self, slots):
        """
        The method to prepare slots in a proper format. The idea is combine slots by day for simplier xml representation

        Args:
         * list of slots dict

        Returns:
         * list of dicts
            *** day: str
            *** slots: - list of dicts: day_to_sort (datetime.date), day (str), start (str), end (str), resource_ids
                (list of resources IDS), resource resource_names (char), extra_ids (list of tuples)
        """
        day_slots = []
        if slots:
            # slots = sorted(slots, key=lambda k: (k["day_to_sort"], k["start"]))
            cur_day_res = []
            to_check_day = slots[0].get("day")
            previous_start = False
            for slot in slots:
                if slot.get("day") == to_check_day:
                    if slot.get("start") == previous_start:
                        # 5
                        cur_day_res[-1].update({
                            "resource_ids": cur_day_res[-1].get("resource_ids") + slot.get("resource_ids"),
                            "resource_names": "{}, {}".format(
                                cur_day_res[-1].get("resource_names"), slot.get("resource_names")
                            ),
                        })
                    else:
                        cur_day_res.append(slot)
                else:
                    day_slots.append({"day": to_check_day, "slots": cur_day_res})
                    to_check_day = slot.get("day")
                    cur_day_res = [slot]
                previous_start = slot.get("start")
            else:
                day_slots.append({"day": to_check_day, "slots": cur_day_res})       
        return day_slots

    @api.model
    def _retrieve_appointment_values(self, appointments, default_tz):
        """
        The method to construct chosen appointment values, including adaptation by time zone

        Args:
         * appointments - list of dict - id (int), requestID (int)
         * default_tz - timezone object

        Methods:
         * _return_lang_date_format

        Returns
         * list of dicts: id, title (str)
        """
        res = []
        lang_date_format = self._return_lang_date_format()
        for core in appointments:
            core_id = self.env["business.appointment.core"].sudo().browse(core.get("id"))
            duration_uom = core_id.service_id.duration_uom
            start = core_id.datetime_start.astimezone(default_tz)
            end = core_id.datetime_end.astimezone(default_tz)
            start_title = start.strftime("%I:%M %p")
            end_title = end.strftime("%I:%M %p")
            day = start.date().strftime(lang_date_format)
            if duration_uom == "days":
                start_title = "{} {}".format(day, start_title)
                end_title = "{} {}".format(end.date().strftime(lang_date_format), end_title)
            title = "{}: {}{} - {}".format(
                core_id.resource_id.name,
                duration_uom == "hours" and day + " " or "", 
                start_title, 
                end_title
            )
            res.append({"id": core.get("id"), "title": title})
        return res

    @api.model
    def _return_lang_date_format(self):
        """
        The method to return date format for js

        Returns:
         * str
        """
        lang = self._context.get("lang")
        lang_date_format = "%m/%d/%Y"
        if lang:
            record_lang = self.env["res.lang"].search([("code", "=", lang)], limit=1)
            lang_date_format = record_lang and record_lang.date_format or lang_date_format
        return lang_date_format
