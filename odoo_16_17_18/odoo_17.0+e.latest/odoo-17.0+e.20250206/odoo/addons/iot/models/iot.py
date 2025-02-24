# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import secrets

from odoo import api, fields, models


# ----------------------------------------------------------
# Models for client
# ----------------------------------------------------------
class IotBox(models.Model):
    _name = 'iot.box'
    _description = 'IoT Box'

    name = fields.Char('Name', readonly=True)
    identifier = fields.Char(string='Identifier (Mac Address)', readonly=True)
    device_ids = fields.One2many('iot.device', 'iot_id', string="Devices")
    device_count = fields.Integer(compute='_compute_device_count')
    ip = fields.Char('Domain Address', readonly=True)
    ip_url = fields.Char('IoT Box Home Page', readonly=True, compute='_compute_ip_url')
    drivers_auto_update = fields.Boolean('Automatic drivers update', help='Automatically update drivers when the IoT Box boots', default=True)
    version = fields.Char('Image Version', readonly=True)
    company_id = fields.Many2one('res.company', 'Company')

    def _compute_ip_url(self):
        for box in self:
            if not box.ip:
                box.ip_url = False
            else:
                url = 'https://%s' if box.get_base_url()[:5] == 'https' else 'http://%s:8069'
                box.ip_url = url % box.ip

    def _compute_device_count(self):
        for box in self:
            box.device_count = len(box.device_ids)


class IotDevice(models.Model):
    _name = 'iot.device'
    _description = 'IOT Device'

    iot_id = fields.Many2one('iot.box', string='IoT Box', required=True, ondelete='cascade')
    name = fields.Char('Name')
    identifier = fields.Char(string='Identifier', readonly=True)
    type = fields.Selection([
        ('printer', 'Printer'),
        ('camera', 'Camera'),
        ('keyboard', 'Keyboard'),
        ('scanner', 'Barcode Scanner'),
        ('device', 'Device'),
        ('payment', 'Payment Terminal'),
        ('scale', 'Scale'),
        ('display', 'Display'),
        ('fiscal_data_module', 'Fiscal Data Module'),
        ], readonly=True, default='device', string='Type',
        help="Type of device.")
    manufacturer = fields.Char(string='Manufacturer', readonly=True)
    connection = fields.Selection([
        ('network', 'Network'),
        ('direct', 'USB'),
        ('bluetooth', 'Bluetooth'),
        ('serial', 'Serial'),
        ('hdmi', 'Hdmi'),
        ], readonly=True, string="Connection",
        help="Type of connection.")
    report_ids = fields.Many2many('ir.actions.report', string='Reports')
    iot_ip = fields.Char(related="iot_id.ip")
    company_id = fields.Many2one('res.company', 'Company', related="iot_id.company_id")
    connected = fields.Boolean(string='Status', help='If device is connected to the IoT Box', readonly=True)
    keyboard_layout = fields.Many2one('iot.keyboard.layout', string='Keyboard Layout')
    display_url = fields.Char('Display URL', help="URL of the page that will be displayed by the device, leave empty to use the customer facing display of the POS.")
    manual_measurement = fields.Boolean('Manual Measurement', compute="_compute_manual_measurement", help="Manually read the measurement from the device")
    is_scanner = fields.Boolean(string='Is Scanner', compute="_compute_is_scanner", inverse="_set_scanner",
        help="Manually switch the device type between keyboard and scanner")

    @api.depends('iot_id')
    def _compute_display_name(self):
        for i in self:
            i.display_name = f"[{i.iot_id.name}] {i.name}"

    @api.depends('type')
    def _compute_is_scanner(self):
        for device in self:
            device.is_scanner = True if device.type == 'scanner' else False

    def _set_scanner(self):
        for device in self:
            device.type = 'scanner' if device.is_scanner else 'keyboard'

    @api.depends('manufacturer')
    def _compute_manual_measurement(self):
        for device in self:
            device.manual_measurement = device.manufacturer == 'Adam'

class KeyboardLayout(models.Model):
    _name = 'iot.keyboard.layout'
    _description = 'Keyboard Layout'

    name = fields.Char('Name')
    layout = fields.Char('Layout')
    variant = fields.Char('Variant')

class IotChannel(models.Model):
    _name = "iot.channel"
    _description = "The Websocket Iot Channel"

    SYSTEM_PARAMETER_KEY = 'iot.ws_channel'

    # TODO: remove in master, too complicate and scenario to handle multi-company with the IoT
    name = fields.Char('Name', default=lambda self: f'iot_channel-{secrets.token_hex(16)}')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company) #One2one

    def _get_iot_no_company_set_ws_company_id(self):
        """Get the company ID of the default company when no company is set on the IoT device"""
        # When the IoT reaches the server to get the WS channel,
        # it does a public request thus the environment is set on the "public user"
        # In this case, if no ID is set on the IoT, it will default to the current environment company.
        # It's computation can be simplified to the following lines

        # simplification of Environment.company computation
        public_user_companies = self.env.ref('base.public_user')._get_company_ids()
        return public_user_companies[0] if public_user_companies else False

    def _create_channel_if_not_exist(self):
        # Temporary workaround to adapt the previous model to the new one
        # If a WS already exist, we keep its value, otherwise, we generate it randomly
        icp = self.env['ir.config_parameter'].sudo()
        existing_channel = self.with_company(
            self._get_iot_no_company_set_ws_company_id()).env['iot.channel'].search(
                [('company_id', "=", self.env.company.id)], limit=1)
        iot_channel = existing_channel.name or f'iot_channel-{secrets.token_hex(16)}'
        icp.set_param(self.SYSTEM_PARAMETER_KEY, iot_channel)
        return iot_channel

    def get_iot_channel(self):
        if self.env.is_system() or self.env.user.has_group('base.group_user'):
            icp = self.env['ir.config_parameter'].sudo()
            iot_channel = icp.get_param(self.SYSTEM_PARAMETER_KEY)
            return iot_channel or self._create_channel_if_not_exist()
        return False

    _sql_constraints = [
        ('unique_name', 'unique(name)', 'The channel name must be unique'),
    ]
