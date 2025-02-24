# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.exceptions import MissingError
from odoo.http import request


class SocialValidationException(Exception):
    pass


class SocialController(http.Controller):

    def _get_social_stream_post(self, stream_post_id, media_type):
        """ Small utility method that fetches the post and checks it belongs
        to the correct media_type """
        stream_post = request.env['social.stream.post'].search([
            ('id', '=', stream_post_id),
            ('stream_id.account_id.media_id.media_type', '=', media_type),
        ])
        if not stream_post:
            raise MissingError(_("Uh-oh! It looks like this message has been deleted from X."))

        return stream_post
