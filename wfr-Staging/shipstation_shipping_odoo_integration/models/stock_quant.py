import base64
import json
import logging
from requests import request
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ShipstationPackageDetails(models.Model):
    _inherit = "stock.quant.package"
    custom_tracking_number = fields.Char(string="Shipstation Tracking Number",
                                         help="If tracking number available print it in this field.")
    is_generate_label_in_shipstation = fields.Boolean(default=True, string="Is Generate Label In Shipstation.?",
                                                      help="If user do not need to generate the label then we need to Set value false. ")
    response_message = fields.Char(string="Response Message")
    carrier_id = fields.Many2one('delivery.carrier', string="Carrier")
    shipstation_shipment_id = fields.Char(string="Shipstation Shipment", help="Shipstation Shipment ID.", copy=False)

    def api_calling_function(self, url_data, body):
        configuration = self.env['shipstation.odoo.configuration.vts'].search([], limit=1)
        if not configuration:
            raise ValidationError("Configuration Not Done.")
        url = configuration.making_shipstation_url(url_data)
        api_secret = configuration.api_secret
        api_key = configuration.api_key
        data = "%s:%s" % (api_key, api_secret)
        encode_data = base64.b64encode(data.encode("utf-8"))
        authrization_data = "Basic %s" % (encode_data.decode("utf-8"))
        headers = {"Authorization": authrization_data,
                   "Content-Type": "application/json"}
        data = json.dumps(body)
        _logger.info("Request Data: %s" % (data))
        try:
            response_body = request(method='POST', url=url, data=data, headers=headers)
        except Exception as e:
            raise ValidationError(e)
        return response_body

    def shipstation_cancel_shipment(self):
        shipment_id = self.shipstation_shipment_id
        if not shipment_id:
            raise ValidationError("Shipstation Shipment Id Not Available!")
        req_data = {"shipmentId": shipment_id}
        try:
            response_data = self.api_calling_function("/shipments/voidlabel", req_data)
            if response_data.status_code == 200:
                responses = response_data.json()
                _logger.info("Response Data: %s" % (responses))
                approved = responses.get('approved')
                if approved:
                    return {
                        'effect': {
                            'fadeout': 'slow',
                            'message': 'Shipment Cancelled In Shipstation %s' % (shipment_id),
                            'img_url': '/web/static/img/smile.svg',
                            'type': 'rainbow_man',
                        }
                    }
            else:
                error_code = "%s" % (response_data.status_code)
                error_message = response_data.reason
                error_detail = {'error': error_code + " - " + error_message + " - "}
                if response_data.json():
                    error_detail = {'error': error_code + " - " + error_message + " - %s" % (response_data.json())}
                raise ValidationError(error_detail)
        except Exception as e:
            raise ValidationError(e)
