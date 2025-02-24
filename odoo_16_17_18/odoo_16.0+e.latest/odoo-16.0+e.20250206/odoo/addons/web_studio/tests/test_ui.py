# Part of Odoo. See LICENSE file for full copyright and licensing details.
# -*- coding: utf-8 -*-

import logging

from lxml import etree
import json

import odoo.tests
from odoo import Command, api, http
from odoo.tools import mute_logger
from odoo.addons.web_studio.controllers.main import WebStudioController

_logger = logging.getLogger(__name__)


@odoo.tests.tagged('post_install', '-at_install')
class TestUi(odoo.tests.HttpCase):

    def test_new_app_and_report(self):
        self.start_tour("/web", 'web_studio_new_app_tour', login="admin")

        # the report tour is based on the result of the former tour
        self.start_tour("/web?debug=tests", 'web_studio_new_report_tour', login="admin")
        self.start_tour("/web?debug=tests", "web_studio_new_report_basic_layout_tour", login="admin")

    def test_optional_fields(self):
        self.start_tour("/web?debug=tests", 'web_studio_hide_fields_tour', login="admin")

    def test_model_option_value(self):
        self.start_tour("/web?debug=tests", 'web_studio_model_option_value_tour', login="admin")

    def test_rename(self):
        self.start_tour("/web?debug=tests", 'web_studio_tests_tour', login="admin", timeout=200)

    def test_approval(self):
        self.start_tour("/web?debug=tests", 'web_studio_approval_tour', login="admin")

    def test_background(self):
        attachment = self.env['ir.attachment'].create({
            'datas': b'R0lGODdhAQABAIAAAP///////ywAAAAAAQABAAACAkQBADs=',
            'name': 'testFilename.gif',
            'public': True,
            'mimetype': 'image/gif'
        })
        self.env.company.background_image = attachment.datas
        self.start_tour("/web?debug=tests", 'web_studio_custom_background_tour', login="admin")

    def test_create_app_with_pipeline_and_user_assignment(self):
        # Mute the logger for read_group, indeed, because of the field
        # x_studio_sequence that is created during the tour, this method will
        # trigger a warning
        web_read_group = type(self.env["base"]).web_read_group
        @mute_logger("odoo.models")
        @api.model
        def muted_web_read_group(self, *args, **kwargs):
            return web_read_group(self, *args, **kwargs)

        self.patch(type(self.env["base"]), "web_read_group", muted_web_read_group)
        self.start_tour("/web?debug=tests", 'web_studio_create_app_with_pipeline_and_user_assignment', login="admin")

    def test_alter_field_existing_in_multiple_views(self):
        created_model_name = None
        studio_model_create = type(self.env["ir.model"]).studio_model_create
        def mock_studio_model_create(*args, **kwargs):
            nonlocal created_model_name
            res = studio_model_create(*args, **kwargs)
            created_model_name = res[0].model
            return res

        self.patch(type(self.env["ir.model"]), "studio_model_create", mock_studio_model_create)
        self.start_tour("/web?debug=tests", 'web_studio_alter_field_existing_in_multiple_views_tour', login="admin", timeout=20000)

        # we can't assert xml equality as a lot of stuff in the arch are set randomly
        view = self.env["ir.ui.view"].search([("model", "=", created_model_name), ("type", "=", "form")], limit=1)
        tree = etree.fromstring(view.get_combined_arch())
        root = tree.getroottree()

        fields_of_interest = tree.xpath("//field[@name='message_partner_ids']")
        self.assertEqual(len(fields_of_interest), 2)

        # First field is on the main model: not below another field
        # The second one is in a subview
        self.assertEqual(root.getpath(fields_of_interest[0]), "/form/sheet/group/group[1]/field")
        self.assertEqual(root.getpath(fields_of_interest[1]), "/form/sheet/field[2]/tree/field[1]")

        # The tour in its final steps is putting invisible on the field in the subview
        self.assertEqual(fields_of_interest[0].get("invisible"), None)
        self.assertEqual(fields_of_interest[1].get("invisible"), "1")

    def test_hide_page_of_notebook(self):
        self.start_tour("/web?debug=tests", 'web_studio_test_hide_page_of_notebook', login="admin")

def _get_studio_view(view):
    domain = [('inherit_id', '=', view.id), ('name', '=', "Odoo Studio: %s customization" % (view.name))]
    return view.search(domain, order='priority desc, name desc, id desc', limit=1)

def _transform_arch_for_assert(arch_string):
    parser = etree.XMLParser(remove_blank_text=True)
    arch_string = etree.fromstring(arch_string, parser=parser)
    return etree.tostring(arch_string, pretty_print=True, encoding='unicode')

def assertViewArchEqual(test, original, expected):
    if original:
        original = _transform_arch_for_assert(original)
    if expected:
        expected = _transform_arch_for_assert(expected)
    test.assertEqual(original, expected)

