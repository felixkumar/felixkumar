# Part of Odoo. See LICENSE file for full copyright and licensing details.
from contextlib import contextmanager

from odoo.fields import Command
from odoo.addons.point_of_sale.tests.common import TestPoSCommon


class TestInGstrPosBase(TestPoSCommon):
    """
    Base class for Indian GSTR and POS-related test cases.
    This class sets up the company, products, and configuration required
    for any test involving GSTR in a POS environment.
    """
    @classmethod
    def setUpClass(cls, chart_template_ref="in"):
        super().setUpClass(chart_template_ref=chart_template_ref)
        country_in_id = cls.env.ref("base.in").id
        cls.company_data["company"].write({
            "vat": "24AAGCC7144L6ZE",
            "state_id": cls.env.ref("base.state_in_gj").id,
            "street": "street1",
            "city": "city1",
            "zip": "123456",
            "country_id": country_in_id,
        })
        cls.config = cls.basic_config
        cls.gst_5 = cls.env['account.chart.template'].ref('sgst_sale_5')

        # Common product setup for POS tests
        cls._setup_products()

    @classmethod
    def _setup_products(cls):
        """Sets up products for POS testing with GST."""
        cls.product_a.write({
            'available_in_pos': True,
            'l10n_in_hsn_code': '1111',
            'list_price': 100,
            'taxes_id': [Command.set(cls.gst_5.ids)],  # Tax: 10
        })
        cls.product_b.write({
            'available_in_pos': True,
            'l10n_in_hsn_code': '2222',
            'list_price': 200,
            'taxes_id': [Command.set(cls.gst_5.ids)],  # Tax: 20
        })

    @contextmanager
    def with_pos_session(self):
        """Opens a new POS session and ensures it is closed properly."""
        session = self.open_new_session(0.0)
        yield session
        session.post_closing_cash_details(0.0)
        session.close_session_from_ui()

    def _create_order(self, ui_data):
        """Helper to create a POS order from UI data."""
        order_data = self.create_ui_order_data(**ui_data)
        results = self.env['pos.order'].create_from_ui([order_data])
        return self.env['pos.order'].browse(results[0]['id'])
