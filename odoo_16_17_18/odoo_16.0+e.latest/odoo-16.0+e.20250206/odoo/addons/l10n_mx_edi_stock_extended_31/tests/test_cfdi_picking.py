from freezegun import freeze_time

from odoo import Command
from odoo.tests import tagged
from .common import TestMXDeliveryGuideCommon


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestCFDIPickingXml(TestMXDeliveryGuideCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.partner_id.city_id = cls.env.ref('l10n_mx_edi_extended.res_city_mx_chh_032').id

        cls.partner_b.write({
            'street': 'Nevada Street',
            'city': 'Carson City',
            'country_id': cls.env.ref('base.us').id,
            'state_id': cls.env.ref('base.state_us_23').id,
            'zip': 39301,
            'vat': '123456789',
        })

    @freeze_time('2017-01-01')
    def test_delivery_guide_31_outgoing(self):
        picking = self.create_picking()
        picking.l10n_mx_edi_gross_vehicle_weight = 2.0

        cfdi = picking._l10n_mx_edi_create_delivery_guide()
        self._assert_document_cfdi(cfdi, 'test_delivery_guide_31_outgoing')

    @freeze_time('2017-01-01')
    def test_delivery_guide_31_incoming(self):
        picking = self.create_picking(picking_type_id=self.new_wh.in_type_id.id)
        picking.l10n_mx_edi_gross_vehicle_weight = 2.0

        cfdi = picking._l10n_mx_edi_create_delivery_guide()
        self._assert_document_cfdi(cfdi, 'test_delivery_guide_31_incoming')

    @freeze_time('2017-01-01')
    def test_delivery_guide_comex_31_outgoing(self):
        self.productA.l10n_mx_edi_material_type = '05'
        self.productA.l10n_mx_edi_material_description = 'Test material description'

        picking = self.create_picking(partner_id=self.partner_b.id)

        picking.l10n_mx_edi_gross_vehicle_weight = 2.0
        picking.l10n_mx_edi_customs_document_type_id = self.env.ref('l10n_mx_edi_stock_extended_30.l10n_mx_edi_customs_document_type_02').id
        picking.l10n_mx_edi_customs_doc_identification = '0123456789'
        picking.l10n_mx_edi_customs_regime_ids = [Command.set([
            self.env.ref('l10n_mx_edi_stock_extended_30.l10n_mx_edi_customs_regime_imd').id,
            self.env.ref('l10n_mx_edi_stock_extended_30.l10n_mx_edi_customs_regime_exd').id,
        ])]

        cfdi = picking._l10n_mx_edi_create_delivery_guide()
        self._assert_document_cfdi(cfdi, 'test_delivery_guide_comex_31_outgoing')

    @freeze_time('2017-01-01')
    def test_delivery_guide_comex_31_incoming(self):
        self.productA.l10n_mx_edi_material_type = '01'

        picking = self.create_picking(partner_id=self.partner_b.id, picking_type_id=self.new_wh.in_type_id.id)

        picking.l10n_mx_edi_gross_vehicle_weight = 2.0
        picking.l10n_mx_edi_customs_document_type_id = self.env.ref('l10n_mx_edi_stock_extended_30.l10n_mx_edi_customs_document_type_01').id
        picking.l10n_mx_edi_importer_id = self.partner_a.id
        picking.l10n_mx_edi_customs_regime_ids = [Command.set([
            self.env.ref('l10n_mx_edi_stock_extended_30.l10n_mx_edi_customs_regime_imd').id,
            self.env.ref('l10n_mx_edi_stock_extended_30.l10n_mx_edi_customs_regime_exd').id,
        ])]

        cfdi = picking._l10n_mx_edi_create_delivery_guide()
        self._assert_document_cfdi(cfdi, 'test_delivery_guide_comex_31_incoming')
