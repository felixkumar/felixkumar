#coding: utf-8

from odoo import api, fields, models


class appointment_day_limit(models.Model):
    """
    The model to keep limits for daily appointments 
    """
    _name = "appointment.day.limit"
    _description = "Appointment Restriction"

    @api.depends("mo", "tu", "we", "th", "fr", "sa", "su")
    def _compute_restricted_weekdays(self):
        """
        Compute method for restricted_weekdays
        The final result represents the string without separator. Since each day migh be only a single digit, this
        approahc is fine for the find method
        """
        weekdays_dict = {"mo": "0", "tu": "1", "we": "2", "th": "3", "fr": "4", "sa": "5", "su": "6"}
        for day_limit in self:
            restricted_weekdays = ""
            for weekday_key, weekday_val in weekdays_dict.items():
                if day_limit[weekday_key]:
                    restricted_weekdays += weekday_val
            day_limit.restricted_weekdays = restricted_weekdays

    name = fields.Char(string="Reference", required=True)
    mo = fields.Boolean("Mon")
    tu = fields.Boolean("Tue")
    we = fields.Boolean("Wed")
    th = fields.Boolean("Thu")
    fr = fields.Boolean("Fri")
    sa = fields.Boolean("Sat")
    su = fields.Boolean("Sun")
    restricted_weekdays = fields.Char(
        string="Restricted weekdays",
        compute=_compute_restricted_weekdays,
        store=True,
    )
    spcific_day_ids = fields.One2many("appointment.day.limit.line", "day_limit_id", string="Specific days") 

    def _check_day(self, check_date, resource_tz):
        """
        The method to check whether the current day satify the rule (so is restricted)

        Args:
         * check_date - datetime object
         * default_tz - timezone

        Returns:
         * bool - True if the date IS restricted, False otherwise
        
        Extra info:
         * Expected singleton 
        """
        result = False
        tz_check_date = check_date.astimezone(resource_tz)
        wekday_str = str(tz_check_date.weekday())
        if self.restricted_weekdays.find(wekday_str) != -1:
            result = True
        if not result:
            simple_date = tz_check_date.date()
            for specific_day in self.spcific_day_ids:
                if specific_day.limit_day == simple_date:
                    result = True
                    break
                elif specific_day.limit_day < simple_date:
                    # since days are limited asc
                    break
        return result
