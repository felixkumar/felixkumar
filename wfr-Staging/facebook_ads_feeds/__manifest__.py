# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "Facebook Catalog Integration",
  "summary"              :  "Facebook Catalog Integration allows you to send the products of odoo as feeds into facebook Market.",
  "category"             :  "eCommerce",
  "version"              :  "1.1.2",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "maintainer"           :  "Mandeep Duggal",
  "website"              :  "https://store.webkul.com/odoo-facebook-catalog-integration-2155.html",
  "description"          :  """Facebook Catalog Integration
Odoo Facebook Catalog Integration
Integrate Facebook Catalog with Odoo 
Facebook
Facebook Integration
Add Catalogs from Odoo to Facebook
Facebook Adds 
Facebook Feeds
Catalog in Facebook""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=facebook_ads_feeds&lifetime=120&lout=1&custom_url=/",
  "depends"              :  [
                             'base',
                             'website_sale',
                             'wk_wizard_messages',
                             'stock'
                            ],
  "data"                 :  [
                             'security/ir.model.access.csv',
                             'views/menuitem_view.xml',
                             'views/facebook_fields_view.xml',
                             'views/facebook_shop_view.xml',
                             'views/field_mapping_view.xml',
                             'views/google_categ_view.xml',
                             'views/product_inherit_view.xml',
                             'views/fb_attachment_mapping.xml',
							               'demo/demo_facebook_fields.xml',
                             'demo/demo_field_mapping.xml',
                            ],
  "css"                  :  [],
  "js"                   :  [],
  "images"               :  ['static/description/Banner.gif'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  99,
  "currency"             :  "USD",
}
