from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.web import Home


class CustomerPortalCustom(CustomerPortal):
    """
    Overwritting the controller to show apps pages
    """
    _portal_object_name = "ba_appointment_id"

    @http.route(['/appointments', '/appointments/page/<int:page>',
                 '/appointments/<int:active_step>',
                 '/appointments/<int:active_step>/page/<int:page>',
                 ], type='http', auth="public", website=True)
    def ba_super_controller(self, active_step=None, url_ba_type_id=None, url_resource_ids=None, url_service_id=None,
                            progress_step=None, confirmation_code=None, page=1, sortby=None, filterby=None, search=None,
                            search_in='name', **kw):
        main_view = request.context.get('main_view')

        if not main_view and not request.params.get('progress_step') and not active_step:
            res = request.render("business_appointment_tus.main_page_appointment")
        else:
            # res = request.render("business_appointment_tus.validate_email_tu")
            res = super(CustomerPortalCustom, self).ba_super_controller(active_step=active_step,
                                                                        url_ba_type_id=url_ba_type_id,
                                                                        url_resource_ids=url_resource_ids,
                                                                        url_service_id=url_service_id,
                                                                        progress_step=progress_step,
                                                                        confirmation_code=confirmation_code, page=page,
                                                                        sortby=sortby, filterby=filterby, search=search,
                                                                        search_in=search_in, **kw)
        return res

    @http.route('/appointments/result', type='http', auth="public", website=True)
    def check_load_id_or_not(self, active_step=None, url_ba_type_id=None, url_resource_ids=None, url_service_id=None,
                            progress_step=None, confirmation_code=None, page=1, sortby=None, filterby=None, search=None,
                            search_in='name', **post):
        ibl_ids = request.env['freight.freight'].sudo().search([('reference', 'ilike', post.get('load_number')), ('stage_id', '=', 'New'), ('is_outbound', '=', False)])
        obl_ids = request.env['freight.freight'].sudo().search([('reference', 'ilike', post.get('load_number')), ('outbound_stage_id', '=', 'New'), ('is_outbound', '!=', False)])
        data = ibl_ids + obl_ids
            # data = request.env['freight.freight'].sudo().search([('reference', 'ilike', post.get('load_number')), ('active', '=', True), ('outbound_stage_id', 'ilike', 'new'), ('stage_id', 'ilike', 'new')])
        if data and post.get('load_number'):
            request.update_context(main_view=True)
            if data and len(data) == 1:
                request.session.update({'freight_id': data.id})
            if data and len(data) == 1 and not request.context.get('uid'):
                return request.redirect(f'/web/login')
            else:
                return self.ba_super_controller(active_step=None, url_ba_type_id=None, url_resource_ids=None,
                                                url_service_id=None,
                                                progress_step=None, confirmation_code=None, page=1, sortby=None, filterby=None,
                                                search=None,
                                                search_in='name')
        else:
            values = post
            return request.render('business_appointment_tus.load_id_not_found', values)

    def _ba_finish_appointment(self, appointment_ids, session_appointment_id):
        res = super(CustomerPortalCustom, self)._ba_finish_appointment(appointment_ids, session_appointment_id)
        if len(appointment_ids) == 1:
            values = {"appointment_id": appointment_ids}
            freight_id = appointment_ids.x_oz_cbaf_3
            freight_id.write({"pickup_schedule_date": appointment_ids.datetime_start})
            res = request.render("business_appointment_tus.confirm_appointment_tu", values)
        return res

    def _step5_prepare_values(self, session_appointment_id, durl="", **kw):
        res = super(CustomerPortalCustom, self)._step5_prepare_values(session_appointment_id, durl="", **kw)
        if session_appointment_id.x_oz_cbaf_3:
            request.session['freight_id'] = session_appointment_id.x_oz_cbaf_3.id
        if not res.get('x_oz_cbaf_3'):
            res.update({'x_oz_cbaf_3': request.session and request.session.get('freight_id') or False})
        return res


class CustomHome(Home):

    @http.route()
    def web_login(self, redirect=None, **kw):
        res = super(CustomHome, self).web_login(redirect, **kw)
        if res and res.location in ['web','/my'] and request.params.get('login_success',False) and request.session.get('freight_id') and not request.params.get('name'):
            return request.redirect('/appointments/result')
        elif res and res.location in ['web','/my'] and request.params.get('login_success',False) and not request.params.get('name'):
            return request.redirect('/appointments')
        return res






    # @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    # def web_auth_signup(self, *args, **kw):
    #     res = super(CustomHome, self).web_auth_signup(*args, **kw)
    #     if request.session.uid:
    #         request.session.logout(keep_db=True)
    #         return request.redirect("/validate_mail")
    #     else:
    #         return res
    #
    # @http.route('/validate_mail', type='http', auth='public', website=True)
    # def validate_email_tu(self, **kw):
    #     return http.request.render("business_appointment_tus.validate_email_tu")
