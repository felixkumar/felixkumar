# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from markupsafe import Markup

from odoo.addons.mrp_workorder.tests import test_tablet_client_action
from odoo.tests import Form, HttpCase, tagged

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestPickingWorkorderClientActionSuggestImprovementPlm(test_tablet_client_action.TestWorkorderClientActionCommon, HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.ref('base.group_user').implied_ids += (
            cls.env.ref('mrp_workorder.group_mrp_wo_tablet_timer')
        )

    def test_add_step_plm(self):
        """ Add 2 new steps as instruction in the tablet view via the 'suggest
        worksheet improvement' and check that corresponding PLM ECO's BoM steps are correct:
         - One with title + instructions,
         - One with no title or instructions (i.e. check no 'False' values displayed) """
        mo_form = Form(self.env['mrp.production'])
        mo_form.product_id = self.potion
        mo = mo_form.save()
        mo.action_confirm()
        self.assertEqual(len(mo.workorder_ids.check_ids), 2)
        wo = mo.workorder_ids[0]
        wo.button_start()
        url = self._get_client_action_url(wo.id)

        self.start_tour(url, 'test_add_step', login='admin', timeout=120)

        eco = self.env['mrp.eco'].search([('product_tmpl_id', "=", self.potion.product_tmpl_id.id)])
        self.assertEqual(len(eco), 1, 'An ECO should have been auto-created for the product')
        eco_steps = eco.new_bom_id.operation_ids.quality_point_ids
        self.assertEqual(len(eco_steps), 4, 'The 2 original steps + 2 added steps should be in the ECO BoM')
        original_steps = mo.bom_id.operation_ids.quality_point_ids
        eco_step = eco_steps[0]
        self.assertEqual(eco_step.note, original_steps[0].note, "original step should have been copied without any changes")
        eco_step = eco_steps[1]
        self.assertEqual(eco_step.note, original_steps[1].note, "original step should have been copied without any changes")
        eco_step = eco_steps[2]
        self.assertEqual(eco_step.title, "New Step Suggestion: New Magical Step", "New step title was not correctly added")
        self.assertEqual(eco_step.note, "<p>Do extra magic</p>", "New step instruction was not correctly added")
        eco_step = eco_steps[3]
        self.assertEqual(eco_step.title, "New Step Suggestion: ", "(Blank) new step title was not correctly added")
        self.assertFalse(eco_step.note, "Blank instruction was not correctly added")

        messages = self.env['mail.message'].search([('model', '=', 'mrp.bom'), ('res_id', '=', mo.bom_id.id)])
        self.assertEqual(len(messages), 0, "New step instruction should be empty")

    def test_remove_step_plm(self):
        """ Removes steps in the tablet view via the 'suggest
        worksheet improvement' and check that original BoM steps' chatter messages + PLM ECO BoM steps are correct:
        - Existing BoM step with a comment (for why step should be removed),
        - Existing BoM step without a comment, i.e. check no 'False' values displayed
        - An added step (via 'suggest worksheet improvement'), i.e. check no activity created and tablet
        """
        mo_form = Form(self.env['mrp.production'])
        mo_form.product_id = self.potion
        mo = mo_form.save()
        mo.action_confirm()
        self.assertEqual(len(mo.workorder_ids.check_ids), 2)
        wo = mo.workorder_ids[0]
        wo.button_start()
        url = self._get_client_action_url(wo.id)

        self.start_tour(url, 'test_remove_step', login='admin', timeout=120)

        # check that original BoM steps have chatter messages about step deletion suggestions
        messages = self.env['mail.message'].search([('model', '=', 'quality.point'), ('res_id', 'in', mo.bom_id.operation_ids.quality_point_ids.ids)], order='id asc')
        self.assertEqual(len(messages), 2, "there should be 2 chatter messages in existing BoM steps about suggested step deletion")
        message = messages[0]
        self.assertEqual(message.body, Markup('<span><b>Mitchell Admin suggests to delete this instruction</b><br><b>Reason:</b> The magic is already within me</span>'))
        message = messages[1]
        self.assertEqual(message.body, Markup('<b>Mitchell Admin suggests to delete this instruction</b>'))

        eco = self.env['mrp.eco'].search([('product_tmpl_id', "=", self.potion.product_tmpl_id.id)])
        self.assertEqual(len(eco), 1, "An ECO should have been auto-created for the product")
        eco_steps = eco.new_bom_id.operation_ids.quality_point_ids
        self.assertEqual(len(eco_steps), 0, "All steps should have been deleted from the ECO BoM")
        self.assertEqual(len(wo.check_ids), 2, "Only original BoM's steps should be left in the WO")

    def test_update_instructions_plm(self):
        """ 'Update Instructions' for a step in the tablet view via the 'suggest
        worksheet improvement' under different conditions and check that the tablet view + PLM BoM + chatter correctly update:
        - Existing BoM step with no title provided (i.e. keep original title) + no note + no comment, i.e. check no 'False' values displayed
        - Existing BoM step with a title + note + comment
        - A removed step, i.e. check chatter record is created for its update"""
        mo_form = Form(self.env['mrp.production'])
        mo_form.product_id = self.potion
        mo = mo_form.save()
        mo.action_confirm()
        self.assertEqual(len(mo.workorder_ids.check_ids), 2)
        wo = mo.workorder_ids[0]
        wo.button_start()
        url = self._get_client_action_url(wo.id)

        self.start_tour(url, 'test_update_step', login='admin', timeout=120)

        eco = self.env['mrp.eco'].search([('product_tmpl_id', "=", self.potion.product_tmpl_id.id)])
        self.assertEqual(len(eco), 1, "An ECO should have been auto-created for the product")
        eco_step = eco.new_bom_id.operation_ids.quality_point_ids
        self.assertEqual(len(eco_step), 1, "One of the steps should have been deleted from the ECO BoM and only 1 should remain")

        # check step update chatter messages
        messages = self.env['mail.message'].search([('model', '=', 'quality.point'), ('res_id', '=', eco_step.id)], order='id asc')
        self.assertEqual(len(messages), 3, "there should be 2 chatter messages in PLM ECO BoM step about suggested updates + 1 for the record creation")
        message = messages[1]
        self.assertEqual(message.body, Markup('<b>New Instruction suggested by Mitchell Admin</b>'), "No title + no instruction + no comment = only suggested line")
        message = messages[2]
        self.assertEqual(message.body, Markup('<b>New Instruction suggested by Mitchell Admin</b><br><p>This is the step before magic is done</p><br><b>Reason:</b> This step was inaccurate<br><b>New Title suggested: Pre-magic Step</b>'))

        activity = eco.activity_ids
        self.assertEqual(len(activity), 1, "there should be 1 chatter message in PLM ECO about suggested updates for missing step")
        self.assertEqual(activity.summary, 'BoM feedback for not found step: %s (%s)' % (self.wizarding_step_2.title, mo.name))
        self.assertEqual(activity.note, Markup('<b>New Instruction suggested by Mitchell Admin</b><br><p>What will happen with this update?!</p>'))

    def test_update_instructions_w_images_plm(self):
        """ 'Update Instructions' for a step in the tablet view via the 'suggest
        worksheet improvement' when images are involved. Since updating/checking images in a tour is a pain,
        only do this via backend and check that the PLM ECO BoM + chatter correctly update:
        - Step with no image + update with an new_image => instruction should be: completely overwritten (only new_image)
        - Step with image and text + update only with 'new_text' => instruction should be: 'new_text' + image
        - Step with image + update with new_image + 'new_text' => instruction should be: new_image + 'new_text' """

        mo_form = Form(self.env['mrp.production'])
        mo_form.product_id = self.potion
        mo = mo_form.save()
        mo.action_confirm()
        self.assertEqual(len(mo.workorder_ids.check_ids), 2)
        wo = mo.workorder_ids[0]
        wo.button_start()

        image = Markup(self.step_image_html)
        updated_note = "Improved magic instructions"
        updated_image = Markup('<p><img src="/stock/static/description/icon.png"></p>')

        # update existing BoM step containing only text instructions with only an image
        action = wo.action_propose_change('update_step', "Update Current Step")
        update_step_form = Form(self.env[action['res_model']].with_context(action['context']), view=action['views'][0][0])
        update_step_form.note = image
        update_step = update_step_form.save()
        update_step.with_user(self.user_admin).process()

        eco = self.env['mrp.eco'].search([('product_tmpl_id', "=", self.potion.product_tmpl_id.id)])
        self.assertEqual(len(eco), 1, "An ECO should have been auto-created for the product")
        eco_steps = eco.new_bom_id.operation_ids.quality_point_ids
        self.assertEqual(len(eco_steps), 2)
        eco_step = eco_steps[0]
        self.assertEqual(eco_step.note, image, "Step's note should have been updated to only be the new instruction image")
        messages = self.env['mail.message'].search([('model', '=', 'quality.point'), ('res_id', '=', eco_step.id)], order='id asc')
        self.assertEqual(len(messages), 2, "there should be 1 chatter messages in PLM BoM step about suggested updates + 1 for the record creation")
        self.assertEqual(messages[1].body, Markup('<b>New Instruction suggested by Mitchell Admin</b><br>') + image, "updated instructions should be recorded in chatter")

        # update existing BoM step containing text + image instructions with only text
        wo.current_quality_check_id = wo.check_ids[1]
        action = wo.action_propose_change('update_step', "Update Current Step")
        update_step_form = Form(self.env[action['res_model']].with_context(action['context']), view=action['views'][0][0])
        update_step_form.note = updated_note
        update_step = update_step_form.save()
        update_step.with_user(self.user_admin).process()
        eco_step = eco_steps[1]
        self.assertEqual(eco_step.note, Markup("<p>%s</p>" % updated_note) + image, "Step's note should have been updated to updated text + original image")

        # update existing BoM step containing text + image instructions with image + text
        action = wo.action_propose_change('update_step', "Update Current Step")
        update_step_form = Form(self.env[action['res_model']].with_context(action['context']), view=action['views'][0][0])
        update_step_form.note = updated_image + Markup("<p>%s</p>" % updated_note)
        update_step = update_step_form.save()
        update_step.with_user(self.user_admin).process()
        self.assertEqual(eco_step.note, updated_image + Markup("<p>%s</p>" % updated_note), "Step's note should have been updated to updated text + original image")

        # check corresponding chatter messages of ECO BoM step
        messages = self.env['mail.message'].search([('model', '=', 'quality.point'), ('res_id', '=', eco_step.id)], order='id asc')
        self.assertEqual(len(messages), 3, "there should be 2 chatter messages in PLM BoM step about suggested updates + 1 for the record creation")
        self.assertEqual(messages[1].body, Markup('<b>New Instruction suggested by Mitchell Admin</b><br><p>%s</p>' % updated_note), "Only the updated text instructions should be in chatter message to avoid wasting db space with unnecessary images")
        self.assertEqual(messages[2].body, Markup('<b>New Instruction suggested by Mitchell Admin</b><br>') + updated_image + Markup('<p>%s</p>' % updated_note))
