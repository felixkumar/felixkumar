# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions


class SignTemplate(models.Model):
    _name = 'sign.template'
    _inherit = ['sign.template', 'documents.mixin']

    folder_id = fields.Many2one('documents.folder', 'Signed Document Workspace')
    documents_tag_ids = fields.Many2many('documents.tag', string="Signed Document Tags")

    def _can_take_ownership_of_attachment(self, attachment):
        """ If the attachment is owned by a document, the ownership can be transferred to the sign template. """
        if attachment.res_model == 'documents.document':
            return True
        return super()._can_take_ownership_of_attachment(attachment)

    @api.model_create_multi
    def create(self, vals_list):
        return super(SignTemplate, self.with_context(no_document=True))\
            .create(vals_list)\
            .with_context(no_document=bool(self._context.get('no_document')))

    def _get_document_tags(self):
        return self.documents_tag_ids

    def _get_document_folder(self):
        return self.folder_id
