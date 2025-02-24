# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from odoo import api, models
from odoo.osv import expression


class DiscussChannelMember(models.Model):
    _inherit = 'discuss.channel.member'

    @api.autovacuum
    def _gc_unpin_whatsapp_channels(self):
        """ Unpin read whatsapp channels with no activity for at least one day to
            clean the operator's interface """
        one_day_ago = datetime.now() - timedelta(days=1)
        two_weeks_ago = datetime.now() - timedelta(weeks=2)
        members = self.env['discuss.channel.member'].search(expression.AND([
            [("is_pinned", "=", True)],
            [("channel_id.channel_type", "=", "whatsapp")],
            expression.OR([
                [("last_seen_dt", "<", one_day_ago)],
                [
                    ("last_seen_dt", "=", False),
                    ("channel_id.create_date", "<=", two_weeks_ago),
                ],
            ]),
        ]), limit=1000)
        members_to_be_unpinned = members.filtered(
            lambda m: m.message_unread_counter == 0 or (not m.last_seen_dt and m.channel_id.create_date <= two_weeks_ago) or m.last_seen_dt <= two_weeks_ago
        )
        members_to_be_unpinned.is_pinned = False
        self.env['bus.bus']._sendmany([
            (member.partner_id, 'discuss.channel/unpin', {'id': member.channel_id.id})
            for member in members_to_be_unpinned
        ])
