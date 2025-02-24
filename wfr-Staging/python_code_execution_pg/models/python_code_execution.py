""" Managed the python code execution """
# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import ValidationError


class PythonCodeExecution(models.Model):
    """Python Code Execution"""
    _name = "python.code.execution"
    _description = "Python Code Execute In User Interface"
    _rec_name = "code_name"
    _order = 'code_name, id asc'

    code_name = fields.Char(string='Name')
    result = fields.Text(string='Result')
    code_exec = fields.Text(string='Code')
    active = fields.Boolean(string='Active', default=True)

    def python_code_execution(self):
        """
        python code execution and return the result
        :return: Result as dictionary or True
        """
        self.ensure_one()
        dict_data = {'self': self, 'user_obj': self.env.user}
        try:
            if self.code_exec:
                exec(self.code_exec, dict_data)
                if "result" in dict_data.keys():
                    self.write({'result': dict_data['result']})
                else:
                    self.write({'result': 'Did not fetch any result!'})
            else:
                raise ValidationError(_("There is no lines for execute!!!"))
        except Exception as exception:
            raise ValidationError(f'{exception}')
        return True
