from odoo import http
from odoo.http import request


class ChatterPosition(http.Controller):
    @http.route(
        ["/configurable_chatter_position"],
        type="json",
    )
    def onchange_chatter_position(self, auth="user", **kw):
        """
            Endpoint to update (store) the chatter position chosen by the user
        """
        user = (
            request.env["res.users"].sudo().with_context(active_test=False).search([("id", "=", request.session.uid)])
        )
        if user.context_chatter_position == "chatter_right":
            user.context_chatter_position = "chatter_bottom"
        else:
            user.context_chatter_position = "chatter_right"
        return user.context_chatter_position
