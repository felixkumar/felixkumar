from odoo import fields,models,api,_

class ThirdPartyAccountNumber(models.Model):
    _name = "third.party.account.number"
    _description = 'Third Party Account Number'

    name = fields.Char(string='Third Party Account Name',required=True)
    account_number = fields.Char(string='Account Number',required=True)