def watch_edit_view(test, on_edit_view):
    clear_routing = test.env["ir.http"]._clear_routing_map

    clear_routing()
    edit_view = WebStudioController.edit_view

    @http.route('/web_studio/edit_view', type='json', auth='user')
    def edit_view_mocked(*args, **kwargs):
        on_edit_view(*args, **kwargs)
        return edit_view(*args, **kwargs)

    test.patch(WebStudioController, "edit_view", edit_view_mocked)
    test.addCleanup(clear_routing)


@odoo.tests.tagged('post_install', '-at_install')
class TestStudioUIUnit(odoo.tests.HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.country_id = cls.env.ref('base.us')
        cls.testView = cls.env["ir.ui.view"].create({
            "name": "simple partner",
            "model": "res.partner",
            "type": "form",
            "arch": '''
                <form>
                    <field name="name" />
                </form>
            '''
        })
        cls.testAction = cls.env["ir.actions.act_window"].create({
            "name": "simple partner",
            "res_model": "res.partner",
            "view_ids": [Command.create({"view_id": cls.testView.id, "view_mode": "form"})]
        })
        cls.testActionXmlId = cls.env["ir.model.data"].create({
            "name": "studio_test_partner_action",
            "model": "ir.actions.act_window",
            "module": "web_studio",
            "res_id": cls.testAction.id,
        })
        cls.testMenu = cls.env["ir.ui.menu"].create({
            "name": "Studio Test Partner",
            "action": "ir.actions.act_window,%s" % cls.testAction.id
        })
        cls.testMenuXmlId = cls.env["ir.model.data"].create({
            "name": "studio_test_partner_menu",
            "model": "ir.ui.menu",
            "module": "web_studio",
            "res_id": cls.testMenu.id,
        })

    def test_form_view_not_altered_by_studio_xml_edition(self):
        self.start_tour("/web?debug=tests", 'web_studio_test_form_view_not_altered_by_studio_xml_edition', login="admin", timeout=200)

    def test_edit_with_xml_editor(self):
        studioView = self.env["ir.ui.view"].create({
            'type': self.testView.type,
            'model': self.testView.model,
            'inherit_id': self.testView.id,
            'mode': 'extension',
            'priority': 99,
            'arch': "<data><xpath expr=\"//field[@name='name']\" position=\"after\"> <div class=\"someDiv\"/></xpath></data>",
            'name': "Odoo Studio: %s customization" % (self.testView.name)
        })

        self.start_tour("/web?debug=tests", 'web_studio_test_edit_with_xml_editor', login="admin", timeout=200)
        self.assertEqual(studioView.arch, "<data/>")

    def test_enter_x2many_edition_and_add_field(self):
        doesNotHaveGroup = self.env["res.groups"].create({
            "name": "studio does not have"
        })
        doesNotHaveGroupXmlId = self.env["ir.model.data"].create({
            "name": "studio_test_doesnothavegroup",
            "model": "res.groups",
            "module": "web_studio",
            "res_id": doesNotHaveGroup.id,
        })

        userView = self.env["ir.ui.view"].create({
            "name": "simple user",
            "model": "res.users",
            "type": "form",
            "arch": '''
                <form>
                    <t groups="{doesnothavegroup}" >
                        <div class="condition_group" />
                    </t>
                    <group>
                        <field name="name" />
                    </group>
                </form>
            '''.format(doesnothavegroup=doesNotHaveGroupXmlId.complete_name)
        })

        userViewXmlId = self.env["ir.model.data"].create({
            "name": "studio_test_user_view",
            "model": "ir.ui.view",
            "module": "web_studio",
            "res_id": userView.id,
        })

        self.testView.arch = '''<form><field name="user_ids" context="{'form_view_ref': '%s'}" /></form>''' % userViewXmlId.complete_name
        studioView = _get_studio_view(self.testView)
        self.assertFalse(studioView.exists())

        self.start_tour("/web?debug=tests", 'web_studio_enter_x2many_edition_and_add_field', login="admin", timeout=200)
        studioView = _get_studio_view(self.testView)

        assertViewArchEqual(self, studioView.arch, """
            <data>
               <xpath expr="//field[@name='user_ids']" position="inside">
                 <form>
                   <t groups="{doesnothavegroup}" >
                     <div class="condition_group" />
                   </t>
                   <group>
                     <field name="name"/>
                     <field name="log_ids"/>
                   </group>
                 </form>
               </xpath>
             </data>
            """.format(doesnothavegroup=doesNotHaveGroupXmlId.complete_name))

    def test_enter_x2many_auto_inlined_subview(self):
        userView = self.env["ir.ui.view"].create({
            "name": "simple user",
            "model": "res.users",
            "type": "tree",
            "arch": '''
                <tree>
                    <field name="display_name" />
                </tree>
            '''
        })

        userViewXmlId = self.env["ir.model.data"].create({
            "name": "studio_test_user_view",
            "model": "ir.ui.view",
            "module": "web_studio",
            "res_id": userView.id,
        })

        self.testView.arch = '''<form><field name="user_ids" context="{'tree_view_ref': '%s'}" /></form>''' % userViewXmlId.complete_name
        studioView = _get_studio_view(self.testView)
        self.assertFalse(studioView.exists())

        self.start_tour("/web?debug=tests", 'web_studio_enter_x2many_auto_inlined_subview', login="admin", timeout=200)
        studioView = _get_studio_view(self.testView)

        assertViewArchEqual(self, studioView.arch, """
            <data>
               <xpath expr="//field[@name='user_ids']" position="inside">
                 <tree>
                   <field name="display_name" />
                   <field name="log_ids" optional="show" />
                 </tree>
               </xpath>
             </data>
            """)

    def test_enter_x2many_auto_inlined_subview_with_multiple_field_matching(self):
        user_view = self.env["ir.ui.view"].create({
            "name": "simple user",
            "model": "res.users",
            "type": "tree",
            "arch": '''
                <tree>
                    <field name="display_name" />
                </tree>
            '''
        })

        user_view_xml_id = self.env["ir.model.data"].create({
            "name": "studio_test_user_view",
            "model": "ir.ui.view",
            "module": "web_studio",
            "res_id": user_view.id,
        })

        self.testView.arch = '''<form>
            <field name="user_ids"/>
            <sheet>
                <notebook>
                    <page>
                        <field name="user_ids" context="{'tree_view_ref': '%s'}" />
                    </page>
                </notebook> 
            </sheet>
        </form>''' % user_view_xml_id.complete_name
        studio_view = _get_studio_view(self.testView)
        self.assertFalse(studio_view.exists())

        self.start_tour("/web?debug=tests", 'web_studio_enter_x2many_auto_inlined_subview_with_multiple_field_matching',
                        login="admin", timeout=200)
        studio_view = _get_studio_view(self.testView)

        assertViewArchEqual(self, studio_view.arch, """
            <data>
               <xpath expr="//form[1]/sheet[1]/notebook[1]/page[1]/field[@name='user_ids']" position="inside">
                 <tree>
                   <field name="display_name" />
                   <field name="log_ids" optional="show" />
                 </tree>
               </xpath>
             </data>
            """)

    def test_field_with_group(self):
        operations = []
        def edit_view_mocked(*args, **kwargs):
            operations.extend(kwargs["operations"] if "operations" in kwargs else args[3])

        watch_edit_view(self, edit_view_mocked)

        doesNotHaveGroup = self.env["res.groups"].create({
            "name": "studio does not have"
        })
        doesNotHaveGroupXmlId = self.env["ir.model.data"].create({
            "name": "studio_test_doesnothavegroup",
            "model": "res.groups",
            "module": "web_studio",
            "res_id": doesNotHaveGroup.id,
        })
        self.testView.write({
            "type": "tree",
            "arch": '''
                <tree>
                    <field name="display_name" />
                    <field name="employee" groups="{doesnothavegroup}" />
                    <field name="function" />
                    <field name="lang" />
                </tree>
            '''.format(doesnothavegroup=doesNotHaveGroupXmlId.complete_name)
        })
        self.testAction.write({
            "view_ids": [Command.clear(), Command.create({"view_id": self.testView.id, "view_mode": "tree"})]
        })

        self.start_tour("/web?debug=tests", 'web_studio_field_with_group', login="admin", timeout=200)

        self.assertEqual(len(operations), 1)
        self.assertEqual(operations[0]["target"]["xpath_info"], [{'tag': 'tree', 'indice': 1}, {'tag': 'field', 'indice': 3}])
        studioView = _get_studio_view(self.testView)
        assertViewArchEqual(self, studioView.arch, """
             <data>
                <xpath expr="//field[@name='function']" position="after">
                    <field name="website" optional="show"/>
                </xpath>
            </data>
        """)

    def test_elements_with_groups_form(self):
        operations = []
        def edit_view_mocked(*args, **kwargs):
            operations.extend(kwargs["operations"] if "operations" in kwargs else args[3])

        watch_edit_view(self, edit_view_mocked)

        doesNotHaveGroup = self.env["res.groups"].create({
            "name": "studio does not have"
        })
        doesNotHaveGroupXmlId = self.env["ir.model.data"].create({
            "name": "studio_test_doesnothavegroup",
            "model": "res.groups",
            "module": "web_studio",
            "res_id": doesNotHaveGroup.id,
        })

        hasGroup = self.env["res.groups"].create({
            "name": "studio has group",
            "users": [Command.link(2)]
        })
        hasGroupXmlId = self.env["ir.model.data"].create({
            "name": "studio_test_hasgroup",
            "model": "res.groups",
            "module": "web_studio",
            "res_id": hasGroup.id,
        })

        self.patch(type(self.env["res.partner"]).function, "groups", doesNotHaveGroupXmlId.complete_name)

        self.testView.write({
            "arch": '''
                <form>
                    <group>
                        <field name="function" groups="{hasgroup}" />
                        <field name="employee" groups="{doesnothavegroup}" />
                        <field name="display_name" />
                    </group>
                </form>
            '''.format(doesnothavegroup=doesNotHaveGroupXmlId.complete_name, hasgroup=hasGroupXmlId.complete_name)
        })
        self.start_tour("/web", 'web_studio_elements_with_groups_form', login="admin", timeout=600000)
        self.assertEqual(len(operations), 1)
        self.assertEqual(operations[0]["target"]["xpath_info"], [{'indice': 1, 'tag': 'form'}, {'indice': 1, 'tag': 'group'}, {'indice': 3, 'tag': 'field'}])
        studioView = _get_studio_view(self.testView)
        assertViewArchEqual(self, studioView.arch, """
            <data>
               <xpath expr="//field[@name='display_name']" position="after">
                 <field name="website"/>
               </xpath>
            </data>
        """)

    def test_element_group_in_sidebar(self):
        group = self.env["res.groups"].create({
            "name": "Test Group",
            "users": [Command.link(2)]
        })
        groupXmlId = self.env["ir.model.data"].create({
            "name": "test_group",
            "model": "res.groups",
            "module": "web_studio",
            "res_id": group.id,
        })

        self.testView.write({
            "arch": '''
                <form>
                    <field name="display_name" groups="{group}" />
                </form>
            '''.format(group=groupXmlId.complete_name)
        })
        self.start_tour("/web?debug=tests", 'test_element_group_in_sidebar', login="admin", timeout=600000)

    def test_create_one2many_lines_then_edit_name(self):
        self.testView.arch = '''
        <form>
            <group>
                <field name="name" />
            </group>
        </form>
        '''

        custom_fields_before_studio = self.env["ir.model.fields"].search([
            ("state", "=", "manual"),
        ])

        self.start_tour("/web?debug=tests", 'web_studio_test_create_one2many_lines_then_edit_name', login="admin", timeout=30000)

        custom_fields = self.env["ir.model.fields"].search_read([
            ("state", "=", "manual"),
            ("id", "not in", custom_fields_before_studio.ids),
        ], fields=["name", "ttype", "field_description"])

        self.maxDiff = None
        self.assertCountEqual(
            [{key: val for key, val in field.items() if key != 'id'} for field in custom_fields],
            [
                {"name": "x_studio_new_name", 'ttype': 'one2many', 'field_description': 'new name'},
                {"name": "x_name", 'ttype': 'char', 'field_description': 'Description'},
                {"name": "x_res_partner_id", 'ttype': 'many2one', 'field_description': 'X Res Partner'},
                {"name": "x_studio_sequence", 'ttype': 'integer', 'field_description': 'Sequence'},
            ]
        )

    def test_address_view_id_no_edit(self):
        self.testView.write({
            "arch": '''
                <form>
                    <div class="o_address_format">
                        <field name="lang"/>
                    </div>
                </form>
            '''
        })
        self.env.company.country_id.address_view_id = self.env.ref('base.view_partner_address_form')
        self.start_tour("/web?debug=tests", 'web_studio_test_address_view_id_no_edit', login="admin", timeout=200)

    def test_custom_selection_field_edit_values(self):
        self.testView.arch = '''
             <form>
                 <group>
                     <field name="name" />
                 </group>
             </form>
        '''

        self.start_tour("/web?debug=tests", 'web_studio_custom_selection_field_edit_values', login="admin", timeout=200)
        selection_field = self.env["ir.model.fields"].search(
            [
                ("state", "=", "manual"),
                ("model", "=", "res.partner"),
                ("ttype", "=", "selection")
            ],
            limit=1
        )

        self.assertCountEqual(selection_field.selection_ids.mapped("name"), ["some value", "another value"])

    def test_create_new_model_from_existing_view(self):
        self.testView.write({
            "model": "res.users",
            "type": "kanban",
            "arch": '''<kanban>
                <templates>
                    <t t-name="kanban-box">
                        <div class="oe_kanban_details">
                            <field name="display_name"/>
                        </div>
                    </t>
                </templates>
            </kanban>
            '''
        })
        self.testAction.view_ids.view_mode = "kanban"
        self.start_tour("/web?debug=tests", 'web_studio_test_create_new_model_from_existing_view', login="admin",
                        timeout=200)

    def test_create_model_with_clickable_stages(self):
        web_read_group = type(self.env["base"]).web_read_group
        @mute_logger("odoo.models")
        @api.model
        def muted_web_read_group(self, *args, **kwargs):
            return web_read_group(self, *args, **kwargs)

        self.patch(type(self.env["base"]), "web_read_group", muted_web_read_group)
        self.start_tour("/web?debug=tests", 'web_studio_test_create_model_with_clickable_stages', login="admin", timeout=200)

    def test_enter_x2many_edition_with_multiple_subviews(self):
        doesNotHaveGroup = self.env["res.groups"].create({
            "name": "studio does not have"
        })
        doesNotHaveGroupXmlId = self.env["ir.model.data"].create({
            "name": "studio_test_doesnothavegroup",
            "model": "res.groups",
            "module": "web_studio",
            "res_id": doesNotHaveGroup.id,
        })

        hasGroup = self.env["res.groups"].create({
            "name": "studio has group",
            "users": [Command.link(2)]
        })
        hasGroupXmlId = self.env["ir.model.data"].create({
            "name": "studio_test_hasgroup",
            "model": "res.groups",
            "module": "web_studio",
            "res_id": hasGroup.id,
        })

        self.testView.arch = '''
            <form>
                <field name="name"/>
                <field name="child_ids">
                    <tree groups="{hasgroup}">
                        <field name="type"/>
                    </tree>
                    <tree groups="{doesnothavegroup}">
                        <field name="name"/>
                    </tree>
                </field>
            </form>
        '''.format(doesnothavegroup=doesNotHaveGroupXmlId.complete_name, hasgroup=hasGroupXmlId.complete_name)
        self.start_tour("/web?debug=tests", 'web_studio_test_enter_x2many_edition_with_multiple_subviews',
                        login="admin", timeout=200)

    def test_enter_x2many_edition_with_multiple_subviews_correct_xpath(self):
        operations = []
        def edit_view_mocked(*args, **kwargs):
            operations.extend(kwargs["operations"] if "operations" in kwargs else args[3])

        watch_edit_view(self, edit_view_mocked)

        doesNotHaveGroup = self.env["res.groups"].create({
            "name": "studio does not have"
        })
        doesNotHaveGroupXmlId = self.env["ir.model.data"].create({
            "name": "studio_test_doesnothavegroup",
            "model": "res.groups",
            "module": "web_studio",
            "res_id": doesNotHaveGroup.id,
        })

        hasGroup = self.env["res.groups"].create({
            "name": "studio has group",
            "users": [Command.link(2)]
        })
        hasGroupXmlId = self.env["ir.model.data"].create({
            "name": "studio_test_hasgroup",
            "model": "res.groups",
            "module": "web_studio",
            "res_id": hasGroup.id,
        })

        self.testView.arch = '''
              <form>
                  <field name="name"/>
                  <field name="child_ids">
                      <tree groups="{doesnothavegroup}">
                          <field name="name"/>
                      </tree>
                      <tree groups="{hasgroup}">
                          <field name="name"/>
                      </tree>
                  </field>
              </form>
        '''.format(doesnothavegroup=doesNotHaveGroupXmlId.complete_name, hasgroup=hasGroupXmlId.complete_name)
        self.start_tour("/web?debug=tests", 'web_studio_test_enter_x2many_edition_with_multiple_subviews_correct_xpath',
                        login="admin", timeout=200)
        studioView = _get_studio_view(self.testView)
        assertViewArchEqual(self, studioView.arch, """
            <data>
               <xpath expr="//form[1]/field[@name='child_ids']/tree[2]/field[@name='name']" position="before">
                 <field name="active" optional="show"/>
               </xpath>
            </data>
        """)
        self.assertEqual(len(operations), 1)
        self.assertDictEqual(operations[0], {
            'type': 'add',
            'target': {
                'tag': 'field',
                'attrs': {
                    'name': 'name'
                },
                'xpath_info': [
                    {
                        'tag': 'tree',
                        'indice': 2
                    },
                    {
                        'tag': 'field',
                        'indice': 1
                    },
                ],
                'subview_xpath': "//field[@name='child_ids']/tree[2]",
            },
            'position': 'before',
            'node': {
                'tag': 'field',
                'attrs': {
                    'name': 'active',
                    'optional': 'show'
                }
            }
        })

    def test_studio_arch_has_measure_field_ids(self):
        view = self.env["ir.ui.view"].create({
            "name": "simple view",
            "model": "res.partner",
            "type": "pivot",
            "arch": '''
                <pivot>
                    <field name="display_name" type="measure"/>
                </pivot>
            '''
        })

        studio_view = self.env[view.model].with_context(studio=True).get_view(view.id, view.type)
        field_id = self.env['ir.model.fields'].search([('model', '=', view.model), ('name', 'in', ['display_name'])]).ids[0]

        assertViewArchEqual(self, studio_view["arch"], '''
            <pivot studio_pivot_measure_field_ids="[{field_id}]">
                <field name="display_name" type="measure"/>
            </pivot>
        '''.format(field_id=field_id))

    @mute_logger('odoo.addons.base.models.ir_ui_view')
    def test_postprocess_empty_groups_attribute(self):
        view = self.env["ir.ui.view"].create({
            "name": "simple view",
            "model": "res.partner",
            "type": "form",
            "arch": '''
                       <form>
                           <field name="display_name" groups=""/>
                       </form>
                   '''
        })
        studio_view = self.env[view.model].with_context(studio=True).get_view(view.id, view.type)
        assertViewArchEqual(self, studio_view["arch"], '''
            <form>
                <field name="display_name" on_change="1" modifiers="{&quot;readonly&quot;: true}" groups="" studio_groups="[]"/>
            </form>
        ''')

    def test_field_with_groups_in_tree_node_has_groups_too(self):
        # The field has a group in python in which the user is
        # The node has also a group in which the user is not
        hasGroup = self.env["res.groups"].create({
            "name": "studio has group",
            "users": [Command.link(self.env.user.id)]
        })
        hasGroupXmlId = self.env["ir.model.data"].create({
            "name": "studio_test_hasgroup",
            "model": "res.groups",
            "module": "web_studio",
            "res_id": hasGroup.id,
        })

        doesNotHaveGroup = self.env["res.groups"].create({
            "name": "studio does not have"
        })
        doesNotHaveGroupXmlId = self.env["ir.model.data"].create({
            "name": "studio_test_doesnothavegroup",
            "model": "res.groups",
            "module": "web_studio",
            "res_id": doesNotHaveGroup.id,
        })

        self.patch(type(self.env["res.partner"]).title, "groups", hasGroupXmlId.complete_name)

        view = self.env["ir.ui.view"].create({
            "name": "simple view",
            "model": "res.partner",
            "type": "tree",
            "arch": '''
                <tree>
                    <field name="display_name"/>
                    <field name="title" groups="{doesnothavegroup}" />
                </tree>
            '''.format(doesnothavegroup=doesNotHaveGroupXmlId.complete_name)
        })
        arch = self.env[view.model].with_context(studio=True).get_view(view.id, view.type)["arch"]

        studio_groups = json.dumps([{
            "id": doesNotHaveGroup.id,
            "name": doesNotHaveGroup.name,
            "display_name": doesNotHaveGroup.display_name,
        }])

        modifiers = json.dumps({"column_invisible": True})
        xml_temp = etree.Element("field", dict(name="title", modifiers=modifiers, groups=doesNotHaveGroupXmlId.complete_name, studio_groups=studio_groups))

        expected = '''
            <tree>
               <field name="display_name" on_change="1" modifiers="{modifiers}"/>
               {xml_stringified}
             </tree>
        '''.format(modifiers="{&quot;readonly&quot;: true}", xml_stringified=etree.tostring(xml_temp).decode("utf-8"))

        assertViewArchEqual(self, arch, expected)

    def test_studio_view_is_last(self):
        # The studio view created should have, in all cases, a priority greater than all views
        # that are part of the inheritance
        self.testView.arch = '''
            <form><sheet>
                <group><field name="name" /></group>
            </sheet></form>
        '''

        self.env["ir.ui.view"].create({
            "name": "simple view inherit",
            "inherit_id": self.testView.id,
            "mode": "extension",
            "priority": 123,
            "model": "res.partner",
            "type": "form",
            "arch": '''
                <data>
                <xpath expr="//field[@name='name']" position="after">
                    <field name="title" />
                </xpath>
                </data>
            '''
        })

        self.start_tour("/web?debug=tests", 'web_studio_test_studio_view_is_last', login="admin", timeout=200)
        studioView = _get_studio_view(self.testView)
        self.assertEqual(studioView.priority, 1230)

        self.maxDiff = None
        assertViewArchEqual(self, studioView["arch"], '''
            <data>
                <xpath expr="//field[@name='title']" position="after">
                  <field name="website"/>
                </xpath>
            </data>
        ''')

    def test_edit_form_subview_attributes(self):
        self.testView.arch = '''
            <form>
                <field name="child_ids">
                    <form>
                        <field name="display_name" />
                    </form>
                </field>
            </form>
        '''

        self.start_tour("/web?debug=tests", 'web_studio_test_edit_form_subview_attributes', login="admin",
                        timeout=200)

        studioView = _get_studio_view(self.testView)
        assertViewArchEqual(self, studioView.arch, """
            <data>
                <xpath expr="//form[1]/field[@name='child_ids']/form[1]" position="attributes">
                    <attribute name="create">false</attribute>
                </xpath>
            </data>""")

    def test_move_similar_field(self):
        self.testView.arch = '''
            <form>
                <sheet>
                    <group><group>
                        <field name="active" />
                    </group></group>
                    <notebook>
                        <page string="one">
                            <group><group><field name="display_name" /></group></group>
                        </page>
                        <page string="two">
                            <group><group><field name="display_name" /></group></group>
                        </page>
                   </notebook>
                </sheet>
            </form>
        '''

        self.start_tour("/web?debug=tests", 'web_studio_test_move_similar_field', login="admin", timeout=400)

        studioView = _get_studio_view(self.testView)
        assertViewArchEqual(self, studioView.arch, '''
        <data>
            <xpath expr="//field[@name='active']" position="before">
                <xpath expr="//form[1]/sheet[1]/notebook[1]/page[2]/group[1]/group[1]/field[@name='display_name']" position="move" />
            </xpath>
        </data>
        ''')

    def create_user_view(self):
        self.testView.write({
            "name": "simple user",
            "model": "res.users",
            "arch": '''
                <form>
                    <group>
                        <field name="name"/>
                    </group>
                </form>
            '''
        })
        self.testAction.write({
            "name": "simple user",
            "res_model": "res.users",
        })
        self.testActionXmlId.name = "studio_test_user_action"
        self.testMenu.name = "Studio Test User"
        self.testMenuXmlId.name = "studio_test_user_menu"

    def test_related_binary_field_with_filename(self):
        self.create_user_view()

        partner_field = self.env["ir.model.fields"].create({
            "field_description": "New File",
            "name": "x_new_file",
            "ttype": "binary",
            "model": "res.partner",
            "model_id": self.env["ir.model"]._get('res.partner').id,
            "state": "manual",
        })
        self.env["ir.model.fields"].create({
            "field_description": "New File filename",
            "name": "x_new_file_filename",
            "ttype": "char",
            "model": "res.partner",
            "model_id": self.env["ir.model"]._get('res.partner').id,
            "state": "manual",
        })

        self.start_tour("/web?debug=tests", 'web_studio_test_related_file', login="admin", timeout=400)

        studioView = _get_studio_view(self.testView)
        binary_field = self.env["ir.model.fields"].search([('model', '=', 'res.users'), ('ttype', '=', 'binary'), ('name', 'like', 'x_studio_related')])
        self.assertEqual(len(binary_field), 1)
        self.assertEqual(binary_field.related_field_id, partner_field)
        assertViewArchEqual(self, studioView.arch,
        '''
        <data>
            <xpath expr="//form[1]/group[1]/field[@name=\'name\']" position="before">
                <field filename="{binary_field.name}_filename" name="{binary_field.name}"/>
                <field invisible="1" name="{binary_field.name}_filename"/>
            </xpath>
        </data>
        '''.format(binary_field=binary_field))

    def test_nested_related_binary_field_with_filename(self):
        self.create_user_view()

        self.env["ir.model.fields"].create({
            "field_description": "New File",
            "name": "x_new_file",
            "ttype": "binary",
            "model": "res.partner.category",
            "model_id": self.env["ir.model"]._get('res.partner.category').id,
            "state": "manual",
        })
        self.env["ir.model.fields"].create({
            "field_description": "New File filename",
            "name": "x_new_file_filename",
            "ttype": "char",
            "model": "res.partner.category",
            "model_id": self.env["ir.model"]._get('res.partner.category').id,
            "state": "manual",
        })

        partner_field = self.env["ir.model.fields"].create({
            "field_description": "New File",
            "name": "x_new_related_file",
            "ttype": "binary",
            "model": "res.partner",
            "model_id": self.env["ir.model"]._get('res.partner').id,
            "state": "manual",
            "related": "category_id.x_new_file"
        })
        self.env["ir.model.fields"].create({
            "field_description": "New File filename",
            "name": "x_new_related_file_filename",
            "ttype": "char",
            "model": "res.partner",
            "model_id": self.env["ir.model"]._get('res.partner').id,
            "state": "manual",
            "related": "category_id.x_new_file_filename"
        })

        self.start_tour("/web?debug=tests", 'web_studio_test_related_file', login="admin", timeout=400)

        studioView = _get_studio_view(self.testView)
        binary_field = self.env["ir.model.fields"].search([('model', '=', 'res.users'), ('ttype', '=', 'binary'), ('name', 'like', 'x_studio_related')])
        self.assertEqual(len(binary_field), 1)
        self.assertEqual(binary_field.related_field_id, partner_field)
        assertViewArchEqual(self, studioView.arch,
        '''
        <data>
            <xpath expr="//form[1]/group[1]/field[@name=\'name\']" position="before">
                <field filename="{binary_field.name}_filename" name="{binary_field.name}"/>
                <field invisible="1" name="{binary_field.name}_filename"/>
            </xpath>
        </data>
        '''.format(binary_field=binary_field))

    def test_related_binary_field_without_filename(self):
        self.create_user_view()

        partner_field = self.env["ir.model.fields"].create({
            "field_description": "New File",
            "name": "x_new_file",
            "ttype": "binary",
            "model": "res.partner",
            "model_id": self.env["ir.model"]._get('res.partner').id,
            "state": "manual",
        })

        self.start_tour("/web?debug=tests", 'web_studio_test_related_file', login="admin", timeout=400)

        studioView = _get_studio_view(self.testView)
        binary_field = self.env["ir.model.fields"].search([('model', '=', 'res.users'), ('ttype', '=', 'binary'), ('name', 'like', 'x_studio_related')])
        self.assertEqual(len(binary_field), 1)
        self.assertEqual(binary_field.related_field_id, partner_field)
        assertViewArchEqual(self, studioView.arch,
        '''
        <data>
            <xpath expr="//form[1]/group[1]/field[@name=\'name\']" position="before">
                <field name="{binary_field.name}"/>
            </xpath>
        </data>
        '''.format(binary_field=binary_field))

    def test_edit_modifier_domain(self):
        self.testView.write({
            "arch": '''
                <form>
                    <group>
                        <field name="display_name"/>
                        <field name="user_id"/>
                        <field name="company_name" attrs="{'invisible': [('user_id', '=', 1)]}"/>
                    </group>
                </form>
            '''
        })
        self.start_tour("/web?debug=tests", 'web_studio_test_edit_modifier_domain', login="admin")
        self.assertXMLEqual(self.testView.get_combined_arch(),
            '''
                <form>
                    <group>
                        <field name="display_name"/>
                        <field name="user_id"/>
                        <field name="company_name" attrs="{&quot;invisible&quot;: [[&quot;user_id&quot;,&quot;=&quot;,1]]}" required="1"/>
                    </group>
                </form>
            '''
        )

    def test_drag_and_drop_boolean(self):
        self.testView.arch = '''
             <form>
                 <group>
                    <field name="name" />
                 </group>
             </form>
        '''

        self.start_tour("/web?debug=tests", 'we_studio_boolean_field_drag_and_drop', login="admin", timeout=200)

        studioView = _get_studio_view(self.testView)
        boolean_field = self.env['ir.model.fields'].search([('name', 'like', 'x_studio_boolean')])[0]

        assertViewArchEqual(self, studioView.arch, '''
             <data>
                <xpath expr="//form[1]/group[1]/field[@name='name']" position="after">
                    <field name="{boolean_field.name}"/>
                </xpath>
            </data>
        '''.format(boolean_field=boolean_field))

    def test_add_button_xml_id(self):
        base_view = self.env["ir.ui.view"].create({
            "name": "test_partner_simple",
            "model": "res.partner",
            "mode": "primary",
            "type": "form",
            "arch": """<form><sheet><div class="oe_button_box"></div></sheet></form>"""
        })

        operations = [
            {
                "type": "add",
                "target": {
                    "tag": "div",
                    "attrs": {
                        "class": "oe_button_box"
                    }
                },
                "view_id": base_view.id,
                "position": "inside",
                "node": {
                    "tag": "button",
                    "field": self.env["ir.model.fields"]._get("res.partner", "parent_id").id,
                    "string": "aa",
                    "attrs": {
                        "class": "oe_stat_button",
                        "icon": "fa-diamond"
                    }
                }
            }
        ]

        with mute_logger("odoo.addons.base.models.ir_ui_view"):
            self.authenticate("admin", "admin")
            self.url_open("/web_studio/edit_view", data=json.dumps({
                "params": {
                    "view_id": base_view.id,
                    "model": "res.partner",
                    "studio_view_arch": "<data />",
                    "operations": operations,
                    "context": {"studio": 1},
                }
            }), headers={"Content-Type": "application/json"})

        action = self.env["ir.actions.act_window"].search([], limit=1, order="create_date DESC")
        self.assertTrue(action.xml_id.startswith("studio_customization."))
        form = base_view.get_combined_arch()
        self.assertXMLEqual(form, f"""
        <form>
           <sheet>
             <div class="oe_button_box">
               <button class="oe_stat_button" icon="fa-diamond" type="action" name="{action.xml_id}">
                 <field widget="statinfo" name="x_parent_id_res_partner_count" string="aa"/>
               </button>
             </div>
           </sheet>
        </form>
        """)

    def test_remove_column_invisible_when_setting_invisible_domain(self):
        self.testView.write({
            "type": "tree",
            "arch": '''
                <tree>
                    <field name="display_name"/>
                    <field name="user_id" attrs="{'column_invisible': True}"/>
                </tree>
            '''
        })
        self.testAction.write({
            "view_ids": [Command.clear(), Command.create({"view_id": self.testView.id, "view_mode": "tree"})]
        })
        self.start_tour("/web?debug=tests", 'web_studio_test_remove_column_invisible_when_setting_invisible_domain', login="admin")
        self.assertXMLEqual(self.testView.get_combined_arch(),
        '''
                <tree>
                    <field name="display_name"/>
                    <field name="user_id" attrs="{&quot;invisible&quot;: [[&quot;id&quot;,&quot;=&quot;,1]]}"/>
                </tree>
            '''
        )
