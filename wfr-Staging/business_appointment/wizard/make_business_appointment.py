# -*- coding: utf-8 -*-

from odoo import api, fields, models

PRICLISTS_GROUPS = ["product.group_product_pricelist", "product.group_sale_pricelist"]


class make_business_appointment(models.TransientModel):
    """
    The key wizard to allocate time slots for resource / service
    """
    _name = "make.business.appointment"
    _description = "Schedule Appointment"

    @api.model
    def _default_resource_type_id(self):
        """
        Default method for resource_type_id
        """
        type_ids = self.env["business.resource.type"].search([])
        return type_ids and type_ids[0] or type_ids

    @api.model
    def _default_number_of_appointments(self):
        """
        Default method for number_of_appointments

        Methods:
         * _return_number_of_appointments of business.resource.type
        """
        return self.env["business.resource.type"]._return_number_of_appointments()

    @api.model
    def _default_pricelist_id(self):
        """
        Default method for pricelist_id
        """
        return self.env.company.ba_pricelist_id

    @api.model
    def _default_group_pricelists(self):
        """
        Default method for group_pricelists
        """
        result = True
        for pr_group in PRICLISTS_GROUPS:
            if self.env.user.has_group(pr_group):
                break
        else:
            result = False
        return result

    @api.depends("resource_ids.service_ids", "resource_type_id.service_ids", "resource_type_id.service_method")
    def _compute_available_service_ids(self):
        """
        Compute method for available_service_ids and make_services_visible
         1. If resource type has the single service method, make services invisible. For suddend case restrict selection
            by this single service
         2. If resources are chosen we take available services from there. Services become visible only if some
            resources are chosen and should be chosen (manual allocation)
         3. If resources are not chosen we take services from resource types. For automatic allocation services
            become available as soon as allocation type is defined

        Methods:
         * _get_available_service_ids
        """
        for wiz in self:
            service_ids, make_services_visible = wiz._get_available_service_ids()
            wiz.available_service_ids = [(6, 0, service_ids)]
            wiz.make_services_visible = make_services_visible

    @api.depends("service_id", "pricelist_id")
    def _compute_product_price(self):
        """
        Compute method for product_price and extra_lines
        IMPORTANT: it is the char fields, whcih are language-dependent

        Methods:
         * action_calculate_price of appointment.product
         * _get_all_extra_resource_titles of appointment.product

        Extra info:
         * we do not care about changes in services extra lines, since to the moment of chosen product, their would
           be already fixed
        """
        for wiz in self:
            product_price = extra_lines = ""
            if wiz.service_id:
                if wiz.service_id.product_id and wiz.pricelist_id:
                    product_price = self.env["appointment.product"].action_calculate_price(
                        wiz.service_id.product_id.id, wiz.pricelist_id.id
                    )
                extra_lines = wiz.service_id._get_all_extra_resource_titles()
            wiz.product_price = product_price
            wiz.extra_lines = extra_lines

    @api.onchange("appointment_id")
    def _onchange_appointment_id(self):
        """
        Onchange method for appointment_id

        We change here only resource_type_id, since in its onchange we check defaults
        """
        for wiz in self:
            if wiz.appointment_id:
                wiz.resource_type_id = wiz.appointment_id.resource_id.resource_type_id
                wiz.pricelist_id = wiz.appointment_id.pricelist_id

    @api.onchange("resource_type_id")
    def _onchange_resource_type_id(self):
        """
        Onchange method for resource_type_id
         1. If allocation is not automatic, and only a single resource is available --> put this resource
            Note: it doesn't contradict default, since this single resource might be the only one possible default
         2. For the single service method, we have always the same service disregarding resources
            Note: it also doesn't contradict default, since single service is always the same
         3. If allocation is automatic, and only single service is availabe --> put this service
            Note: it also doesn't contradict default, since single service is always the same
            Note: the case to put a single service of resource is done under changing resource
         4. If service relates to a new resource type as well, leave it there. Already chosen service is in priority
            NoteL it doesn't contradict service, since it is already chosen
         5. If resource or service are not found, we try to retrieve that from defaults
         6. Make sure resources and service suit the resource type
         7. We add conditions not to trigger excess onchanges
        """
        for wiz in self:
            resource_ids = False
            service_id = False
            if wiz.resource_type_id:
                if wiz.allocation_type == "manual" and len(wiz.resource_type_id.resource_ids) == 1:
                    # 1
                    resource_ids = wiz.resource_type_id.resource_ids[0]
                if wiz.resource_type_id.service_method == "single":
                    # 2
                    service_id = wiz.resource_type_id.always_service_id
                elif wiz.allocation_type == "automatic":
                    if len(wiz.resource_type_id.service_ids) == 1:
                        # 3
                        service_id = wiz.resource_type_id.service_ids[0]
                    elif wiz.service_id in wiz.resource_type_id.service_ids:
                        # 4
                        service_id = wiz.service_id
            # 5
            if not resource_ids:
                if wiz.appointment_id:
                    resource_ids = wiz.appointment_id.resource_id
                elif self._context.get("default_resource_id"):
                    resource_ids = self.env["business.resource"].browse(self._context.get("default_resource_id"))
            if not service_id:
                if wiz.appointment_id:
                    service_id = wiz.appointment_id.service_id
                elif not resource_ids and self._context.get("default_service_id"):
                    service_id = self.env["appointment.product"].browse(self._context.get("default_service_id"))
            # 6
            if wiz.resource_type_id:
                if resource_ids:
                    rtype_resources = set(wiz.resource_type_id.resource_ids.ids or [])
                    resource_ids = self.env["business.resource"].browse(list(set(resource_ids.ids) & rtype_resources))            
                rtype_final_services = wiz.resource_type_id.final_service_ids
                if service_id and (not rtype_final_services or service_id.id not in rtype_final_services.ids):
                    service_id = False
            else:
                resource_ids = False
                service_id = False                
            # 7
            if wiz.resource_ids != resource_ids:
                wiz.resource_ids = resource_ids
            if wiz.service_id != service_id:
                wiz.service_id = service_id

    @api.onchange("resource_ids")
    def _onchange_resource_ids(self):
        """
        Onchange method for resource_ids
         1. We change service in case of resource is changed only in case of manual resources (otherwise it is done
            by resource type) and multiple services possible (otherwise it is take from resource type)
          1.1. We can work here only with ids, since reords contain new origin
         2. If only a single service possible --> take it
            Note: it doesn't contradict default, since it is the only service of this resource
         3. If there are multiple services, and one is among those is already chosen in the wizard --> keep it
            Note: it doesn't contradcit default, since it already chosen resource
         4. If service is not found, we try to retrieve that from defaults (if suit the resource type)
         5. Make sure service does not contradict resource
         6. We add conditions not to trigger excess onchanges
        """
        for wiz in self:
            # 1
            if wiz.resource_type_id.service_method == "multiple" and wiz.allocation_type == "manual":
                service_id = False
                service_ids = wiz.available_service_ids.ids
                unique_services = self.env["appointment.product"]
                if wiz.resource_ids:
                    # 2
                    if len(service_ids) == 1:
                        service_id = self.env["appointment.product"].browse(service_ids[0])
                if service_ids and not service_id and wiz.service_id.id in service_ids:
                    # 3
                    service_id = wiz.service_id
                if not service_id:
                    # 4
                    if wiz.appointment_id:
                        service_id = wiz.appointment_id.service_id
                    elif self._context.get("default_service_id") and wiz.resource_ids and service_ids:
                        service_id = self.env["appointment.product"].browse(self._context.get("default_service_id"))
                # 5
                if service_id and (not service_ids or (service_id.id not in service_ids)):
                    service_id = False
                # 6 
                if wiz.service_id != service_id:
                    wiz.service_id = service_id

    appointment_id = fields.Many2one("business.appointment", string="Appointment")
    resource_type_id = fields.Many2one(
        "business.resource.type",
        string="Resource Type",
        required=True,
        default=_default_resource_type_id,
    )
    resource_ids = fields.Many2many(
        "business.resource",
        "business_resource_make_business_appointment_rel_table",
        "business_resource_rel_id",
        "make_business_appointment_rel_id",
        string="Resource",
    )
    service_id = fields.Many2one("appointment.product", string="Service")
    pricelist_id = fields.Many2one("product.pricelist", "Pricelist", default=_default_pricelist_id)
    product_price = fields.Char(
        string="Service Price",
        compute=_compute_product_price,
        compute_sudo=True,
        store=True,
    )
    extra_lines = fields.Html(
        string="Extra resources",
        compute=_compute_product_price,
        compute_sudo=True,
        store=True,
    )
    allocation_type = fields.Selection(related="resource_type_id.allocation_type", compute_sudo=True)
    available_service_ids = fields.Many2many(
        "appointment.product",
        "appointment_product_make_business_appointment_rel_table",
        "appointment_product_rel_id",
        "make_business_appointment_rel_id",
        string="Available services",
        compute=_compute_available_service_ids,
        store=True,
    )
    make_services_visible = fields.Boolean(
        "Service is visible",
        compute=_compute_available_service_ids,
        store=True,
    )
    number_of_appointments = fields.Integer(string="Number of appointments", default=_default_number_of_appointments)
    timeslots = fields.Char(string="Time Slots")
    group_pricelists = fields.Boolean(string="Pricelists", default=_default_group_pricelists)

    def _get_available_service_ids(self):
        """
        The method to define available services based on resource type and resource settings
         1. If resource type has the single service method, make services invisible. For suddend case restrict selection
            by this single service
         2. If resources are chosen we take available services from there. Services become visible only if some
            resources are chosen and should be chosen (manual allocation)
         3. If resources are not chosen we take services from resource types. For automatic allocation services
            become available as soon as allocation type is defined

        Return:
         * tuple of:
          * list of ints
          ** bool
        """
        service_ids = []
        make_services_visible = False
        if self.resource_type_id.service_method == "single":
            # 1
            service_ids = [self.resource_type_id.always_service_id.id]
        else:
            if self.resource_ids:
                #2
                service_ids = self.resource_ids.mapped("final_service_ids").ids
                make_services_visible = True
            elif self.resource_type_id:
                #3
                service_ids = self.resource_type_id.final_service_ids.ids
                if self.allocation_type == "automatic":
                    make_services_visible = True
        return service_ids, make_services_visible
