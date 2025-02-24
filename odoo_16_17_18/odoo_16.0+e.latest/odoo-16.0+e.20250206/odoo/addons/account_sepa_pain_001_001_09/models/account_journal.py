# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from lxml import etree

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    sepa_pain_version = fields.Selection(
        selection_add=[('pain.001.001.09', 'New generic version (09)')],
        ondelete={'pain.001.001.09': lambda recs: recs.write({'sepa_pain_version': 'pain.001.001.03'})}
    )

    def _get_document(self, pain_version):
        if pain_version == 'pain.001.001.09':
            return self._create_iso20022_document('pain.001.001.09')
        return super()._get_document(pain_version)

    def _get_company_PartyIdentification32(self, sct_generic=False, org_id=True, postal_address=True, nm=True, issr=True, schme_nm=False):
        ret = super()._get_company_PartyIdentification32(sct_generic, org_id, postal_address, nm, issr, schme_nm)

        if self.sepa_pain_version == "pain.001.001.09" and self.company_id.account_sepa_lei:
            OrgId = ret and ret[-1].find("OrgId")
            if OrgId is not None:
                # LEI needs to be inserted before Othr
                LEI = etree.Element("LEI")
                LEI.text = self.company_id.account_sepa_lei
                insert_at = 0 if len(OrgId) == 1 else 1 # sometimes AnyBIC node is there, sometimes not
                OrgId.insert(insert_at, LEI)

        return ret

    def _get_CdtTrfTxInf(self, PmtInfId, payment, sct_generic, pain_version, local_instrument=None):
        CdtTrfTxInf = super()._get_CdtTrfTxInf(PmtInfId, payment, sct_generic, pain_version, local_instrument)

        if self.sepa_pain_version == "pain.001.001.09":
            PmtId = CdtTrfTxInf.find("PmtId")
            UETR = etree.SubElement(PmtId, "UETR")
            UETR.text = payment["sepa_uetr"]

        return CdtTrfTxInf

    def _get_CdtrAgt(self, bank_account, sct_generic, pain_version):
        CdtrAgt = super()._get_CdtrAgt(bank_account, sct_generic, pain_version)

        if self.sepa_pain_version != "pain.001.001.09":
            return CdtrAgt

        partner_lei = bank_account.partner_id.account_sepa_lei
        FinInstnId = CdtrAgt.find("FinInstnId")
        if FinInstnId is not None:
            BIC = FinInstnId.findall("BIC")
            if BIC:
                BIC[0].tag = "BICFI"
            if partner_lei:
                # LEI needs to be inserted after BIC
                LEI = etree.Element("LEI")
                LEI.text = partner_lei
                insert_at = 1 if BIC else 0
                FinInstnId.insert(insert_at, LEI)

        return CdtrAgt
