import os
import base64
import binascii
import logging
from requests import request
from PyPDF2 import PdfFileMerger
from odoo.exceptions import ValidationError
from odoo import fields, models, api, _
from odoo.tools import pdf

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    shipstation_order_id = fields.Char(string="Shipstation Order ID", copy=False)
    shipstation_order_key = fields.Char(string="Shipstation Order Key", copy=False)
    shipstation_shipment_id = fields.Char(string="Shipstation Shipment ID", copy=False)
    is_order_imported_in_shipstation = fields.Boolean("Imported Shipstation Shipment", copy=False, default=False,
                                                      help="If Checked, This order is Imported From shipstation.")
    shipstation_service_code = fields.Char(string="Shipstation Shipment Wise Service Code", copy=False)
    shipstation_weight = fields.Float(string='Shipstation Order Weight')
    shipstation_unit_of_measure = fields.Char(string='Shipstation Units')
    shipstation_carrier_code = fields.Char(string='Carrier Code')
    shipstation_sale_order_number = fields.Char(string="Shipstation Order Number", copy=False)
    shipstation_batch_number = fields.Char(string='Shipstation Batch')
    shipment_cost = fields.Float(string='Shipment Cost')
    shipstation_configuration_id = fields.Many2one('shipstation.odoo.configuration.vts',
                                                   string='Shipstation Configuration')

    def update_order_in_shipstation(self):
        self.ensure_one()
        if not self.carrier_id:
            raise ValidationError("Please set proper delivery method")
        try:
            body = self.carrier_id and self.carrier_id.create_or_update_order(self)
            response_data = self.carrier_id and self.carrier_id.api_calling_function("/orders/createorder", body)
            if response_data.status_code == 200:
                responses = response_data.json()
                order_id = responses.get('orderId')
                order_key = responses.get('orderKey')
                if order_id:
                    self.shipstation_order_id = order_id
                    self.shipstation_order_key = order_key
            else:
                error_code = "%s" % (response_data.status_code)
                error_message = response_data.reason
                error_detail = {'error': error_code + " - " + error_message + " - "}
                if response_data.json():
                    error_detail = {'error': error_code + " - " + error_message + " - %s" % (response_data.json())}
                raise ValidationError(error_detail)
        except Exception as e:
            raise ValidationError(e)

    def generate_label_from_shipstation(self):
        _logger.info(">>>>>>>>>>>>>>>>>> Generate Lebel")
        shipment_cost = 0.0
        self.ensure_one()
        if not self.carrier_id:
            raise ValidationError("Please set proper delivery method")
        final_tracking_number = []
        input_path = []
        label_datas = []
        file_name = self.name
        pdf_merger = PdfFileMerger()
        file_name = file_name.replace('/', '_')
        file_path = "/tmp/waves/"
        directory = os.path.dirname(file_path)
        try:
            os.stat(directory)
        except:
            os.system("mkdir %s" % (file_path))
        error_detail = ""
        if any(move.product_id.weight <= 0.0 for move in self.move_ids):
            raise ValidationError("Need to set Product Weight.")
        for package_id in self.package_ids:
            _logger.info("Inside Package : %s" % (package_id))
            try:
                if not package_id.is_generate_label_in_shipstation:
                    continue
                weight = package_id.shipping_weight
                carrier_id = package_id.carrier_id if package_id.carrier_id else self.carrier_id
                body = carrier_id.generate_label_from_shipstation(self, package_id, weight)
                _logger.info("Label Body >>>>>>>>>>> : %s" % (body))
                # response_data = carrier_id.api_calling_function("/shipments/createlabel", body, self.sale_id.shipstation_warehouse_address_id)
                response_data = carrier_id.api_calling_function("/orders/createlabelfororder", body)
                _logger.info("Label Response Data: %s" % (response_data))
                if response_data.status_code == 200:
                    responses = response_data.json()
                    _logger.info("Label Responsese >>>> After 200 : %s" % (responses))
                    shipment_id = responses.get('shipmentId')
                    if shipment_id:
                        self.shipstation_shipment_id = shipment_id
                        label_data = responses.get('labelData')
                        tracking_number = responses.get('trackingNumber')
                        shipment_cost += responses.get('shipmentCost')
                        final_tracking_number.append(tracking_number)
                        base_data = binascii.a2b_base64(str(label_data))
                        label_datas.append(base_data)
                        tracking_message = (_("Shipstation Tracking Number: </b>%s") % (tracking_number))
                        message_id = self.message_post(
                            body=tracking_message)  # attachments=[('%s_Shipstation_Tracking_%s.pdf' % (self.name ,tracking_number), base_data)]
                        package_id.response_message = "Sucessfully Label Generated"
                        package_id.custom_tracking_number = tracking_number
                        package_id.shipstation_shipment_id = shipment_id
                        input_path.append("%s_%s.pdf" % (file_path, tracking_number))
                        # with open("%s_%s.pdf" % (file_path, tracking_number), "ab") as f:
                        #     f.write(base64.b64decode(message_id and message_id.attachment_ids[0] and message_id.attachment_ids[0].datas))
                        logmessage = _("<b>Tracking Numbers:</b> %s") % (tracking_number)
                        label_data_pdf = binascii.a2b_base64(str(label_data))
                        self.message_post(body=logmessage, attachments=[("%s.pdf" % (self.id), label_data_pdf)])
                else:
                    error_code = "%s" % (response_data.status_code)
                    _logger.info("ERROR CODE: %s" % (error_code))
                    error_message = response_data.reason
                    _logger.info("Package : ERROR Response: %s" % (response_data))
                    error_detail = {'error': error_code + " - " + error_message + " - %s" % (
                                response_data.text or response_data.content)}
                    # if response_data.json():
                    #     error_detail = {'error': error_code + " - " + error_message + " - %s"%(response_data.json())}
                    package_id.response_message = error_detail
            except Exception as e:
                package_id.response_message = e
                _logger.info("Exception >>>>> Inside Package: %s" % (e))
        if self.weight_bulk:
            try:
                weight = self.weight_bulk
                body = self.carrier_id and self.carrier_id.generate_label_from_shipstation(self, False, weight)
                # warehouse_location_id = self.sale_id and self.sale_id.shipstation_warehouse_address_id
                # response_data=self.carrier_id and self.carrier_id.api_calling_function("/shipments/createlabel", body, warehouse_location_id)
                response_data = self.carrier_id.api_calling_function("/orders/createlabelfororder", body)
                if response_data.status_code == 200:
                    responses = response_data.json()
                    shipment_id = responses.get('shipmentId')
                    if shipment_id:
                        self.shipstation_shipment_id = shipment_id
                        label_data = responses.get('labelData')
                        tracking_number = responses.get('trackingNumber')
                        shipment_cost += responses.get('shipmentCost')
                        final_tracking_number.append(tracking_number)
                        base_data = binascii.a2b_base64(str(label_data))
                        label_datas.append(base_data)
                        tracking_mesage = (_("Shipstation Tracking Number: </b>%s") % (tracking_number))
                        message_id = self.message_post(
                            body=tracking_mesage)  # attachments=[('%s_Shipstation_Tracking_%s.pdf' % (self.name ,tracking_number), base_data)]
                        input_path.append("%s_%s.pdf" % (file_path, tracking_number))
                        # with open("%s_%s.pdf" % (file_path, tracking_number), "ab") as f:f.write(base64.b64decode(message_id and message_id.attachment_ids[0] and message_id.attachment_ids[0].datas))
                        logmessage = _("<b>Tracking Numbers:</b> %s") % (tracking_number)
                        label_data_pdf = binascii.a2b_base64(str(label_data))
                        self.message_post(body=logmessage, attachments=[("%s.pdf" % (self.id), label_data_pdf)])
                else:
                    error_code = "%s" % (response_data.status_code)
                    _logger.info("Inside Bulk Weight ERROR CODE: %s" % (error_code))
                    error_message = response_data.reason
                    _logger.info("ERROR Reponse Data: %s" % (response_data))
                    error_detail = {'error': error_code + " - " + error_message + " - %s" % (response_data.json())}
                    # if response_data.json():
                    #     error_detail = {'error': error_code + " - " + error_message + " - %s"%(response_data.json())}
                    self.message_post(body=error_detail)

            except Exception as e:
                self.message_post(body=e)
                _logger.info("Exception >>> Inside Bulk Weight: %s" % (e))
        if not final_tracking_number:
            # _logger.info("Not Final Tracking Number: %s" % (response_data))
            raise ValidationError("{}".format(error_detail))
        self.carrier_tracking_ref = ','.join(final_tracking_number)
        self.shipment_cost = shipment_cost

        # for path in input_path:
        #     pdf_merger.append(path)

        file_data_temp = pdf.merge_pdf(label_datas)
        file_data_temp = base64.b64encode(file_data_temp)

        att_id = self.env['ir.attachment'].create(
            {'name': "Wave -%s.pdf" % (file_name or ""), 'type': 'binary', 'datas': file_data_temp or "",
             'mimetype': 'application/pdf', 'res_model': 'stock.picking', 'res_id': self.id, 'res_name': self.name})

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=ir.attachment&field=datas&id=%s&filename=%s.pdf' % (
            att_id.id, self.name.replace('/', '_')),
            'target': 'self'
        }

    def _prepare_picking_for_immediate_transfer(self):
        self.ensure_one()
        # If still in draft => confirm and assign
        if self.state == 'done':
            _logger.info("%s (Backend Process) : Could not process. Picking already in DONE state." % self.name)
            return False
        if self.state == 'draft':
            self.action_confirm()
            if self.state != 'assigned':
                self.action_assign()
                if self.state != 'assigned':
                    _logger.info(
                        "%s (Backend Process) : Could not reserve all requested products. Please use the \'Check Availability\' button to handle the reservation manually." % self.name)
                    return False

        # set product done qty = product uom qty.
        if self.state == 'assigned':
            for move in self.move_ids:
                for move_line in move.move_line_ids:
                    move_line.qty_done = move_line.product_uom_qty
            if self._check_backorder():
                _logger.info(
                    "%s (Backend Process) : Could not transfer because there is a possibility of BackOrder. Please check delivery order." % self.name)
                for move in self.move_ids:
                    for move_line in move.move_line_ids:
                        move_line.product_uom_qty = move_line.qty_done
                        move_line.qty_done = 0
                return False
        else:
            _logger.info(
                "{} (Backend Process) : Could not process the picking because state is not as expected '{}'.".format(
                    self.name, self.state))
            return False
        return True

    def import_delivery_order_using_cron(self):
        shipstation_operation_detail = self.env['shipstation.operation.detail']
        operation_id = shipstation_operation_detail.create({
            'shipstation_operation': 'shipment', 'shipstation_operation_type': 'import',
            'message': 'Shipstation Shipment Importing...',
        })
        pickings = self.search([('state', '=', 'done'),
                                ('is_order_imported_in_shipstation', '=', False),
                                ('shipstation_order_id', '!=', ''),
                                ('picking_type_code', '=', 'outgoing')])
        _logger.info("Total PICKING : {0} >>>>>>>>>>>>>> Pickings : {1}".format(len(pickings), pickings))
        for picking in pickings:
            picking.sudo().import_delivery_order(operation_id)

        operation_id and operation_id.write({'message': 'Shipstation Shipment Import Process Done Successfully.', })
        _logger.info("Shipstation Import delivery order Cron Finished")
        return True

    def import_delivery_order(self, operation_id=False):
        self.ensure_one()
        shipstation_operation_details = self.env['shipstation.operation.details']
        try:
            configuration = self.shipstation_configuration_id
            if not configuration:
                configuration = self.sale_id.shipstation_configuration_id
            if not configuration:
                configuration = self.env['shipstation.odoo.configuration.vts'].search([], limit=1)
            if not configuration:
                shipstation_operation_details.create(
                    {'operation_id': operation_id and operation_id.id,
                     'shipstation_response_message': "Shipstation Configuration Missing",
                     'fault_operaion': True,
                     'shipstation_operation': 'shipment'})
                return
            ref_number = self.shipstation_sale_order_number
            shipstation_sale_order_number = ref_number.replace("#", "%23")
            url = configuration.making_shipstation_url('/shipments?orderNumber=%s' % (shipstation_sale_order_number))
            # api_secret = configuration.api_secret
            # api_key = configuration.api_key
            # data = "%s:%s" % (api_key, api_secret)
            # encode_data = base64.b64encode(data.encode("utf-8"))
            # authrization_data = "Basic %s" % (encode_data.decode("utf-8"))
            # headers = {"Authorization": authrization_data,
            #            "Content-Type": "application/json"}
            try:
                response_data = configuration.api_calling_function(url)
            except Exception as e:
                shipstation_operation_details.create(
                    {'operation_id': operation_id and operation_id.id,
                     'shipstation_response_message': "Shipstation Import Order Issue %s, %s" % (self.name, e),
                     'fault_operaion': True,
                     'shipstation_operation': 'shipment'})
                return

            if response_data.status_code == 200:
                responses = response_data.json()
                shipments = responses.get('shipments')
                if not shipments:
                    shipstation_operation_details.create(
                        {'operation_id': operation_id and operation_id.id,
                         'shipstation_response_message': "%s Data is not availabel. %s" % (self.name, responses),
                         'fault_operaion': True,
                         'shipstation_operation': 'shipment'})
                    return
                if isinstance(shipments, dict):
                    shipments = [shipments]
                shipment_tracking_number = shipstation_batch_numbers = shipstation_carrier_codes = \
                    shipstation_unit_of_measures = shipment_ids = service_code = []
                total_shipping_cost = total_shipstation_weight = 0.0
                # customField_deatils = ""
                for shipment in shipments:
                    _logger.info(">>>>>>>> ORDER SHIPMENT : {}".format(shipment))
                    if shipment.get('voided') != True:
                        _logger.info("Insided not voided")
                        tracking_number = shipment.get('trackingNumber')
                        shipping_cost = shipment.get('shipmentCost')
                        service = shipment.get('serviceCode')
                        shipment_id = shipment.get('shipmentId')
                        shipstation_weight = shipment.get('weight').get('value')
                        shipstation_unit_of_measure = shipment.get('weight').get('units')
                        shipstation_carrier_code = shipment.get('carrierCode')
                        shipstation_batch_number = shipment.get('batchNumber')
                        service_code.append("%s-%s" % (service, tracking_number))
                        shipment_ids.append("%s" % shipment_id)
                        total_shipping_cost += float(shipping_cost)
                        total_shipstation_weight += float(shipstation_weight)
                        shipment_tracking_number.append(tracking_number)
                        shipstation_batch_numbers.append(shipstation_batch_number)
                        shipstation_carrier_codes.append(shipstation_carrier_code)
                        shipstation_unit_of_measures.append(shipstation_unit_of_measure)

                self.carrier_tracking_ref = ','.join(shipment_tracking_number)
                self.shipstation_service_code = ','.join(service_code)
                self.carrier_price = total_shipping_cost
                self.is_order_imported_in_shipstation = True
                self.shipstation_shipment_id = ','.join(shipment_ids)
                self.shipstation_weight = total_shipstation_weight
                self.shipstation_unit_of_measure = ','.join(shipstation_unit_of_measures)
                self.shipstation_carrier_code = ','.join(shipstation_carrier_codes)
                # self.shipstation_batch_number = ','.join(shipstation_batch_numbers)
                # self.order_custom_data = customField_deatils

                shipstation_operation_details.sudo().create(
                    {'operation_id': operation_id and operation_id.id,
                     'shipstation_request_message': "URL : %s" % (url),
                     'shipstation_response_message': "%s Delivery Order Information Imported Successfully, Order ID : %s, Tracking Number : %s, Shipping Cost : %s " % (
                         self.name, self.shipstation_order_id, ','.join(shipment_tracking_number), total_shipping_cost),
                     'fault_operaion': False,
                     'shipstation_operation': 'shipment'})
                # self.action_done()
                self._cr.commit()
                _logger.info("Shipment Data Imported For This Picking : %s." % (self.name))
            else:
                error_code = "%s" % (response_data.status_code)
                error_message = response_data.reason
                error_detail = {'error': error_code + " - " + error_message + " - "}
                if response_data.json():
                    error_detail = {'error': error_code + " - " + error_message + " - %s" % (response_data.json())}
                shipstation_operation_details.sudo().create(
                    {'operation_id': operation_id and operation_id.id,
                     'shipstation_response_message': "%s Delivery order Not Imported %s" % (self.name, error_detail),
                     'fault_operaion': True,
                     'shipstation_operation': 'shipment'})
        except Exception as e:
            shipstation_operation_details.sudo().create(
                {'operation_id': operation_id and operation_id.id,
                 'shipstation_response_message': "%s Delivery order Not Imported %s" % (self.name, e),
                 'fault_operaion': True,
                 'shipstation_operation': 'shipment'})
