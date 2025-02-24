# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools

class appointment_analytic(models.Model):
    """
    The model to calculate statistics by appointments
    """
    _name = "appointment.analytic"
    _auto = False
    _description = "Appointments Analysis"
    _rec_name = "id"

    def _state_selection(self):
        """
        The method to return available appointment states
        """
        return self.env["business.appointment"]._state_selection()

    name = fields.Char(string="Appointment Reference", readonly=True)
    resource_type_id = fields.Many2one(
        "business.resource.type",
        string="Resource Type",
        readonly=True,
    )
    resource_id = fields.Many2one(
        "business.resource",
        string="Resource (with aliases)",
        readonly=True,
    )
    info_resource_id = fields.Many2one(
        "business.resource",
        string="Resource (only prime)",
        readonly=True,
    )
    service_id = fields.Many2one(
        "appointment.product",
        string="Service",
        readonly=True,
    )    
    user_id = fields.Many2one(
        "res.users",
        string="Responsible",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Contact",
        readonly=True,
    )    
    state = fields.Selection(
        _state_selection,
        string="State",
        readonly=True,
    )
    datetime_start = fields.Datetime(
        string="Reserved Time",
        readonly=True,
    )
    duration = fields.Float(
        string="Duration",
        readonly=True,
    )    
    company_id = fields.Many2one(
        "res.company", 
        "Company", 
        readonly=True,
    )    

    def _select_query(self):
        """
        The method to prepare columns for SQL execute
        """
        select_str = """
            SELECT
                a.id,
                a.name,
                a.resource_type_id,
                a.info_resource_id,
                a.resource_id,
                a.service_id,
                a.user_id,
                a.partner_id,
                a.state,
                a.datetime_start,
                a.duration,
                a.company_id"""
        return select_str
    
    def _from_query(self):
        """
        The method to prepare table for SQL execute
        """
        from_str = """
            FROM
                "business_appointment" a"""
        return from_str

    def _join_query(self):
        """
        The method to prepare joined table for SQL execute
        """
        join_str = """ """
        return join_str

    def _where_query(self):
        """
        The method to prepare restrictions for SQL execute
        """
        where_str = """ """
        return where_str

    def _group_by_query(self):
        """
        The method to prepare groupings for SQL execute
        """
        group_by_str = """
            GROUP BY 
                a.id,
                a.resource_type_id,
                a.info_resource_id,
                a.resource_id,
                a.service_id,
                a.user_id,
                a.partner_id,
                a.state"""
        return group_by_str

    def init(self):
        """
        Initialize the model
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
                %s
                %s
            )
        """ % (self._table, self._select_query(), self._from_query(), self._join_query(), self._where_query(), 
               self._group_by_query())
        self.env.cr.execute(query)
