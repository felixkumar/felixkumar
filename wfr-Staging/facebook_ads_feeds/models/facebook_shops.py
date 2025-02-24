# -*- coding: utf-8 -*-
################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
################################################################################
from odoo import models,fields,api
import json
import logging
from odoo.http import request
_logger = logging.getLogger(__name__)
from odoo.tools.safe_eval import safe_eval
import xml.etree.ElementTree as ET
import base64
from time import time 
from odoo.fields import Datetime
from odoo.exceptions import UserError
from odoo.addons.http_routing.models.ir_http import slug

fixed_fields_layout = ['price','link','image_link','sale_price','inventory','status']
to_remove_keys = ['CURRENCY','BASE_URL','ID','SLUG']
many2one_fields = ['google_product_category']


class xml(object):

    @staticmethod
    def _encode_content(data):
        return data.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"', '&quot;')

    @classmethod
    def dumps(cls,key,obj):
        # if isinstance(obj, dict) and key in obj.keys() and isinstance(obj[key], list):
        #     return "".join("%s" % (cls.dumps(key, obj[key])))
        if isinstance(obj, dict):

            # return cls.dumps(key, obj[key])
            return "".join(("<%s>%s</%s>" % (key, cls.dumps(key, obj[key]), key),cls.dumps(key, obj[key]))[isinstance(obj[key], list)] for key in obj)
        elif isinstance(obj, list):

            return "".join("<%s>%s</%s>" % (key, cls.dumps(key,element), key) for index,element in enumerate(obj))
        else:
            return "%s" % (xml._encode_content(obj.__str__()))

    @staticmethod
    def loads(string):
        def _node_to_dict(node):
            if node.text:
                return node.text
            else:
                return {child.tag: _node_to_dict(child) for child in node}
        root = ET.fromstring(string)
        return {root.tag: _node_to_dict(root)}




