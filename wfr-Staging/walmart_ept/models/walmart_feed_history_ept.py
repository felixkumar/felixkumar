import logging

from odoo.exceptions import ValidationError

from odoo import models, fields, _

_logger = logging.getLogger("walmart_feed_history")

class WalmartFeedHistory(models.Model):
    _name = 'walmart.feed.history.ept'
    _description = 'Walmart Feed Submission History'
    _rec_name = 'feed_id'

    feed_id = fields.Char(string='Feed Result ID',
                          help="A unique ID used for tracking the Feed File")
    feed_request = fields.Text(help='Request for Feed')
    feed_response = fields.Text(help="Response that we get after requesting for Feed.")
    marketplace_id = fields.Many2one('walmart.marketplace.ept', help="Walmart Marketplace")

    def get_feed_submission_history(self):
        """
        This method Feed Feeds are constructed to handle bulk functions.
        Which is give to Particular details for the Update Any like (Product Price, Stock etc)
        @param None.
        @return: True
        """
        walmart_log_line_obj = self.env['common.log.lines.ept']

        marketplace_id = self.marketplace_id
        if not self.feed_id:
            raise ValidationError(_("Feed Result ID Not Set"))

        walmart_conn_obj = marketplace_id.get_walmart_connection()
        try:
            response = walmart_conn_obj.feed.get_status(feed_id=self.feed_id)
            if not response or not response.get('feedId', False):
                message = '{} - Feed Result not Found...!'.format(self.feed_id)
                walmart_log_line_obj.create_common_log_line_ept(
                    message=message, module='walmart_ept', res_id=False, walmart_marketplace_id=marketplace_id.id,
                    model_name=self._name, log_line_type='fail', mismatch_details=False,
                    operation_type="import")
            else:
                self.write({"feed_response": response})
        except Exception as err:
            _logger.exception(err)
            raise ValidationError(str(err))
        return True
