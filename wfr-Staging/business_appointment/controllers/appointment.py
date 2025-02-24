# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta

from odoo import fields, http
from odoo.exceptions import AccessError
from odoo.http import request


class AppointmentController(http.Controller):
    """
    The controller to manage RPC calls invoked by appointment scheduling
    """
    @http.route(["/business_appointment/defaults"], methods=["POST"], type="json", auth="public", website=True)
    def get_appointment_defaults(self):
        """
        The method to prepare scheduling defaults needed for the slots kanban
            
        Returns:
         * dict
        """
        return {"date_start": fields.Date.today(), "date_end": fields.Date.today() + relativedelta(days=30)}

    @http.route(["/business_appointment/duration"], methods=["POST"], type="json", auth="public", website=True)
    def get_appointment_duration(self, service_id, preduration=False):
        """
        The method get duration settings based on the service

        Args:
         * service_id - int - ID of the schedule service
         * preduration - float (hours)

        Methods:
         * _return_available_choices of appointment.product

        Returns:
         * dict (keys depend on the settings)
        """
        service = request.env["appointment.product"].browse(service_id)
        manual_duration = service.manual_duration
        duration_uom = service.duration_uom or "hours"
        duration = duration_uom == "hours" and service.appointment_duration or service.appointment_duration_days
        duration_choices = manual_duration and service._return_available_choices() or False
        if duration_choices and manual_duration and preduration:
            preduration = duration_uom == "hours" and preduration or preduration // 24
            if preduration >= duration_choices[0] and preduration <= duration_choices[-1]:
                duration = min(duration_choices, key=lambda choice:abs(choice - preduration))
        return {
            "manual_duration": manual_duration,
            "duration": duration,
            "duration_uom": duration_uom,
            "duration_choices": duration_choices,
        }

    @http.route(["/business_appointment/suggested_products"], methods=["POST"], type="json", auth="public",
        website=True)
    def get_suggested_products(self, service_id, from_website_id=False, appointment_id=False, pricelist_id=False):
        """
        The route method to get suggested products

        Args:
         * service_id - int id of the linked appointment.product
         * from_website - bool
         * appointment_id - int (in case of rescheduling or False)
         * pricelist_id - int or False

        Methods:
         * _get_suggested_products of appointment.product

        Returns:
         * list of dicts
        """
        service = request.env["appointment.product"].browse(service_id)
        return service._get_suggested_products(
            from_website_id=from_website_id, appointment_id=appointment_id, pricelist_id=pricelist_id
        )

    @http.route(["/business_appointment/suggested_product_price"], methods=["POST"], type="json", auth="public",
        website=True)
    def get_suggested_product_price(self, product_id, pricelist_id=False, qty=1.0):
        """
        The route method to get product price based on the pricelist and quantity

        Args:
         * product_id - int id of a product.product
         * pricelist_id - int of product.pricelist or False
         * qty - float

        Methods:
         * action_calculate_price of appointment.product

        Returns:
         * str
        """
        service = request.env["appointment.product"]
        return service.action_calculate_price(product_id=product_id, pricelist_id=pricelist_id, qty=qty)

    @http.route(["/business_appointment/auto/resources"], methods=["POST"], type="json", auth="public", website=True)
    def get_auto_resources(self, resource_type_id):
        """
        The route method to get auto resources by the resource type

        Args:
         * resource_type_id - int

        Returns:
         * list of intes
        """
        return request.env["business.resource.type"].browse(resource_type_id).resource_ids.ids

    @http.route(["/business_appointment/slots"], methods=["POST"], type="json", auth="public", website=True)
    def calculate_appointment_slots(
        self, resource_type_id, resource_ids, service_id, duration=1.0, date_start=False, date_end=False, 
        active_month=False, active_year=False, tz_info={}, chosen_cores=[],
    ):
        """
        The route method to calculate available slots based on the provided params

        Args:
         * @see business.resource action_construct_time_slots

        Methods:
         * action_construct_time_slots

        Returns:
         * dict: @see business.resource action_construct_time_slots
        """
        resources = request.env["business.resource"].browse(resource_ids)
        return resources.action_construct_time_slots(
            resource_type_id=resource_type_id, service_id=service_id, duration=duration, date_start=date_start,
            date_end=date_end, active_month=active_month, active_year=active_year, tz_info=tz_info,
            chosen_cores=chosen_cores,
        )

    @http.route(["/business_appointment/add"], methods=["POST"], type="json", auth="public", website=True)
    def add_reservation_slot(
        self, from_website_id, start_utc, duration, service_id, resource_ids_list, reservation_for_group_id,
        pricelist_id, extra_ids_list, tz_info, extra_product_ids, reschedule_id,
    ):
        """
        The route method to calculate available slots based on the provided params

        Args:
         * from_website_id - int or False
         * start_utc - str
         * duration - float
         * service_id - int - the id of appointment.product
         * resource_ids_list - list of ints
         * reservation_for_group_id - int - ID of the root business.appointment.core
         * pricelist_id - int
         * extra_ids_list - list of lists of ints
         * tz_info - dict
         * extra_product_ids - list of list (m2m commands) or False
         * reschedule_id - business.appointment (for the case of re-scheduling)

        Methods:
         * _find_tz_options of business.resource
         * _create_reservation of business.appointment.core
         * _return_appointment_values of business.appointment

        Returns (alternatively; @see _create_reservation of business.appointment.core):
         * dict of id, str (resource name for the title)
         * False - in case of ordinary error
         * None - if it is an access error
        """
        business_resource_object = request.env["business.resource"]
        appointment_core_object = request.env["business.appointment.core"]
        datetime_start = fields.Datetime.from_string(start_utc)
        datetime_end = datetime_start + relativedelta(hours=duration)
        tz_options, tz = request.env["business.resource"]._find_tz_options(tz_info=tz_info)
        core_vals = {
            "datetime_start": datetime_start,
            "datetime_end": datetime_end,
            "service_id": service_id,
            "pricelist_id": pricelist_id,
            "tz": tz,
            "extra_product_ids": extra_product_ids,
        }
        resource_ids = business_resource_object.browse(resource_ids_list)
        extra_resources = []
        if extra_ids_list:
            for extras in extra_ids_list:
                # sudo is needed since extra resources are not obgligatory published
                extra_resources.append(business_resource_object.sudo().browse(extras))
        if from_website_id:
            core_vals.update({"website_created": True})
            user_id = request.env.user
            if user_id.has_group("base.group_user") or user_id.has_group("base.group_portal"):
                # portal/internal users are considered as clients on the website
                core_vals.update({"partner_id": user_id.partner_id.id})
            else:
                # public users otherwise do not have enough rights
                appointment_core_object = appointment_core_object.sudo()
        if reservation_for_group_id:
            root_id = appointment_core_object.browse(reservation_for_group_id).exists()
            if root_id:
                core_vals.update({"reservation_group_id": root_id.reservation_group_id.id})
        if reschedule_id:
            appointment_id = request.env["business.appointment"].browse(reschedule_id)
            core_vals.update(appointment_id._return_appointment_values(pure_values=True))
            if from_website_id:
                core_vals.update({"agree_terms": True})
        try:
            res = appointment_core_object._create_reservation(
                core_vals=core_vals, resource_ids=resource_ids, extra_resources=extra_resources or False,
            )
        except Exception as e:
            if isinstance(e, AccessError):
                res = None
            else:
                res = False
        return res

    @http.route(["/business_appointment/remove"], methods=["POST"], type="json", auth="public", website=True)
    def remove_reservation(self, reservation_ids):
        """
        The method unreserve time slot

        Args:
         * reservation_ids - list of ints

        Returns:
         * bool
        """
        prereservations = request.env["business.appointment.core"].sudo().browse(reservation_ids)
        res = prereservations.write({"state": "processed"})
        return res
