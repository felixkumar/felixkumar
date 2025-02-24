from odoo import fields, models, api


class FreightFreightInherit(models.Model):
    _inherit = 'freight.freight'

    def create_vas_cost_lines(self):
        self.vas_cost_ids = False
        pallet_config_obl = self.env['pallet.config.obl']
        pallet_vas_cost = self.env['pallet.vas.cost']
        for rec in self:
            carton_data = {}
            volume_data = {}
            weight_data = {}
            pallet_data = {}
            load_data = {}

            fulfill_method = rec.fulfillment_method

            domain = [('warehouse_id', '=', rec.warehouse_id.id), ('partner_id', '=', rec.partner_id.id),
                      ('fulfillment_method', '=', fulfill_method)]

            if fulfill_method == 'e-commerce':
                for line in rec.freight_order_line_ids.filtered(lambda f: f.goods.detailed_type != 'service'):
                    product_id = line.goods
                    if product_id:
                        is_carton = pallet_config_obl.search(domain + [('is_carton', '=', True)])
                        if is_carton:
                            carton_dict = self.bill_by_service_fee(is_carton) or {}

                            for service in carton_dict:
                                carton_bill = carton_dict[service]
                                has_product = [x for x in carton_bill if x.product_ids and product_id in x.product_ids]
                                no_product = [x for x in carton_bill if not x.product_ids]
                                if has_product:
                                    bill = has_product[0]
                                elif no_product:
                                    bill = no_product[0]
                                else:
                                    if not carton_bill[0].service_fee.name in [bill.product_id.name for bill in
                                                                               self.vas_cost_ids]:
                                        bill = carton_bill[0]
                                    else:
                                        bill = False
                                if bill and line.qty_carton > 0:
                                    carton_data = {
                                        'product_id': bill.service_fee.id,
                                        'total_unit': line.qty_carton,
                                        'product_uom': bill.service_uom.id,
                                        'unit_price': bill.cost,
                                        'transit_app_id': rec.id,
                                    }
                                    pallet_vas_cost.create(carton_data)

                        is_volume = pallet_config_obl.search(domain + [('is_volume', '=', True)])
                        if is_volume:
                            volume_dict = self.bill_by_service_fee(is_volume) or {}

                            for service in volume_dict:
                                volume_bill = volume_dict[service]
                                has_product = [x for x in volume_bill if x.product_ids and product_id in x.product_ids]
                                no_product = [x for x in volume_bill if not x.product_ids]
                                if has_product:
                                    bill = has_product[0]
                                elif no_product:
                                    bill = no_product[0]
                                else:
                                    if not volume_bill[0].service_fee.name in [bill.product_id.name for bill in
                                                                               self.vas_cost_ids]:
                                        bill = volume_bill[0]
                                    else:
                                        bill = False
                                if bill and line.product_volume:
                                    volume_data = {
                                        'product_id': bill.service_fee.id,
                                        'total_unit': line.product_volume,
                                        'product_uom': bill.service_uom.id,
                                        'unit_price': bill.cost,
                                        'transit_app_id': rec.id,
                                    }
                                    pallet_vas_cost.create(volume_data)

                        is_weight = pallet_config_obl.search(domain + [('is_weight', '=', True)])
                        if is_weight:
                            weight_dict = self.bill_by_service_fee(is_weight) or {}

                            for service in weight_dict:
                                weight_bill = weight_dict[service]
                                has_product = [x for x in weight_bill if x.product_ids and product_id in x.product_ids]
                                no_product = [x for x in weight_bill if not x.product_ids]
                                if has_product:
                                    bill = has_product[0]
                                elif no_product:
                                    bill = no_product[0]
                                else:
                                    if not weight_bill[0].service_fee.name in [bill.product_id.name for bill in
                                                                               self.vas_cost_ids]:
                                        bill = weight_bill[0]
                                    else:
                                        bill = False
                                if bill and line.net_weight > 0:
                                    weight_data = {
                                        'product_id': bill.service_fee.id,
                                        'total_unit': line.net_weight,
                                        'product_uom': bill.service_uom.id,
                                        'unit_price': bill.cost,
                                        'transit_app_id': rec.id,
                                    }
                                    pallet_vas_cost.create(weight_data)

                        is_pallet = pallet_config_obl.search(domain + [('is_pallet', '=', True)])
                        if is_pallet:
                            pallet_dict = self.bill_by_service_fee(is_pallet) or {}

                            for service in pallet_dict:
                                pallet_bill = pallet_dict[service]
                                has_product = [x for x in pallet_bill if x.product_ids and product_id in x.product_ids]
                                no_product = [x for x in pallet_bill if not x.product_ids]
                                if has_product:
                                    bill = has_product[0]
                                elif no_product:
                                    bill = no_product[0]
                                else:
                                    if not pallet_bill[0].service_fee.name in [bill.product_id.name for bill in
                                                                               self.vas_cost_ids]:
                                        bill = pallet_bill[0]
                                    else:
                                        bill = False
                                if bill and line.required_pallet > 0:
                                    pallet_data = {
                                        'product_id': bill.service_fee.id,
                                        'total_unit': line.required_pallet,
                                        'product_uom': bill.service_uom.id,
                                        'unit_price': bill.cost,
                                        'transit_app_id': rec.id,
                                    }
                                    pallet_vas_cost.create(pallet_data)

                        is_load = pallet_config_obl.search(domain + [('is_load', '=', True)])
                        if is_load:
                            load_dict = self.bill_by_service_fee(is_load) or {}

                            for service in load_dict:
                                load_bill = load_dict[service]
                                has_product = [x for x in load_bill if x.product_ids and product_id in x.product_ids]
                                no_product = [x for x in load_bill if not x.product_ids]
                                if has_product:
                                    bill = has_product[0]
                                elif no_product:
                                    bill = no_product[0]
                                else:
                                    if not load_bill[0].service_fee.name in [bill.product_id.name for bill in
                                                                             self.vas_cost_ids]:
                                        bill = load_bill[0]
                                    else:
                                        bill = False
                                if bill:
                                    load_data = {
                                        'product_id': bill.service_fee.id,
                                        'total_unit': 1,
                                        'product_uom': bill.service_uom.id,
                                        'unit_price': bill.cost,
                                        'transit_app_id': rec.id,
                                    }
                                    pallet_vas_cost.create(load_data)
            else:
                for line in rec.freight_order_line_ids.filtered(lambda f: f.goods.detailed_type != 'service'):
                    product_id = line.goods
                    if product_id:
                        is_carton = pallet_config_obl.search(domain + [('is_carton', '=', True)])
                        if is_carton:
                            has_product = [x for x in is_carton if x.product_ids and product_id in x.product_ids]
                            no_product = [x for x in is_carton if not x.product_ids]
                            if has_product:
                                bill = has_product[0]
                            elif no_product:
                                bill = no_product[0]
                            else:
                                bill = False
                            if bill and line.qty_carton > 0:
                                carton_data = {
                                    'product_id': bill.service_fee.id,
                                    'total_unit': line.qty_carton,
                                    'product_uom': bill.service_uom.id,
                                    'unit_price': bill.cost,
                                    'transit_app_id': rec.id,
                                }
                                prod_exist = rec.vas_cost_ids.filtered(lambda x: x.product_id.id == bill.service_fee.id)
                                if prod_exist:
                                    prod_exist.total_unit += line.qty_carton
                                else:
                                    pallet_vas_cost.create(carton_data)

                        is_volume = pallet_config_obl.search(domain + [('is_volume', '=', True)])
                        if is_volume:
                            has_product = [x for x in is_volume if x.product_ids and product_id in x.product_ids]
                            no_product = [x for x in is_volume if not x.product_ids]
                            if has_product:
                                bill = has_product[0]
                            elif no_product:
                                bill = no_product[0]
                            else:
                                bill = False
                            if bill and line.product_volume:
                                volume_data = {
                                    'product_id': bill.service_fee.id,
                                    'total_unit': line.product_volume,
                                    'product_uom': bill.service_uom.id,
                                    'unit_price': bill.cost,
                                    'transit_app_id': rec.id,
                                }
                                prod_exist = rec.vas_cost_ids.filtered(lambda x: x.product_id.id == bill.service_fee.id)
                                if prod_exist:
                                    prod_exist.total_unit += line.product_volume
                                else:
                                    pallet_vas_cost.create(volume_data)

                        is_weight = pallet_config_obl.search(domain + [('is_weight', '=', True)])
                        if is_weight:
                            has_product = [x for x in is_weight if x.product_ids and product_id in x.product_ids]
                            no_product = [x for x in is_weight if not x.product_ids]
                            if has_product:
                                bill = has_product[0]
                            elif no_product:
                                bill = no_product[0]
                            else:
                                bill = False
                            if bill and line.net_weight > 0:
                                weight_data = {
                                    'product_id': bill.service_fee.id,
                                    'total_unit': line.net_weight,
                                    'product_uom': bill.service_uom.id,
                                    'unit_price': bill.cost,
                                    'transit_app_id': rec.id,
                                }
                                prod_exist = rec.vas_cost_ids.filtered(lambda x: x.product_id.id == bill.service_fee.id)
                                if prod_exist:
                                    prod_exist.total_unit += line.net_weight
                                else:
                                    pallet_vas_cost.create(weight_data)

                        is_pallet = pallet_config_obl.search(domain + [('is_pallet', '=', True)])
                        if is_pallet:
                            has_product = [x for x in is_pallet if x.product_ids and product_id in x.product_ids]
                            no_product = [x for x in is_pallet if not x.product_ids]
                            if has_product:
                                bill = has_product[0]
                            elif no_product:
                                bill = no_product[0]
                            else:
                                bill = False
                            if bill and line.required_pallet > 0:
                                pallet_data = {
                                    'product_id': bill.service_fee.id,
                                    'total_unit': line.required_pallet,
                                    'product_uom': bill.service_uom.id,
                                    'unit_price': bill.cost,
                                    'transit_app_id': rec.id,
                                }
                                prod_exist = rec.vas_cost_ids.filtered(lambda x: x.product_id.id == bill.service_fee.id)
                                if prod_exist:
                                    prod_exist.total_unit += line.required_pallet
                                else:
                                    pallet_vas_cost.create(pallet_data)

                        is_load = pallet_config_obl.search(domain + [('is_load', '=', True)])
                        if is_load:
                            has_product = [x for x in is_load if x.product_ids and product_id in x.product_ids]
                            no_product = [x for x in is_load if not x.product_ids]
                            if has_product:
                                bill = has_product[0]
                            elif no_product:
                                bill = no_product[0]
                            else:
                                bill = False
                            if bill:
                                load_data = {
                                    'product_id': bill.service_fee.id,
                                    'total_unit': 1,
                                    'product_uom': bill.service_uom.id,
                                    'unit_price': bill.cost,
                                    'transit_app_id': rec.id,
                                }
                                prod_exist = rec.vas_cost_ids.filtered(lambda x: x.product_id.id == bill.service_fee.id)
                                if prod_exist:
                                    prod_exist.total_unit += 1
                                else:
                                    pallet_vas_cost.create(load_data)

    def bill_by_service_fee(self, billing_rules):
        rules_dict = {}
        service_fee = []
        billing_rules = billing_rules.sorted(key=lambda x: x.product_ids, reverse=True)
        for bill in billing_rules:
            if bill.service_fee.id not in service_fee:
                service_fee.append(bill.service_fee.id)
                rules_dict[bill.service_fee.id] = [bill]
            else:
                rules_dict[bill.service_fee.id].append(bill)

        return rules_dict
