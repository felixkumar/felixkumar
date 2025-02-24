# -*- coding: utf-8 -*-

import base64
import logging
import werkzeug

from collections import OrderedDict
from markupsafe import Markup

from odoo import _, fields, http, tools
from odoo.http import request
from odoo.tools.safe_eval import safe_eval 

from odoo.addons.portal.controllers.portal import get_records_pager, CustomerPortal, pager as portal_pager

_logger = logging.getLogger(__name__)


def return_resources_set(resources, to_add):
    """
    The method to be triggered from xml to generate resource chosen add

    Args:
     * resources - list or False
     * to_remove - int/str

    Returns:
     * list
    """
    if not resources:
        resources = [to_add]
    elif to_add not in resources:
        resources.append(to_add)
    else:
        resources.remove(to_add) 
    return resources or []

def return_resources_subset(resources, to_remove):
    """
    The method to be triggered from xml to generate resource chosen unlink

    Args:
     * resources - list or False
     * to_remove - int/str

    Returns:
     * list
    """
    if resources and to_remove in resources:
        resources.remove(to_remove) 
    return resources or []


class CustomerPortal(CustomerPortal):
    """
    Overwritting the controller to show apps pages
    """
    ####################################################################################################################
    ################################### Prepare basic values for all controllers  ######################################
    ####################################################################################################################
    def _get_extra_options_ba_values(self):
        """
        The method to get common values introduced by optional apps required for many controllers
        Introduced for inheritance purposes

        Returns:
         * dict
        """
        return {}

    def _prepare_home_portal_values(self, counters):
        """
        Overwrite to understand wheter the portal entries should be shown
        """
        values = super(CustomerPortal, self)._prepare_home_portal_values(counters)
        ba_turn_on_appointments = request.website and request.website.ba_turn_on_appointments or False
        if "ba_counter" in counters:
            values.update({"ba_counter": ba_turn_on_appointments and _("appointments") or 0})
        if not request.env.user.has_group("base.group_portal") \
                and not request.env.user.has_group("business_appointment.group_ba_user"):
            # some internal users might not have rights for appointments
            return values
        if "appointments_count" in counters:
            com_partner_id = request.env.user.partner_id.id
            appointments_count = request.env["business.appointment"].search_count([("partner_id", "=", com_partner_id)]) 
            values.update({"appointments_count": ba_turn_on_appointments and appointments_count or 0})
        return values

    def _prepare_portal_layout_values(self):
        """
        Re-write to pass whether appointments are turned on in portal

        Methods:
         * _get_extra_options_ba_values
        """
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        website_id = request.website
        if website_id and website_id.ba_turn_on_appointments:
            values.update({"ba_turn_on_appointments": True})
            values.update(self._get_extra_options_ba_values())
        return values

    def _check_ba_portal_user_rights(self):
        """
        The method to check rights

        Methods:
         * _check_whether_user_is_not_public

        Returns:
         * dict of values based on user rights used for all business appointment pages
        """
        values = {}
        ba_website_id = request.website
        user_auth = self._check_whether_user_is_not_public()
        if not ba_website_id.ba_turn_on_appointments:
            raise werkzeug.exceptions.NotFound()
        elif not ba_website_id.ba_turn_on_appointments_public and not user_auth:
            raise werkzeug.exceptions.NotFound()           
        return values

    def _prepare_session_order(self):
        """
        The method to prepare values based on order session and url params
         0. We keep session for each website individually
         1. We in try and add log to make sure session appointment exists. Browse does not throw an error
            We also check here that the session relates to a proper website
         2. To the case when portal user logs in after reservation
         3. To make sure for public user there is no re-schedule context
         4. Try to get from session from this partner
         5. Otherwise create a new session order

        Methods:
         * _check_whether_user_is_not_public

        Returns:
         * website.appointment object
        """
        user_auth = self._check_whether_user_is_not_public()
        website_id = request.website
        # 0
        session_key = "session_appointment_id_{}".format(website_id.id)
        session_appointment_id = request.session.get(session_key)
        if session_appointment_id:
            try:
                # 1
                session_appointment_id = request.env["website.business.appointment"].sudo().browse(session_appointment_id)
                _logger.debug("Session appointment {} for type {} is restored".format(
                    session_appointment_id, session_appointment_id.url_ba_type_id
                ))
                if user_auth:
                    # 2
                    partner_id = request.env.user.partner_id.id
                    if partner_id:
                        if partner_id != session_appointment_id.partner_id.id:
                            session_appointment_id.write({"partner_id": partner_id})
                            session_appointment_id.sudo().url_reservation_ids.write({"partner_id": partner_id})
                elif session_appointment_id.resechedule_id:
                    # 3
                    session_appointment_id.resechedule_id = False
            except:
                _logger.debug("Session appointment {} can not be restored".format(session_appointment_id))
                session_appointment_id = False
        if not session_appointment_id:      
            if user_auth:
                # 4
                session_appointment_ids = request.env["website.business.appointment"].search([
                    ("partner_id", "=", request.env.user.partner_id.id), ("website_id", "=", website_id.id),
                ], order="create_date desc", limit=1)
                session_appointment_id = session_appointment_ids and session_appointment_ids[0] or False             
            if not session_appointment_id:
                # 5
                session_appointment_id = request.env["website.business.appointment"].create({
                    "partner_id": user_auth and request.env.user.partner_id.id or False, "website_id": website_id.id,
                })
            request.session[session_key] = session_appointment_id.id     
        return session_appointment_id

    ####################################################################################################################
    ################################### Helpers for all controllers  ###################################################
    ####################################################################################################################
    def _check_whether_user_is_not_public(self):
        """
        The method helper to check whether is user is internal or portal

        Returns:
         * Bool 
        """
        user_id = request.env.user
        return (user_id.has_group("base.group_user") or user_id.has_group("base.group_portal")) and True or False

    def _contact_details_validate(self, session_appointment_id, data):
        """
        The method to check contact details values

        Args:
         * session_appointment_id - website.business.order
         * data - dict of values

        Methods:
         * _return_website_ba_contact_fields of website
         * _check_existing_duplicates

        Returns:
         * dict if field names with errors
         * list of error
         * business.appointment.core values
        """
        error = dict()
        error_message = []
        all_fields, mandatory_fields = request.website._return_website_ba_contact_fields()
        for field_name in mandatory_fields:
            if not data.get(field_name):
                error[field_name] = "missing"
        if data.get("email") and not tools.single_email_re.match(data.get("email")):
            error["email"] = "error"
            error_message.append(_("Invalid Email! Please enter a valid email address."))
        if data.get("phone"):
            try:
                raise_error = "phone" in mandatory_fields 
                res = session_appointment_id._format_phone_number(data.get("phone"), raise_error)
                data["phone"] = res
            except Exception as e:
                error["phone"] = "error"
                error_message.append(_("Invalid Phone! {}".format(e)))
        if data.get("mobile"):
            try:
                raise_error = "mobile" in mandatory_fields 
                res = session_appointment_id._format_phone_number(data.get("mobile"), raise_error)
                data["mobile"] = res
            except Exception as e:
                error["mobile"] = "error"
                error_message.append(_("Invalid Mobile! {}".format(e)))
        existing_partner = session_appointment_id._check_existing_duplicates(
            data.get("email"), data.get("mobile"), data.get("phone"), session_appointment_id.partner_id,
        )
        if existing_partner:
            error["email"] = "error"
            error["mobile"] = "error"
            error["phone"] = "error"
            error_message.append(_(
                "Sorry, but the user with the same email, phone, or mobile already exists! Please change or log in!" 
            ))            
        if [err for err in error.values() if err == "missing"]:
            error_message.append(_("Some required fields are empty."))
        values = {key: data[key] for key in all_fields if key in data}
        return error, error_message, values

    def _reservation_details_validate(self, data, rtype_id=None):
        """
        The method to check business.appointment core values

        Args:
         * data - dict of values
         * rtype_id - resource.type object

        Methods:
         * _return_mandatory_fields of appointment.contact info
         * _check_whether_user_is_not_public

        Returns:
         * dict if field names with errors
         * list of error
         * business.appointment.core values

        Extr info:
         * here all reservation custom fields are processed, that is why we have check for "filename"
        """
        reservation_obj = request.env["appointment.contact.info"].sudo()
        error = dict()
        error_message = []
        mandatory_fields, date_fields, binary_fields, bool_fields, ma2o_fields = reservation_obj._return_custom_fields(
            rtype_id
        )
        website_id = request.website
        public_user = self._check_whether_user_is_not_public()
        if request.website.ba_agree_to_terms_and_conditions \
                and (not public_user or not website_id.ba_agree_to_terms_public_only):
            mandatory_fields.append("agree_terms")
        for field_name in mandatory_fields:
            if not data.get(field_name):
                error[field_name] = "missing"
        contact_details = request.website._all_contact_fields + ["contact_name", "email"]
        values = {}
        for field_name, field_value in data.items():
            if field_name not in contact_details and hasattr(reservation_obj, field_name):
                if field_name in binary_fields:
                    # the check for file_name is required not to replace existing but not changed binaries
                    if hasattr(field_value, "filename"):
                        field_id = request.env["ir.model.fields"].sudo().search([
                            ("model", "=", "appointment.contact.info"), ("name", "=", field_name)
                        ], limit=1)
                        if field_id and field_id.ttype == "binary":
                            values.update({
                                field_name: base64.b64encode(field_value.read()),
                                field_name+"_filename": field_value.filename,
                            })
                    elif not field_value:
                        values.update({field_name: False, field_name + "_filename": False})
                elif field_name in ma2o_fields and field_value not in ["", False]:
                    values.update({field_name: int(field_value)})
                elif field_name in date_fields and field_value == "":
                    values.update({field_name: False})
                else:
                    values.update({field_name: field_value})
        for field_name in bool_fields:
            # since false checkboxes do not pass value from form
            if not data.get(field_name):
                values.update({field_name:False})
        if [err for err in error.values() if err == "missing"]:
            error_message.append(_("Some required fields are empty."))
        return error, error_message, values

    def _ba_finish_appointment(self, appointment_ids, session_appointment_id):
        """
        The method to define how appointment success should be finished

        Args:
         * appointment_ids - business.appointment object
         * session_appointment_id - int - website.business.appointment

        Methods:
         * _return_appointment_redirect_url of website
         * _check_whether_user_is_not_public
         * _create_portal_user of website.business.appointment
        """
        res = request.redirect("/")
        appoinment_url = request.website._return_appointment_redirect_url(appointment_ids)
        if self._check_whether_user_is_not_public():
            res = request.redirect(appoinment_url)  
        else:
            public_token_url = session_appointment_id._create_portal_user(request.website.company_id)
            values = {
                "single_appointment": len(appointment_ids) == 1 and True or False,
                "appointment_confirmation": ", ".join(appointment_ids.mapped("name")),
                "public_token_url": "{}&redirect={}".format(public_token_url, appoinment_url),
            }
            res = request.render("business_appointment_website.ba_public_thankyou", values)
        session_appointment_id.sudo().unlink()
        return res

    def _retrieve_custom_filters(self, param):
        """
        The method to return searchbar custom filters based on configuration

        Args:
         * param - char - key of related param

        Returns:
         * dict
        """
        custom_searchbar_filters = {}
        custom_filters_ids = request.website[param]
        for cfilter in custom_filters_ids:
            custom_searchbar_filters.update({
                "{}".format(cfilter.id): {"label": cfilter.name,  "domain": safe_eval(cfilter.domain)}
            })
        return custom_searchbar_filters

    def _retrive_custom_search_domain(self, search_in, search, param):
        """
        The method to construct domain based on configured custom searches

        Args:
         * search_in - char - input key of current search
         * search - char - input value of current search
         * param - char - key of related param

        Returns:
         * list of typles = RPR        
        """
        search_domain = False
        custom_search_ids = request.website[param]
        for csearch in custom_search_ids:
            field_id = csearch.sudo().custom_field_id
            field_name = field_id.name
            if search_in in (field_name,):
                field_type = field_id.ttype
                if field_type == "selection":
                    all_sel_values_ids = request.env["ir.model.fields.selection"].sudo().search([
                        ("field_id", "=", field_id.id), ("name", "ilike", search),
                    ])
                    if all_sel_values_ids:
                        search_domain = [(field_name, "in", all_sel_values_ids.mapped("value"))]
                    else:
                        search_domain = [("id", "=", 0)]
                else:
                    search_domain = [(field_name, "ilike", search)]
        return search_domain

    def _retrive_custom_search_inputs(self, param):
        """
        The method to return custom search inputs based on configs

        Args:
         * param - char - key of related param

        Returns:
         * dict   
        """
        searchbar_inputs = {}
        custom_search_ids = request.website[param]
        for csearch in custom_search_ids:
            try:
                searchbar_inputs.update({
                    "{}".format(csearch.sudo().custom_field_id.name): {
                        "input": csearch.sudo().custom_field_id.name, "label": csearch.name,
                    }
                })
            except:
                # for the case when field was removed
                continue
        return searchbar_inputs

    ####################################################################################################################
    ######################################## Helpers for searches  #####################################################
    ####################################################################################################################
    def _step1_return_search_in(self, search_in, search):
        """
        The method to prepare domain base on search (resource types)

        Args:
         * search_in - char
         * search - char

        Methods:
         * _retrive_custom_search_domain

        Returns:
         * list - domain to search
        """
        search_domain = []
        if search_in in ("name"):
            search_domain =  [("name", "ilike", search)]
        if search_in in ("description"):
            search_domain = [("description", "ilike", search)]
        if search_in in ("final_service_ids"):
            search_domain = [("final_service_ids", "ilike", search)]
        search_domain = self._retrive_custom_search_domain(search_in, search, "ba_rtypes_portal_search_ids") \
            or search_domain
        return search_domain
    
    def _step1_return_inputs(self):
        """
        The method to prepare search inputs for resource types

        Methods:
         * _retrive_custom_search_inputs

        Returns:
         * dict
        """
        searchbar_inputs = {
            "name": {"input": "name", "label": _("By name")},
            "description": {"input": "description", "label": _("In description")},
            "final_service_ids": {"input": "final_service_ids", "label": _("In services")},
        }
        searchbar_inputs.update(self._retrive_custom_search_inputs("ba_rtypes_portal_search_ids"))
        return searchbar_inputs

    def _step2_return_search_in(self, search_in, search):
        """
        The method to prepare domain base on search (resources)

        Args:
         * search_in - char
         * search - char

        Methods:
         * _retrive_custom_search_domain

        Returns:
         * list - domain to search
        """
        search_domain = []
        if search_in in ("name"):
            search_domain =  [("name", "ilike", search)]
        if search_in in ("description"):
            search_domain = [("description", "ilike", search)]
        if search_in in ("final_service_ids"):
            search_domain = [("final_service_ids", "ilike", search)]
        search_domain = self._retrive_custom_search_domain(search_in, search, "ba_resources_portal_search_ids") \
            or search_domain
        return search_domain

    def _step2_return_inputs(self):
        """
        The method to prepare search inputs for resources

        Methods:
         * _retrive_custom_search_inputs

        Returns:
         * dict
        """
        searchbar_inputs = {
            "name": {"input": "name", "label": _("By name")},
            "description": {"input": "description", "label": _("In description")},
            "final_service_ids": {"input": "final_service_ids", "label": _("In services")},
        }
        searchbar_inputs.update(self._retrive_custom_search_inputs("ba_resources_portal_search_ids"))
        return searchbar_inputs

    def _step3_return_search_in(self, search_in, search):
        """
        The method to prepare domain base on search (services)

        Args:
         * search_in - char
         * search - char

        Methods:
         * _retrive_custom_search_domain

        Returns:
         * list - domain to search
        """
        search_domain = []
        if search_in in ("name"):
            search_domain =  [("name", "ilike", search)]
        if search_in in ("description"):
            search_domain = [("ba_description", "ilike", search)]
        search_domain = self._retrive_custom_search_domain(search_in, search, "ba_service_portal_search_ids") \
            or search_domain
        return search_domain

    def _step3_return_inputs(self):
        """
        The method to prepare search inputs for services

        Methods:
         * _retrive_custom_search_inputs

        Returns:
         * dict
        """
        searchbar_inputs = {
            "name": {"input": "name", "label": _("By name")},
            "description": {"input": "ba_description", "label": _("In description")},
        }
        searchbar_inputs.update(self._retrive_custom_search_inputs("ba_service_portal_search_ids"))
        return searchbar_inputs

    def _portal_appointments_return_search_in(self, search_in, search):
        """
        The method to prepare domain base on search (portal appointments)

        Args:
         * search_in - char
         * search - char

        Methods:
         * _retrive_custom_search_domain

        Returns:
         * list - domain to search
        """
        search_domain = []
        if search_in in ("name"):
            search_domain =  [("name", "ilike", search)]
        if search_in in ("resource_id"):
            search_domain =  [("resource_id.name", "ilike", search)]
        if search_in in ("service_id"):
            search_domain =  [("service_id.name", "ilike", search)]
        if search_in in ("resource_type_id"):
            search_domain =  [("resource_type_id.name", "ilike", search)]
        search_domain = self._retrive_custom_search_domain(search_in, search, "ba_portal_appointments_search_ids") \
            or search_domain
        return search_domain

    def _portal_appointments_return_inputs(self):
        """
        The method to prepare search inputs for portal appointments

        Methods:
         * _retrive_custom_search_inputs

        Returns:
         * dict
        """
        searchbar_inputs = {
            "name": {"input": "name", "label": _("by reference")},
            "resource_id": {"input": "resource_id", "label": _("by resource")},
            "service_id": {"input": "service_id", "label": _("by service")},
            "resource_type_id": {"input": "resource_type_id", "label": _("by resource type")},
        }
        searchbar_inputs.update(self._retrive_custom_search_inputs("ba_portal_appointments_search_ids"))
        return searchbar_inputs

    ####################################################################################################################
    ######################################## Helpers for filterings  ###################################################
    ####################################################################################################################
    def _step1_return_filters(self):
        """
        The method to prepare filters for resource types

        Methods:
         * _retrieve_custom_filters

        Returns:
         * dict
        """
        searchbar_filters = {"all": {"label": _("All"), "domain": []},}
        searchbar_filters.update(self._retrieve_custom_filters("ba_rtypes_portal_filters_ids"))
        return searchbar_filters

    def _step2_return_filters(self):
        """
        The method to prepare filters for resources

        Methods:
         * _retrieve_custom_filters

        Returns:
         * dict
        """
        searchbar_filters = {"all": {"label": _("All"), "domain": []},}
        searchbar_filters.update(self._retrieve_custom_filters("ba_resources_portal_filters_ids"))
        return searchbar_filters

    def _step3_return_filters(self):
        """
        The method to prepare filters for services

        Methods:
         * _retrieve_custom_filters

        Returns:
         * dict
        """
        searchbar_filters = {"all": {"label": _("All"), "domain": []},}
        searchbar_filters.update(self._retrieve_custom_filters("ba_services_portal_filters_ids"))
        return searchbar_filters

    def _portal_appointments_return_filters(self):
        """
        The method to prepare filters for services

        Methods:
         * _retrieve_custom_filters

        Returns:
         * dict
        """
        searchbar_filters = {
            "all": {"label": _("All"), "domain": []},
            "planned": {
                "label": _("Planned"), 
                "domain": [("datetime_end", ">=", fields.Datetime.now()), ("state", "=", "reserved")]
            },
        }
        searchbar_filters.update(self._retrieve_custom_filters("ba_portal_appointments_filters_ids"))
        return searchbar_filters

    ####################################################################################################################
    ######################################## Helpers for sortings  #####################################################
    ####################################################################################################################
    def _step1_return_sortings(self):
        """
        The method to prepare possible sortings for resource types

        Returns:
         * dict of values
        """
        searchbar_sortings = {
            "sequence": {"label": _("Standard"), "order": "sequence, id"},
            "name": {"label": _("A-Z"), "order": "name ASC, sequence, id"},
            "name_backward": {"label": _("Z-A"), "order": "name DESC, sequence, id"},
        }
        return searchbar_sortings

    def _step2_return_sortings(self):
        """
        The method to prepare possible sortings for resources

        Returns:
         * dict of values
        """
        searchbar_sortings = {
            "sequence": {"label": _("Standard"), "order": "sequence, id"},
            "name": {"label": _("A-Z"), "order": "name ASC, sequence, id"},
            "name_backward": {"label": _("Z-A"), "order": "name DESC, sequence, id"},
        }
        return searchbar_sortings

    def _step3_return_sortings(self):
        """
        The method to prepare possible sortings for services

        Returns:
         * dict of values
        """
        searchbar_sortings = {
            "name": {"label": _("A-Z"), "order": "name ASC, id"},
            "name_backward": {"label": _("Z-A"), "order": "name DESC, id"},
        }
        return searchbar_sortings

    def _portal_appointments_return_sortings(self):
        """
        The method to prepare possible sortings for portal appointments

        Returns:
         * dict of values
        """
        searchbar_sortings = {
            "day_date": {"label": _("Date"), "order": "day_date DESC, id"},
            "resource_id": {"label": _("Resource"), "order": "resource_id DESC, id"},
            "service_id": {"label": _("Service"), "order": "service_id DESC, id"},
            "resource_type_id": {"label": _("Resource Type"), "order": "resource_type_id DESC, id"},
        }
        return searchbar_sortings

    ####################################################################################################################
    ################################### Helpers to prepare main route values############################################
    ####################################################################################################################
    def _step1_prepare_values(self, session_appointment_id, durl="", page=1, sortby=None, filterby=None, search=None, 
        search_in="name", **kw):
        """
        The method to prepare values for business resource types

        Args:
         * session_appointment_id -  website.business.appointment
         * durl - str 
         * page - int
         * sortby - char
         * filterby - char
         * search - char
         * search_in - char

        Methods:
         * _step1_return_sortings
         * _step1_return_filters
         * _step1_return_inputs
         * _step1_return_search_in

        Returns:
         * dict of values
        """
        website_id = request.website
        domain = [("id", "in", session_appointment_id.all2choose_rtype_ids.ids)]
        rtype_object = request.env["business.resource.type"]
        sortby = sortby or "sequence"
        filterby = filterby or "all"     
        searchbar_sortings = self._step1_return_sortings()
        searchbar_filters = self._step1_return_filters()
        searchbar_inputs = self._step1_return_inputs()
        domain += searchbar_filters[filterby]["domain"]
        if search and search_in:
            domain += self._step1_return_search_in(search_in, search)
        ba_types_count = rtype_object.search_count(domain)
        pager = portal_pager(
            url=durl,
            url_args={"sortby": sortby, "filterby": filterby, "search": search, "search_in": search_in},
            total=ba_types_count,
            page=page,
            step=self._items_per_page,
        )
        resource_types = rtype_object.search(
            domain,
            order=searchbar_sortings[sortby]["order"],
            limit=self._items_per_page,
            offset=pager["offset"],
        )
        show_full_details = website_id.show_ba_rtypes_full_details
        values = {
            "resource_types": resource_types,
            "pager": pager,
            "searchbar_sortings": searchbar_sortings,
            "searchbar_inputs": searchbar_inputs,
            "search_in": search_in,
            "sortby": sortby,
            "searchbar_filters": OrderedDict(sorted(searchbar_filters.items())),
            "filterby": filterby,
            "done_filters": filterby != "all" and searchbar_filters[filterby]["label"] or False,
            "done_search": search or False,
            "show_full_details": show_full_details,
        }
        return values

    def _step2_prepare_values(self, session_appointment_id, durl="", page=1, sortby=None, filterby=None, search=None, 
        search_in="name", **kw):
        """
        The method to prepare values for business resources

        Args:
         * session_appointment_id -  website.business.appointment
         * durl - str 
         * page - int
         * sortby - char
         * filterby - char
         * search - char
         * search_in - char

        Methods:
         * _step2_return_sortings
         * _step2_return_filters
         * _step2_return_inputs
         * _step2_return_search_in

        Returns:
         * dict of values
        """
        website_id = request.website
        all2choose_resource_ids = session_appointment_id.url_ba_type_id._return_viable_resources(website_id)
        domain = [("id", "in", all2choose_resource_ids.ids),]
        resource_object = request.env["business.resource"]
        sortby = sortby or "sequence"
        filterby = filterby or "all"     
        searchbar_sortings = self._step2_return_sortings()
        searchbar_filters = self._step2_return_filters()
        searchbar_inputs = self._step2_return_inputs()
        domain += searchbar_filters[filterby]["domain"]
        if search and search_in:
            domain += self._step2_return_search_in(search_in, search)
        all_resources = resource_object.search(domain).ids
        ba_resource_count = len(all_resources)
        pager = portal_pager(
            url=durl,
            url_args={"sortby": sortby, "filterby": filterby, "search": search, "search_in": search_in},
            total=ba_resource_count,
            page=page,
            step=self._items_per_page,
        )
        resources = resource_object.search(
            domain,
            order=searchbar_sortings[sortby]["order"],
            limit=self._items_per_page,
            offset=pager["offset"],
        )
        values = {
            "all_resources": all_resources,
            "resources": resources,
            "pager": pager,
            "searchbar_sortings": searchbar_sortings,
            "searchbar_inputs": searchbar_inputs,
            "search_in": search_in,
            "sortby": sortby,
            "searchbar_filters": OrderedDict(sorted(searchbar_filters.items())),
            "filterby": filterby,
            "done_filters": filterby != "all" and searchbar_filters[filterby]["label"] or False,
            "done_search": search or False,
            "return_resources_subset": return_resources_subset,
            "return_resources_set": return_resources_set,
            "show_full_details": website_id.show_ba_resource_full_details,
        }
        return values

    def _step3_prepare_values(self, session_appointment_id, durl="", page=1, sortby=None, filterby=None, search=None, 
        search_in="name", **kw):
        """
        The method to prepare values for services

        Args:
         * session_appointment_id -  website.business.appointment
         * durl - str 
         * page - int
         * sortby - char
         * filterby - char
         * search - char
         * search_in - char

        Methods:
         * _step3_return_sortings
         * _step3_return_filters
         * _step3_return_inputs
         * _step3_return_search_in
         * _get_extra_options_ba_values

        Returns:
         * dict of values
        """
        website_id = request.website
        service_object = request.env["appointment.product"]
        service_ids = session_appointment_id.url_resource_ids._return_viable_services(website_id)
        domain = [("id", "in", service_ids.ids),]
        sortby = sortby or "name"
        filterby = filterby or "all"     
        searchbar_sortings = self._step3_return_sortings()
        searchbar_filters = self._step3_return_filters()
        searchbar_inputs = self._step3_return_inputs()
        domain += searchbar_filters[filterby]["domain"]
        if search and search_in:
            domain += self._step3_return_search_in(search_in, search)
        ba_services_count = service_object.search_count(domain)
        pager = portal_pager(
            url=durl,
            url_args={"sortby": sortby, "filterby": filterby, "search": search, "search_in": search_in},
            total=ba_services_count,
            page=page,
            step=self._items_per_page,
        )
        services = service_object.search(
            domain,
            order=searchbar_sortings[sortby]["order"],
            limit=self._items_per_page,
            offset=pager["offset"],
        )
        values = {
            "services": services,
            "pager": pager,
            "searchbar_sortings": searchbar_sortings,
            "searchbar_inputs": searchbar_inputs,
            "search_in": search_in,
            "sortby": sortby,
            "searchbar_filters": OrderedDict(sorted(searchbar_filters.items())),
            "filterby": filterby,
            "done_filters": filterby != "all" and searchbar_filters[filterby]["label"] or False,
            "done_search": search or False,
            "show_full_details": website_id.show_ba_services_full_details,
            "session_appointment_id": session_appointment_id,
        }
        values.update(self._get_extra_options_ba_values())
        return values

    def _step4_prepare_values(self, session_appointment_id, durl="", **kw):
        """
        The method to prepare values for slots

        Args:
         * session_appointment_id -  website.business.appointment
         * durl - str 

        Returns:
         * dict of values
        
        Extra info
         * we need pager to avoid portal layout calculations error
        """
        return {"pager": portal_pager(url=durl, url_args={}, total=1, page=1, step=self._items_per_page)}

    def _step5_prepare_values(self, session_appointment_id, durl="", **kw):
        """
        The method to prepare account details page

        Args:
         * session_appointment_id -  website.business.appointment
         * durl - str 

        Methods:
         * _return_website_ba_contact_fields of website
         * _return_contact_info of website.business.appointment
         * _check_whether_user_is_not_public

        Returns:
         * dict of values
        """
        website_id = request.website
        public_user = self._check_whether_user_is_not_public()
        ba_sign_in_type = not public_user and (website_id.ba_sign_in_type or "optional") or "no"
        if ba_sign_in_type == "required":
            return {"redirect_login": "/web/login?redirect=/appointments/5?progress_step=5"}
        all_fields, mandatory_fields = request.website._return_website_ba_contact_fields()
        values = session_appointment_id._return_contact_info()
        if session_appointment_id.error:
            values.update({
                "error": safe_eval(session_appointment_id.error and session_appointment_id.error) or {},
                "error_message": session_appointment_id.error_message \
                    and safe_eval(session_appointment_id.error_message) or [],
            })
            values.update(session_appointment_id.error_vals and safe_eval(session_appointment_id.error_vals) or {})
        else:
            values.update({"error": {}, "error_message": []})
        if "country_id" in all_fields:
            values.update({"countries": request.env["res.country"].sudo().search([]),})
        if "state_id" in all_fields:
            values.update({"states": request.env["res.country.state"].sudo().search([]),})
        if "title" in all_fields:
            values.update({"titles": request.env["res.partner.title"].sudo().search([]),})
        if website_id.ba_agree_to_terms_and_conditions and (not public_user \
                or not website_id.ba_agree_to_terms_public_only):
            values.update({"agree_terms_text": Markup(website_id.ba_agree_to_terms_text)})
        pager = portal_pager(url=durl, url_args={}, total=1, page=1, step=self._items_per_page,)
        values.update({
            "ba_sign_in_type": ba_sign_in_type,
            "ba_sign_in_type_text": ba_sign_in_type == "optional" and Markup(website_id.ba_sign_in_type_text) or "",
            "all_fields": all_fields,
            "mandatory_fields": mandatory_fields,
            "pager": pager, # to avoid portal layout calculations error
            "resource_type_id": session_appointment_id.url_ba_type_id.id,
        })
        return values

    def _step6_prepare_values(self, session_appointment_id, durl="", **kw):
        """
        The method to prepare confirmation page

        Args:
         * session_appointment_id -  website.business.appointment
         * durl - str 

        Returns:
         * dict of values
        """
        pager = portal_pager(url=durl, url_args={}, total=1, page=1, step=self._items_per_page,)
        values = {"pager": pager,}
        if session_appointment_id.error:
            values.update({
                "error": safe_eval(session_appointment_id.error and session_appointment_id.error) or {},
                "error_message": session_appointment_id.error_message \
                    and safe_eval(session_appointment_id.error_message) or [],
            })
            session_appointment_id.write({"error": False, "error_message": False, "error_vals": False})
        else:
            values.update({"error": {}, "error_message": []})
        return values        

    def _prepare_vals_portal_appointments(self,  page=1, sortby=None, filterby=None, search=None, search_in="name", 
        **kw):
        """
        The method to prepare values for appointments

        Args:
         * page - int
         * sortby - char
         * filterby - char
         * search - char
         * search_in - char

        Methods:
         * _prepare_portal_layout_values
         * _portal_appointments_return_sortings
         * _portal_appointments_return_filters
         * _portal_appointments_return_inputs
         * _portal_appointments_return_search_in

        Returns:
         * dict of values
        """
        default_url = "/my/business/appointments"
        values = self._prepare_portal_layout_values()
        website_id = request.website
        appointment_object = request.env["business.appointment"]
        com_partner_id = request.env.user.partner_id.id
        domain = [("partner_id", "=", com_partner_id)]
        sortby = sortby or "day_date"
        filterby = filterby or "planned"     
        searchbar_sortings = self._portal_appointments_return_sortings()
        searchbar_filters = self._portal_appointments_return_filters()
        searchbar_inputs = self._portal_appointments_return_inputs()
        domain += searchbar_filters[filterby]["domain"]
        if search and search_in:
            domain += self._portal_appointments_return_search_in(search_in, search)
        ba_appointment_count = appointment_object.search_count(domain)
        pager = portal_pager(
            url=default_url,
            url_args={"sortby": sortby, "filterby": filterby, "search": search, "search_in": search_in},
            total=ba_appointment_count,
            page=page,
            step=self._items_per_page,
        )
        appointments = appointment_object.search(
            domain,
            order=searchbar_sortings[sortby]["order"],
            limit=self._items_per_page,
            offset=pager["offset"]            
        )
        values.update({
            "page_name": "My Appointments",
            "default_url": default_url,
            "appointments": appointments,
            "pager": pager,
            "searchbar_sortings": searchbar_sortings,
            "searchbar_inputs": searchbar_inputs,
            "search_in": search_in,
            "sortby": sortby,
            "searchbar_filters": OrderedDict(sorted(searchbar_filters.items())),
            "filterby": filterby,
            "done_filters": filterby not in ["all"] and searchbar_filters[filterby]["label"] or False,
            "done_search": search or False,
        })
        request.session["all_appointments"] = appointments.ids[:100]
        return values

    def _prepare_full_appointment_vals(self, appointment_id):
        """
        Method to pass values by business.appointment

        Args:
         * appointment_id - business.appointment object

        Returns:
         * dict
        """
        vals = self._prepare_portal_layout_values()
        vals.update({
            "ba_appointment_id": appointment_id,
            "page_name": appointment_id.name,
            "extra_products_option": request.website.ba_extra_products_frontend,
        })
        history = request.session.get("all_appointments", [])
        vals.update(get_records_pager(history, appointment_id))
        if appointment_id.success:
            vals.update({"success": appointment_id.success,})
            appointment_id.sudo().write({"success": False,})
        if appointment_id.error:
            vals.update({"error": appointment_id.error,})
            appointment_id.sudo().write({"error": False,})
        return vals

    ####################################################################################################################
    ############################################### ROUTES #############################################################
    ####################################################################################################################
    @http.route(["/appointments", "/appointments/page/<int:page>", "/appointments/<int:active_step>",
        "/appointments/<int:active_step>/page/<int:page>"], type="http", auth="public", website=True)
    def ba_super_controller(self, active_step=None, url_ba_type_id=None, url_resource_ids=None, url_service_id=None, 
        progress_step=None, confirmation_code=None, page=1, sortby=None, filterby=None, search=None, search_in="name", 
        **kw):
        """
        The controller to define at which step we are and route to the required template
        It is the MOST IMPORTANT CONTROLLER to manage all redirects

        Args:
         * active_step - int
         * url_ba_type_id - int - business.resource.type ID
         * url_resource_ids - str - represents list of business.resource.object ids [1,2]
         * url_service_id - int - business.resource ID
         * progress_step - int 
         * confirmation_code - str (mainly used to go from the email)
         * page - int
         * sortby - char
         * filterby - char
         * search - char
         * search_in - char

        Methods:
         * _check_ba_portal_user_rights 
         * _prepare_session_order
         * _check_and_adapt_session_order   
         * _step1_prepare_values
         * _step2_prepare_values
         * _step3_prepare_values
         * _step4_prepare_values
         * _step5_prepare_values

        Returns:
         * rendered page
        """
        values = self._check_ba_portal_user_rights()
        session_appointment_id = self._prepare_session_order()   
        session_values = session_appointment_id._check_and_adapt_session_order(
            request.website, active_step, url_ba_type_id, url_resource_ids, url_service_id, progress_step
        )
        if session_values is None:
            session_appointment_id.sudo().unlink()
            return request.redirect("/appointments")
        else:
            values.update(session_values)
        active_step = session_appointment_id.active_step
        durl = values.get("default_url")       
        if active_step == 1:
            values.update(self._step1_prepare_values(
                session_appointment_id, durl=durl, page=page, sortby=sortby, filterby=filterby, search=search, 
                search_in=search_in, kw=kw,
            ))
            res = request.render("business_appointment_website.ba_appointments", values)
        elif active_step == 2:           
            values.update(self._step2_prepare_values(
                session_appointment_id, durl=durl, page=page, sortby=sortby, filterby=filterby, search=search, 
                search_in=search_in, kw=kw,
            ))
            res = request.render("business_appointment_website.ba_resources", values)
        elif active_step == 3:           
            values.update(self._step3_prepare_values(
                session_appointment_id, durl=durl, page=page, sortby=sortby, filterby=filterby, search=search,
                search_in=search_in, kw=kw,
            ))
            res = request.render("business_appointment_website.ba_services", values)
        elif active_step == 4:
            values.update(self._step4_prepare_values(session_appointment_id, durl=durl, kw=kw))
            res = request.render("business_appointment_website.ba_time_slots", values)
        elif active_step == 5:
            values.update(self._step5_prepare_values(session_appointment_id, durl=durl, kw=kw))
            if values.get("redirect_login"):
                # the public user should log in
                return request.redirect(values.get("redirect_login"))
            res = request.render("business_appointment_website.ba_contact_info", values)
        elif active_step == 6:
            if 6 in values.get("hidden_steps"):
                res = self.ba_account_confirm(noconfirmation_code=True,) 
            elif confirmation_code:
                res = self.ba_account_confirm(confirmation_code=confirmation_code,)
            else:
                values.update(self._step6_prepare_values(session_appointment_id, durl=durl, kw=kw))
                res = request.render("business_appointment_website.ba_confirmation_page", values)
        else:
            raise werkzeug.exceptions.NotFound()
        # to make sure the controller would work even in case of the button move and forward
        res.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        res.headers["Pragma"] = "no-cache"
        res.headers["Expires"] = "0"
        return res

    @http.route(["/appointments/account"], type="http", auth="public", methods=["POST"], website=True)
    def ba_account_details(self, **post):
        """
        The route to create partner / update current partner contact details

        Methods:
         * _check_ba_portal_user_rights
         * _prepare_session_order
         * _check_reservations
         * _contact_details_validate
         * _reservation_details_validate
         * _update_session_contact_details of website.business.appointment

        Returns:
         * if error - page with errors
         * otherwise redirect to the new step

        Extra info:
         * even here we check for reservations expiration for the location reload did not take place
         * we keep vals in both website.order and reservations. The former is required to recover values when 
           reservations are cancelled in the process of scheduling
        """
        values = self._check_ba_portal_user_rights()
        session_appointment_id = self._prepare_session_order() 
        miss1, miss2, four_step = session_appointment_id._check_reservations(
            session_appointment_id.url_resource_ids, session_appointment_id.url_service_id
        )
        if four_step and not request.params.get('x_oz_cbaf_3') and not request.params.get('email'):
            res = request.redirect("/appointments/4?progress_step=4")
        else:
            error, error_message, contact_values = self._contact_details_validate(session_appointment_id, post)
            values.update(contact_values)
            r_error, r_error_message, reservation_vals = self._reservation_details_validate(
                request.params, session_appointment_id.url_ba_type_id,
            )
            values.update(reservation_vals)
            error.update(r_error)
            error_message += r_error_message
            if error:
                error_vals = {}
                for key, val in error.items():
                    if key in ["agree_terms", "email", "phone", "mobile"]:
                        # to save them and show after reload, but not write. Not all fields, since binary are not safe eval
                        error_vals.update({key: values.get(key)})             
                    if values.get(key):
                        # we do not write fields with errors
                        del values[key]
                values.update({
                    "error": error,
                    "error_message": error_message,
                    "error_vals": error_vals,
                })
                session_appointment_id._update_session_contact_details(values, False)
                res = request.redirect("/appointments/5?progress_step=5")
            else:
                values.update({
                    "error": False,
                    "error_message": False,
                    "error_vals": False,
                    "website_id": request.website.id,
                })
                session_appointment_id._update_session_contact_details(values, True)
                res = request.redirect("/appointments/6?progress_step=6")
        return res

    @http.route(["/appointments/confirm"], type="http", auth="public", website=True)
    def ba_account_confirm(self, confirmation_code=False, noconfirmation_code=False, **post):
        """
        The route to finish reservation 

        Methods:
         * _check_ba_portal_user_rights
         * _prepare_session_order
         * _check_reservations
         * _update_session_confirmation
         * _ba_finish_appointment
        """
        values = self._check_ba_portal_user_rights()
        session_appointment_id = self._prepare_session_order()
        miss1, miss2, four_step = session_appointment_id._check_reservations(
            session_appointment_id.url_resource_ids, session_appointment_id.url_service_id
        )
        if four_step:
            res = request.redirect("/appointments/4?progress_step=4")
        else:
            confirmation_code = confirmation_code or post.get("confirmation_code")
            error = dict()
            error_message = []
            if not noconfirmation_code and (not confirmation_code \
                    or confirmation_code != session_appointment_id.confirmation_code):
                error["confirmation_code"] = "error"
                error_message.append(_("Confirmation code is not valid!"))
            if error:
                values.update({"error": error, "error_message": error_message})
                session_appointment_id._update_session_confirmation(values, False)
                res = request.redirect("/appointments/6?progress_step=6")
            else:
                values.update({"error": False, "error_message": False})
                appointment_ids, error_internal = session_appointment_id._update_session_confirmation(values, True)
                if error_internal:
                    redirect_step = noconfirmation_code and 5 or 6
                    res = request.redirect("/appointments/{}?progress_step={}".format(redirect_step, redirect_step))                
                else:
                    res = self._ba_finish_appointment(appointment_ids, session_appointment_id)
        return res

    @http.route(["/appointments/resend"], type="http", auth="public", website=True)
    def ba_appointments_resend(self):
        """
        The method to resend code

        Methods:
         * _check_ba_portal_user_rights
         * _prepare_session_order
         * _update_confirmation_code
         * _caclulate_expiration_timer
        """
        values = self._check_ba_portal_user_rights()
        session_appointment_id = self._prepare_session_order()
        if session_appointment_id._caclulate_expiration_timer() <= 0 \
                and session_appointment_id.confirmation_refresh_attempts >= 0:
            session_appointment_id._update_confirmation_code()
        res = request.redirect("/appointments/6?progress_step=6")
        return res

    @http.route(["/appointments/types/<model('business.resource.type'):rtype_id>"], type="http", auth="public", 
        website=True)
    def business_resource_type_full_details(self, rtype_id=None, **kw):
        """
        The route to open the article page

        Args:
         * rtype_id - business.resource.type record

        Methods:
         * _check_ba_portal_user_rights
         * _return_check_viable of business.resource.type

        Returns:
         * rendered page

        Extra info:
         * we check publicity only for external users, since there should be a way to update full details for
           internal users 
        """
        values = self._check_ba_portal_user_rights()
        if not rtype_id:
            raise werkzeug.exceptions.NotFound()
        if not request.env.user.has_group("base.group_user"):
            website_id = request.website
            show_full_details = website_id.show_ba_rtypes_full_details
            if not rtype_id._return_check_viable(website_id) or not show_full_details \
                    or rtype_id.donotshow_full_description:
                raise werkzeug.exceptions.NotFound()
        values.update({
            "main_object": rtype_id,
            "page_name": "{}".format(rtype_id.name),
        })
        res = request.render("business_appointment_website.ba_resource_type_full", values)
        return res

    @http.route(["/appointments/resources/<model('business.resource'):resource_id>"], type="http", auth="public", 
        website=True)
    def business_resources_full_details(self, resource_id=None, **kw):
        """
        The route to open the article page

        Args:
         * resource_id - business.resource record

        Methods:
         * _check_ba_portal_user_rights
         * _return_check_viable of business.resource

        Returns:
         * rendered page

        Extra info:
         * we check publicity only for external users, since there should be a way to update full details for
           internal users          
        """
        values = self._check_ba_portal_user_rights()      
        if not resource_id:
            raise werkzeug.exceptions.NotFound()
        if not request.env.user.has_group("base.group_user"):
            website_id = request.website
            show_full_details = website_id.show_ba_resource_full_details
            if not resource_id._return_check_viable(website_id) or not show_full_details \
                    or resource_id.donotshow_full_description:
                raise werkzeug.exceptions.NotFound()        
        values.update({"main_object": resource_id, "page_name": "{}".format(resource_id.name)})
        res = request.render("business_appointment_website.ba_resource_full", values)
        return res

    @http.route(["/appointments/services/<model('appointment.product'):service_id>"], type="http", auth="public", 
        website=True)
    def business_service_full_details(self, service_id=None, **kw):
        """
        The route to open the article page

        Args:
         * service_id - appointment.product record

        Methods:
         * _check_ba_portal_user_rights
         * _return_check_viable
         * _get_extra_options_ba_values

        Returns:
         * rendered page of appointment.product

        Extra info:
         * we check publicity only for external users, since there should be a way to update full details for
           internal users  
        """
        values = self._check_ba_portal_user_rights()       
        if not service_id:
            raise werkzeug.exceptions.NotFound()
        if not request.env.user.has_group("base.group_user"):
            website_id = request.website
            show_full_details = website_id.show_ba_services_full_details
            if not service_id._return_check_viable(website_id, website_id.company_id) \
                    or not show_full_details or service_id.donotshow_full_description:
                raise werkzeug.exceptions.NotFound()
        values.update({"main_object": service_id, "page_name": "{}".format(service_id.name)})
        values.update(self._get_extra_options_ba_values())
        res = request.render("business_appointment_website.ba_products_full", values)
        return res

    ####################################################################################################################
    ############################################### JS methods for widgets #############################################
    ####################################################################################################################
    @http.route(["/appointments/prereserve"], type="json", auth="public", methods=["POST"], website=True, csrf=False)
    def save_prereservations_to_session(self, core_id, remove=False):
        """
        The method to save bussiness.appointment.core changes to the session: either added or cancelled

        Arg:
         * core_id - int
         * remove - bool - True if slot should be unreserver

        Methods:
         * _prepare_session_order

        Returns:
         * website.business.appointment record
        """
        session_appointment_id = self._prepare_session_order()
        session_appointment_id.sudo().url_reservation_ids = [(remove and 3 or 4, core_id)]
        return session_appointment_id
    
    @http.route(["/appointments/get/session"], type="json", auth="public", methods=["POST"], website=True, csrf=False)
    def get_slots_session(self):
        """
        The method to get session values required for the time slots widget

        Methods:
         * _prepare_session_order
         * _return_number_of_appointments_portal of business.resource.type
         * _get_appointment_pricelist_id (introduced only within business_appointment_website_sale)

        Returns:
         * dict
        """
        session_appointment_id = self._prepare_session_order()
        max_appoints = request.env["business.resource.type"]._return_number_of_appointments_portal(request.website)
        pricelist_id = False
        if hasattr(self, "_get_appointment_pricelist_id"):
            pricelist_id = self._get_appointment_pricelist_id(session_appointment_id)
        return {
            "fromWebsite": request.website.id,
            "resourceTypeID": session_appointment_id.url_ba_type_id.id,
            "resourceIDS": session_appointment_id.url_resource_ids.ids,
            "serviceID": session_appointment_id.url_service_id.id,
            "pricelistID": pricelist_id,
            "appointmentId": session_appointment_id.resechedule_id.id,
            "numberOfAppointments": max_appoints,
            "chosenAppointments": session_appointment_id.url_reservation_ids.mapped(lambda core: {
                "id": core.sudo().id,
                "title": core.sudo().resource_id.name, # here we just pass resource name, it will be recalculated then
            }),
        }

    @http.route(["/appointments/prereservation_timer"], type="json", auth="public", methods=["POST"], website=True, csrf=False)
    def get_prereservation_timer(self):
        """
        The method to check prereservation time and make sure reservations are still possible

        Methods:
         * _prepare_session_order
         * return_prereservation_timer

        Returns:
         * int
        """
        session_appointment_id = self._prepare_session_order()
        return session_appointment_id.return_prereservation_timer()

    ####################################################################################################################
    ############################################### Portal routes ######################################################
    ####################################################################################################################
    @http.route(["/my/business/appointments", "/my/business/appointments/page/<int:page>"], type="http", auth="user",
        website=True)
    def business_appointments_list_portal(self, page=1, sortby=None, filterby=None, search=None, search_in="name", 
        **kw):
        """
        The route to open the list of business.appointments
        """
        values = self._prepare_vals_portal_appointments(
            page=page, sortby=sortby, filterby=filterby, search=search, search_in=search_in, **kw,
        )
        if values.get("ba_turn_on_appointments"):
            res = request.render("business_appointment_website.portal_appointments", values)
        else:
            res = request.render("http_routing.403")
        return res

    @http.route(["/my/business/appointments/<model('business.appointment'):appointment_id>"], type="http", auth="user", 
        website=True)
    def portal_my_ba_appointment(self, appointment_id=None, **kw):
        """
        The route to open full appoinment page

        Returns:
         * rendered page
        """
        values = self._prepare_full_appointment_vals(appointment_id=appointment_id)
        if values.get("ba_turn_on_appointments"):
            res = request.render("business_appointment_website.portal_appointment_page", values)
        else:
            res = request.render("http_routing.403")
        return res

    @http.route(["/my/business/appointments/join_video"], type="json", auth="user", methods=["POST"], website=True, 
        csrf=False)
    def join_video_ba_appointment(self, appointment_id):
        """
        The method to open appointment video

        Args:
         * appointment_id - int - id of business.appointment

        Returns:
         * string (video URL)
        """
        appointment = request.env["business.appointment"].search([("id", "=", appointment_id)], limit=1)
        res = appointment and appointment.videocall or False
        return res

    @http.route(["/my/business/appointments/reschedule"], type="json", auth="user", methods=["POST"], website=True, 
        csrf=False)
    def reschedule_ba_appointment(self, appointment_id, should_be_cancelled=True):
        """
        The method to adapt session to existing appointment and get new scheduling for its params

        Args:
         * appointment_id - int - id of rescheduled business.appointment
         * should_be_cancelled - bool - wether re-scehduled appointment should be cancelled

        Methods:
         * _prepare_session_order
         * action_cancel_prereserv of business.appointment.core
         * _return_appointment_values of appointment.contact.info
        """
        session_id = self._prepare_session_order()
        appointment = request.env["business.appointment"].search([("id", "=", appointment_id)], limit=1)
        session_id.url_reservation_ids.action_cancel_prereserv()
        new_session_vals = {
            "url_ba_type_id": appointment.resource_type_id.id,
            "url_resource_ids": [(6, 0, [appointment.resource_id.id])],
            "url_service_id": appointment.service_id.id,
            "url_reservation_ids": [(6, 0, [])],
            "resechedule_id": should_be_cancelled and appointment_id or False,
            "progress_step": 4,
            "active_step": 4,
            "confirmation_attempts": 0,
            "confirmation_refresh_attempts": 0,
        }
        new_session_vals.update(appointment._return_appointment_values(pure_values=True, tosession=True))
        session_id.write(new_session_vals)
        return True

    @http.route(["/my/business/appointments/cancel"], type="json", auth="user", methods=["POST"], 
        website=True, csrf=False)
    def cancel_ba_appointment(self, appointment_id):
        """
        The method to cancel appointment

        Methods:
         * action_portal_cancel_reservation of business.appointment
        """
        appointment_id = request.env["business.appointment"].browse(appointment_id).exists()
        res = False
        if appointment_id:
            res = appointment_id.action_portal_cancel_reservation()
        return res

    @http.route(["/my/business/appointments/cancel_reschedule"], type="json", auth="user", methods=["POST"], 
        website=True, csrf=False)
    def cancel_reschedule_ba_appointment(self):
        """
        The method to cancel rescheduling and consider as the repeat

        Methods:
         * _prepare_session_order
        """
        session_id = self._prepare_session_order()
        session_id.write({"resechedule_id": False})
        return True 

    @http.route(["/my/business/appointments/suggested_products"], methods=["POST"], type="json", auth="public",
        website=True, csrf=False)
    def get_suggested_products(self, appointment):
        """
        The route method to get suggested products

        Args:
         * appointment_id - int

        Methods:
         * _get_suggested_products of appointment.product

        Returns:
         * dict:
          ** suggested_products - list of dicts
          ** website_id - int
          ** pricelist_id - int
        """
        result = False
        appointment_id = request.env["business.appointment"].browse(appointment).exists()
        if appointment_id:
            website_id = request.website.id
            service = appointment_id.service_id
            pricelist_id = appointment_id.pricelist_id.id
            result = {
                "suggested_products": service._get_suggested_products(
                    from_website_id=website_id, appointment_id=appointment, pricelist_id=pricelist_id,
                ),
                "website_id": website_id,
                "pricelist_id": pricelist_id,
            }
        return result

    @http.route(["/my/business/appointments/suggested_products/update"], methods=["POST"], type="json", auth="public",
        website=True, csrf=False)
    def update_suggested_products(self, appointment, extra_product_ids):
        """
        The route method to get suggested products

        Args:
         * appointment_id - int
        """
        result = False
        appointment_id = request.env["business.appointment"].browse(appointment).exists()
        if appointment_id:
            appointment_id.extra_product_ids.unlink()
            result = appointment_id.write({"extra_product_ids": extra_product_ids})
        return result

    @http.route(["/my/business/appointments/download/<model('business.appointment'):appointment_id>/<aname>"], 
        type="http",  auth="public",website=True)
    def print_ba_appointment(self, appointment_id=None, aname=None, **kw):
        """
        The route to make and download confirmation of appointment

        Methods:
         * _prepare_portal_layout_values
         * _prepare_confirmation_report of business.appointment
         * make_response of odoo.request
        """
        values = self._prepare_portal_layout_values()
        if values.get("ba_turn_on_appointments"):
            if appointment_id:
                pdf_content = appointment_id._prepare_confirmation_report()
                pdfhttpheaders = [
                    ("Content-Type", "application/pdf"), ("Content-Length", len(pdf_content)),
                ]
                res = request.make_response(pdf_content, headers=pdfhttpheaders)
            else:
                res = request.render("http_routing.404")
        else:
            res = request.render("http_routing.403")
        return res
