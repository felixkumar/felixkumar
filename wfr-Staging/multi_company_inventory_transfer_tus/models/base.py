#  See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import Warning, UserError


class BaseModel(models.AbstractModel):
    _inherit = 'base'

    def _check_company(self, fnames=None):
        """ Check the companies of the values of the given field names.

        :param list fnames: names of relational fields to check
        :raises UserError: if the `company_id` of the value of any field is not
            in `[False, self.company_id]` (or `self` if
            :class:`~odoo.addons.base.models.res_company`).

        For :class:`~odoo.addons.base.models.res_users` relational fields,
        verifies record company is in `company_ids` fields.

        User with main company A, having access to company A and B, could be
        assigned or linked to records in company B.
        """
        if fnames is None:
            fnames = self._fields

        regular_fields = []
        property_fields = []
        for name in fnames:
            field = self._fields[name]
            if field.relational and field.check_company and \
                    'company_id' in self.env[field.comodel_name]:
                if not field.company_dependent:
                    regular_fields.append(name)
                else:
                    property_fields.append(name)

        if not (regular_fields or property_fields):
            return

        inconsistencies = []
        for record in self:
            company = record.company_id if record._name != 'res.company' else record
            # The first part of the check verifies that all records linked via relation fields are compatible
            # with the company of the origin document, i.e. `self.account_id.company_id == self.company_id`
            for name in regular_fields:
                corecord = record.sudo()[name]
                # Special case with `res.users` since an user can belong to multiple companies.
                if corecord._name in ['res.users', 'product.product'] and corecord.company_ids:
                    if not (company <= corecord.company_ids):
                        inconsistencies.append((record, name, corecord))
                elif not (corecord.company_id <= company):
                    inconsistencies.append((record, name, corecord))
            # The second part of the check (for property / company-dependent fields) verifies that the records
            # linked via those relation fields are compatible with the company that owns the property value, i.e.
            # the company for which the value is being assigned, i.e:
            #      `self.property_account_payable_id.company_id == self.env.company
            company = self.env.company
            for name in property_fields:
                # Special case with `res.users` since an user can belong to multiple companies.
                corecord = record.sudo()[name]
                if corecord._name in ['res.users', 'product.product'] and corecord.company_ids:
                    if not (company <= corecord.company_ids):
                        inconsistencies.append((record, name, corecord))
                elif not (corecord.company_id <= company):
                    inconsistencies.append((record, name, corecord))

        if inconsistencies and not self.env.company.is_multi_company_inventory_transfer:
            lines = [_("Incompatible companies on records:")]
            company_msg = _(
                "- Record is company %(company)r and %(field)r (%(fname)s: %(values)s) belongs to another company.")
            record_msg = _(
                "- %(record)r belongs to company %(company)r and %(field)r (%(fname)s: %(values)s) belongs to another company.")
            for record, name, corecords in inconsistencies[:5]:
                if record._name == 'res.company':
                    msg, company = company_msg, record
                else:
                    msg, company = record_msg, record.company_id
                field = self.env['ir.model.fields']._get(self._name, name)
                lines.append(str(msg) % {
                    'record': record.display_name,
                    'company': company.display_name,
                    'field': field.field_description,
                    'fname': field.name,
                    'values': ", ".join(repr(rec.display_name) for rec in corecords),
                })
            raise UserError("\n".join(lines))