class FacebookMerchantShop(models.Model):
    _name = 'fb.facebook.shop'
    _description = "Facebook Shops"

    def _get_default_domain(self):
        domain = [("sale_ok", "=", True),("website_published","=",True)]
        return domain

    @api.onchange('id', 'shop_url', 'enable_token', 'feed_token')
    def _get_feed_url(self):
        if self.shop_url and self.id:
            url = str(self.shop_url)+"/shop/"+str(self.id)+"/content"
            if self.feeds_security == "automatic" and  self.enable_token and self.feed_token:
                url = url + "?token=%s"%(self.feed_token)
            self.feed_url =  url
        else:
            self.feed_url = False
            
    @api.onchange('website_id')
    def onchange_website(self):
        if self.website_id:
            self.shop_url = self.website_id.get_base_url()

    name = fields.Char(string="Shop Name", required=True, translate=True)
    id=fields.Integer(string="Sequence No")
    currency_id = fields.Many2one(string="Currency", store=True)
    website_id = fields.Many2one('website', string="Website")
    currency_id = fields.Many2one(string="Currency", related="pricelist_id.currency_id", readonly=True)
    content_language_id = fields.Many2one(string="Content Language", comodel_name="res.lang", required=True, help="Language in which your products will get sync on Facebook Shop")
    shop_url=fields.Char(name="Shop URL", help="Write your domain name of your website")
    feed_url=fields.Char(string="Feed URL", readonly=True, compute="_get_feed_url")
    pricelist_id = fields.Many2one(comodel_name="product.pricelist", string="Product Pricelist", required=True, help="select the pricelist according to which your product price will get selected")
    field_mapping_id = fields.Many2one(comodel_name="fb.field.mappning", string="Field Mapping", domain=[('active','=',True)], required=True)
    product_selection_type = fields.Selection([('domain','Domain'),('manual','Manual'),('category','Category')], default = "domain", string="Product Select Way", help="Select wether you want to select the product manually or with the help of domain")
    domain_input = fields.Char(string="Domain", default="[]", help="Domain Filter:- Using this only filtered products will generate inside feed xml.")
    limit = fields.Integer(string="Limit", default=10, help="Product Limit:- Selected limit product will generate inside feed xml.")
    product_ids_rel = fields.Many2many(comodel_name='product.template', relation='fb_shop_product_rel', column1='facebook_id', column2='product_id', domain=_get_default_domain, string="Products")
    public_categ_ids = fields.Many2many(comodel_name='product.public.category', relation='fb_shop_public_category_rel', column1='facebook_id', column2='prod_cat_id', string="Category")
    mapping_count=fields.Integer(string="Total Mappings", compute="_mapping_count")
    crone_id=fields.Many2one(comodel_name='ir.cron', string="Cron Detail", readonly=True)
    multi_images = fields.Boolean(string="Want to sync Multi Images at facebook catalog")
    sync_product_variant = fields.Boolean(string="Want to sync product variants at facebook catalog")
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", help="If it's set then selected warehouse quantity will get fetched else all quantity will fetch.")
    feeds_security = fields.Selection([('automatic','Automatic'),('manual','Manual')], string="Feed Security", default="automatic")
    enable_token = fields.Boolean(string="Token Enabled", help="Enbale if you want to secure publicly access Feed URL")
    feed_token = fields.Char(string="Token")

    @api.onchange('enable_token')
    def onchange_enable_token(self):
        if self.enable_token:
            if not self.feed_token:
                self.feed_token = request.csrf_token()
        else:
            self.feed_token = False
        
    def regenerate_token(self):
        for obj in self:
            obj.feed_token = request.csrf_token()
            obj._get_feed_url()

    def _mapping_count(self):
        for rec in self:
            rec.mapping_count=self.env['fb.attachment.mapping'].search_count([('fb_shop','=',self.id)])

    def test_function(self):

        mappings = self.env['fb.attachment.mapping'].search([('fb_shop','=',self.id)]).ids
        action = self.env.ref('facebook_ads_feeds.fb_attachment_mapping_action').read()[0]
        action['domain'] = [('id', 'in', mappings)]
        return action

    def _get_product_fields(self,field_mapping_lines_ids):
        field_mapping_model=self.env['fb.field.mappning.line'].search_read([('id','in',field_mapping_lines_ids),('fixed','=',False)],['model_field_id'])
        field_mapping_model_ids=[x.get('model_field_id')[0] for x in field_mapping_model]
        field_mapping_model_name_ids=self.env['ir.model.fields'].sudo().search_read([('id','in',field_mapping_model_ids)],['name'])
        field_mapping_model_name=[x.get('name') for x in field_mapping_model_name_ids]
        return field_mapping_model_name

    def _get_final_domain(self,domain=[]):
        design_domain=self._get_default_domain()
        design_domain += domain
        return design_domain


    def _wrap2xml(self, data):
        resp_xml = "<?xml version='1.0' encoding='UTF-8'?>"
        resp_xml +="<feed xmlns='http://www.w3.org/2005/Atom' xmlns:g='http://base.google.com/ns/1.0'>"
        resp_xml += xml.dumps("",data)
        resp_xml +="</feed>"
        return resp_xml

    def _get_product_detail(self, field_mapping_lines_ids):

        sel_type=self.product_selection_type

        context = self._context.copy()
        context.update({'pricelist': self.pricelist_id.id,'website_id':self.website_id.id,'lang': self.content_language_id.code,'warehouse':self.warehouse_id.id if self. warehouse_id else False,'active_test':False})
        limit = 0
        if(sel_type == 'domain'):
            domain = safe_eval(self.domain_input)
            final_domain=self._get_final_domain(domain=domain)
            limit = self.limit
        elif(sel_type == 'manual'):
            return self.product_ids_rel.with_context(context)
        elif(sel_type == 'category'):
            categ_ids=self.public_categ_ids.ids
            categ_domain=[('public_categ_ids','child_of',categ_ids)]
            final_domain=self._get_final_domain(domain=categ_domain)
        else:
            return False
        if limit > 0:
            return self.env['product.template'].with_context(context).search(final_domain, limit=limit)
        return self.env['product.template'].with_context(context).search(final_domain)

    def _get_one_product_mapping(self,product,field_mapping_lines):
        d={}
        field_mapping_model_name = self._get_product_fields(field_mapping_lines.ids)
        context = self._context.copy()
        context.update({'pricelist': self.pricelist_id.id,'quantity':1,'website_id':self.website_id.id,'lang': self.content_language_id.code,'warehouse':self.warehouse_id.id if self. warehouse_id else False,'uom':product.uom_id})
        pricelist_item_id = self.pricelist_id._get_product_rule(
                    product,
                    quantity=1.0,
                    uom=product.uom_id,)
        price = 0.0
        if pricelist_item_id:
            price = self.env['product.pricelist.item'].browse(pricelist_item_id)._compute_price(
                product=product.with_context(context),
                quantity= 1.0,
                uom=product.uom_id,
                date=fields.Date.today(),
                currency=self.currency_id,
            )
        product_detail = product.with_context(context).read(field_mapping_model_name)[0]
        if price > 0.0:
            product_detail['list_price'] = price
        d['SLUG'] = slug(product.product_tmpl_id)
        d['ID'] = str(product.id)
        d['BASE_URL'] = self.shop_url
        d['CURRENCY'] = self.currency_id.name
        if self.multi_images:
            additiona_images = []
            for image in product.product_template_image_ids:
                additiona_images.append(d.get('BASE_URL')+"/web/image/product.image/"+str(image.id)+"/image_1024/600x600"+"?mlsec=%s"%(int(time() * 1000)))
            d['additional_image_link'] = ','.join(additiona_images)
        values = []
        for attribute in product.product_template_attribute_value_ids:
            if attribute.attribute_id.name.lower() == 'color':
                d['color'] = attribute.name
            else:
                attr = {'label': attribute.attribute_id.name, 'value' : attribute.name}
                values.append(attr)
        if values:
            d['additional_variant_attribute'] = values
        for i in field_mapping_lines:
            key=i.facebook_field_id.name
            if i.fixed:
                value=i.fixed_text
            else:
                if i.model_field_id.ttype == 'many2one':
                    v_name=product_detail.get(i.model_field_id.name)
                    if v_name:
                        value=v_name[1]
                    else:
                        value = False or i.default
                elif (key in fixed_fields_layout): #  ---------------make value accorrding to fixed layout
                    v_name=product_detail.get(i.model_field_id.name) or i.default
                    value = self._default_designed_function(key,v_name,d)
                else:
                    # v_name=i.model_field_id.name
                    value=product_detail.get(i.model_field_id.name) or i.default
            if i.facebook_field_id.g_beg:
                key="g:"+str(key)
            d[key] = value

        for i in to_remove_keys:
            if(i in d.keys()):
                d.pop(i)

        return d

    def _get_product_mapping(self,products,field_mapping_lines):
        final_list_of_dict=[]
        for product in products:
            if self.sync_product_variant and product.product_variant_count > 1:
                for variant in product.product_variant_ids:
                    data = self._get_one_product_mapping(variant,field_mapping_lines)
                    data['g:title'] = variant.product_tmpl_id.name
                    data['item_group_id'] = str(variant.product_tmpl_id.id)
                    final_list_of_dict+=[data]
            elif product and product.product_variant_id:
                data = self._get_one_product_mapping(product.product_variant_id,field_mapping_lines)
                final_list_of_dict+=[data]
        return final_list_of_dict

    def _default_designed_function(self,key,value,d):
        if(key == 'price'):
            # value=self.website_id.company_id.currency_id.compute(value,self.pricelist_id.currency_id)
            return str(value)+" "+d.get('CURRENCY')
        elif (key == 'sale_price'):
            if not value:
                value = 0.0
            return str(value)+" "+d.get('CURRENCY')
        elif (key == 'link'):
            product_url=d.get('BASE_URL') + value
            return product_url
        elif (key == 'image_link'):
            image_url = d.get('BASE_URL')+"/web/image/product.product/"+d.get('ID')+"/image_1024/600x600" +"?mlsec=%s"%(int(time() * 1000))
            return image_url
        elif (key == 'inventory'):
            return value if value else 0
        elif (key == 'status'):
            if value:
                return "active"
            else:
                return "archived"
        else:
            pass

    def _get_dict(self):
        field_mapping_lines_ids=self.field_mapping_id.field_mapping_line_ids
        final_dict={}
        final_dict['title'] = self.with_context(lang = self.content_language_id.code).name
        final_dict['link'] = self.shop_url
        products = self._get_product_detail(field_mapping_lines_ids)
        final_dict['entry'] = self._get_product_mapping(products,field_mapping_lines_ids)

        return self._wrap2xml(final_dict)

    def _store_data(self,final_xml):

        name=str(self.name)+"/"+str(Datetime.now())
        _attach_1 = self.env['ir.attachment'].create({
        'name':name + '.xml',
        'type':'binary',
        'datas': base64.b64encode(final_xml.encode("utf8")),
        'public':True,
        'mimetype':'application/xml;charset=utf-8',
        # 'datas_fname':name+".xml"
        })
        self.env['fb.attachment.mapping'].search([('fb_shop','=',self.id),('latest','=',True)]).write({'latest':False})


        self.env['fb.attachment.mapping'].create({
        'fb_shop':self.id,
        'attachment_id':_attach_1.id,
        'latest':True,
        'updated':False
        })

    def create_xml(self, **kw):
        final_xml=self._get_dict()
        self._store_data(final_xml)
        message="Attachment is Created Please enter the following URL to the Facebook Catalog :-"+self.feed_url
        if not kw.get('cron'):
            _logger.info("Hey Attachment is Created Manually")
            return self.env['wk.wizard.message'].genrated_message(message=message,name='Message')
        else:
            _logger.info("Hey!!! Cron of FB Shop Executed and the Attachment is created")

    def create_cron(self):
        if(not self.crone_id):
            model_id=self.env['ir.model'].search([('model','=','fb.facebook.shop')],limit=1).id
            name=str(self.id)+":"+self.name
            code="env['fb.facebook.shop'].browse("+str(self.id)+").create_xml(cron=True)"
            crone_rec=self.env["ir.cron"].sudo().create({
                "name":name,
                "model_id":model_id,
                "state":"code",
                "code":code,
                "doall":False
                })
            self.crone_id=crone_rec.id
        else:
            raise UserError("More Than One Cron Cannot Be Created")

        pass
