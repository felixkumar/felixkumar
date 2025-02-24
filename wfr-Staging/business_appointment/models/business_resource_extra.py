#coding: utf-8

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

REQUIRED_WARNING =_("The required resources for the service {}{} are not correct. Please enter either resources or\
resource types!")


class business_resource_extra(models.Model):
    """
    The model to keep extra resources for products
    """
    _name = "business.resource.extra"
    _description = "Extra resource required"

    @api.constrains("viable")
    def constrains_restrictions(self):
        """
        The constrains method for extra_resource_type_ids and extra_resource_ids
        One of those should be filled
        """
        for line in self:
            if not line.viable:
                raise ValidationError(
                    REQUIRED_WARNING.format(line.service_id.name, line.name and " ({}) ".format(line.name) or "")
                )

    @api.depends("extra_resource_type_ids.active", "extra_resource_ids.active")
    def _compute_viable(self):
        """
        Compute method for viable
        """
        for line in self:
            line.viable = line.extra_resource_type_ids or line.extra_resource_ids

    name = fields.Char(string="Reference")
    extra_resource_type_ids = fields.Many2many(
        "business.resource.type",
        "business_resource_type_extra_rel_table",
        "business_resource_type_rel_id",
        "extra_rel_id",
        string="Types alternatively",
        required=False,
    )
    extra_resource_ids = fields.Many2many(
        "business.resource",
        "business_resource_extra_rel_table",
        "business_resource_rel_id",
        "extra_rel_id",
        string="Resources alternatively",
        required=False,
    )
    service_id = fields.Many2one("appointment.product", string="Service", required=True, ondelete="cascade")
    sequence = fields.Integer(string="Sequence", default=0)
    viable = fields.Boolean(string="Viable", compute=_compute_viable, compute_sudo=True, store=True)

    _order = "sequence, id"

    def _get_all_extra_resources(self):
        """
        The method to get all extra resources
        
        Returns:
         * business.resource.recordset

        Extra info:
         * We consider extra resources as only prime resources (aliases are not used)
         * Expected singleton
        """
        all_resource_ids = self.extra_resource_ids + self.extra_resource_type_ids.mapped("resource_ids")
        all_resource_ids = all_resource_ids.mapped("info_resource_id")
        return all_resource_ids

    def _get_extra_resource_titles(self):
        """
        The method to represent extra resources in the form of string 

        Methods:
         * _get_all_extra_resources

        Returns:
         * Char

        Extra info:
         * Expected singleton
        
        To-do:
         * lang
        """
        res = ""
        extra_resource_ids = self._get_all_extra_resources()
        if extra_resource_ids:
            extra_titles = extra_resource_ids.mapped("name")
            res = _(" OR ").join(extra_titles)
        else:
            res = _("The service requires extra resources that are not possible!")
        return "<p>* {}</p>".format(res)
