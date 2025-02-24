# -*- coding: utf-8 -*-

from odoo import api, fields, models


class rating_rating(models.Model):
    """
    Overwrite to add service and resource
    """
    _inherit = "rating.rating"

    @api.depends("res_model", "res_id")
    def _compute_service_id(self):
        """
        Compute method for service_id and resource_id
        """
        for rating in self:
            service_id = False
            resource_id = False
            if rating.res_model == "business.appointment":
                try:
                    appointment = self.env[rating.res_model].sudo().browse(rating.res_id)
                    service_id = appointment.service_id
                    resource_id = appointment.resource_id
                except:
                    service_id = False
                    resource_id = False                    
            rating.service_id = service_id
            rating.resource_id = resource_id

    service_id = fields.Many2one(
        "appointment.product",
        string="Service",
        compute=_compute_service_id,
        store=True,
        compute_sudo=True,
    )
    service_id_int = fields.Integer(
        string="Service ID",
        related="service_id.id",
        store=True,
        compute_sudo=True,
        related_sudo=True,
    )
    resource_id = fields.Many2one(
        "business.resource",
        string="Resource",
        compute=_compute_service_id,
        store=True,
        compute_sudo=True,
    )
    resource_id_int = fields.Integer(
        string="Resource ID",
        related="resource_id.id",
        store=True,
        compute_sudo=True,
        related_sudo=True,
    )

    @api.model
    def _calculate_satisfaction_rate(self, parent_records):
        """
        The method to calculate satisfaction rate for business.appointment objects

        Args:
         * parent_records - recordset: business.resource.type, business.resource, appointment.product

        Returns:
         * float
        """
        domain = [("parent_res_model", "=", "business.resource.type"), ("rating", ">=", 1), ("consumed", "=", True)]
        parent_key = "parent_res_id"
        if parent_records._name == "business.resource.type":
            domain.append(("parent_res_id", "in", parent_records.ids))
        elif parent_records._name == "business.resource":
            domain.append(("resource_id", "in", parent_records.ids))
            parent_key = "resource_id_int"
        elif parent_records._name == "appointment.product":
            domain.append(("service_id", "in", parent_records.ids))
            parent_key = "service_id_int"
        data = self.read_group(
            domain, [parent_key, "rating"], [parent_key, "rating"], lazy=False
        )
        default_grades = {"great": 0, "okay": 0, "bad": 0}
        grades_per_parent = dict((parent_id, dict(default_grades)) for parent_id in parent_records.ids)
        for item in data:
            parent_id = item[parent_key]
            rating = item["rating"]
            if rating >= 5:
                grades_per_parent[parent_id]["great"] += item["__count"]
            elif rating > 3:
                grades_per_parent[parent_id]["okay"] += item["__count"]
            else:
                grades_per_parent[parent_id]["bad"] += item["__count"]
        res = {}
        for record in parent_records:
            repartition = grades_per_parent.get(record.id)
            res[record.id] = repartition["great"] * 100 / sum(repartition.values()) if sum(repartition.values()) else -1
        return res
