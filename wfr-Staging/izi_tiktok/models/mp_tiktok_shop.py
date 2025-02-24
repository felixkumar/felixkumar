from odoo import api, fields, models


class MPTiktokShop(models.Model):
    _name = 'mp.tiktok.shop'
    _inherit = 'mp.base'
    _description = 'Marketplace Tiktok Shop'
    _rec_name = 'shop_name'

    SHOP_TYPE = [
        ('1', 'CROSS BORDER'),
        ('2', 'LOCAL TO LOCAL'),
    ]

    shop_id = fields.Char(string="Shop ID", readonly=True)
    shop_name = fields.Char(string="Shop Name", readonly=True)
    region = fields.Char(string="Region", readonly=True)
    type = fields.Selection(string="Type", selection=SHOP_TYPE, readonly=True)
    shop_logistic_ids = fields.One2many(comodel_name="mp.tiktok.logistic", inverse_name="shop_id",
                                        string="Active Logistics", required=False)


# class MPTiktokShopLogistic(models.Model):
#     _name = 'mp.tiktok.shop.logistic'
#     _inherit = 'mp.base'
#     _description = 'Marketplace Tiktok Shop Logistic'
#     _sql_constraints = [
#         ('unique_shop_logistic', 'UNIQUE(shop_id,logistic_id)', 'Please select one logistic per shop!')
#     ]

#     shop_id = fields.Many2one(comodel_name="mp.tiktok.shop", string="Shop", required=True, ondelete="restrict")
#     logistic_id = fields.Many2one(comodel_name="mp.tiktok.shop", string="Logistic", required=True,
#                                   ondelete="restrict")
#     service_ids = fields.Many2many(comodel_name="mp.tokopedia.logistic.service",
#                                    relation="rel_tp_shop_logistic_service", column1="shop_logistic_id",
#                                    column2="service_id", string="Active Service(s)")
#     name = fields.Char(related="logistic_id.shipping_provider_name")
