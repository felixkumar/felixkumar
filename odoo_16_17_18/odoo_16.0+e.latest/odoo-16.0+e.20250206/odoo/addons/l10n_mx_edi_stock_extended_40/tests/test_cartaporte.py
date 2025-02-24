from freezegun import freeze_time

from odoo.addons.l10n_mx_edi_stock_extended_31.tests.common import TestMXDeliveryGuideCommon
from odoo.tests import tagged


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

        cls.productA = cls.env['product.product'].create({
            'name': 'Product A',
            'type': 'product',
            'uom_id': cls.env.ref('uom.product_uom_kgm').id,
            'uom_po_id': cls.env.ref('uom.product_uom_kgm').id,
            'weight': 1,
        })
        cls.vehicle_pedro.write({
            'environment_insurer': 'DEMO INSURER',
            'environment_insurance_policy': 'DEMO INSURER POLICY',
        })

    @freeze_time('2017-01-01')
    def test_delivery_guide_hazardous_product_outgoing(self):
        '''Test the delivery guide of an (1) hazardous product'''
        self.productA.write({
            'unspsc_code_id': self.env.ref('product_unspsc.unspsc_code_12352120').id,
            'l10n_mx_edi_hazardous_material_code': '1052',
            'l10n_mx_edi_hazard_package_type': '1H1',
        })
        picking = self.create_picking()
        cfdi = picking._l10n_mx_edi_create_delivery_guide()
        self._assert_document_cfdi(cfdi, 'test_delivery_guide_hazardous_product_outgoing')

    @freeze_time('2017-01-01')
    def test_delivery_guide_maybe_hazardous_product_outgoing_0(self):
        '''Test the delivery guide of a maybe (0,1) hazardous product
           Instance not hazardous
        '''
        self.productA.write({
            'unspsc_code_id': self.env.ref('product_unspsc.unspsc_code_12352106').id,
            'l10n_mx_edi_hazardous_material_code': '0',
        })
        picking = self.create_picking()
        cfdi = picking._l10n_mx_edi_create_delivery_guide()
        self._assert_document_cfdi(cfdi, 'test_delivery_guide_maybe_hazardous_product_outgoing_0')

    @freeze_time('2017-01-01')
    def test_delivery_guide_maybe_hazardous_product_outgoing_1(self):
        '''Test the delivery guide of a maybe (0,1) hazardous product
           Instance hazardous
        '''
        self.productA.write({
            'unspsc_code_id': self.env.ref('product_unspsc.unspsc_code_12352106').id,
            'l10n_mx_edi_hazardous_material_code': '1052',
            'l10n_mx_edi_hazard_package_type': '1H1',
        })
        picking = self.create_picking()
        cfdi = picking._l10n_mx_edi_create_delivery_guide()
        self._assert_document_cfdi(cfdi, 'test_delivery_guide_maybe_hazardous_product_outgoing_1')
