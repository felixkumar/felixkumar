odoo.define('header_layout.login_popup_custom', function(require) {
    "use strict";

    $(document).ready(function() {
        /** Login / Signup Popup **/
       $(document).on('click', '.te_signup', function() {
            $.fn._myCartPop();
            $("#loginRegisterPopup a[href='#loginPopup']").removeClass('active');
            $("#loginRegisterPopup #loginPopup").removeClass('show active');
            $("#loginRegisterPopup a[href='#registerPopup']").addClass('active');
            $("#loginRegisterPopup #registerPopup").addClass('active');
            $("#loginRegisterPopup .oe_signup_form_ept").show();
            $(document).mouseup(function (e) {
                if ($(e.target).closest(".modal-body").length === 0) {
                    $("#loginRegisterPopup").removeClass("show modal_shown").hide();
                }
            });
            });
        });
       $(document).on('click', '.te_signin', function() {
            $.fn._myCartPop();
            $("#loginRegisterPopup a[href='#registerPopup']").removeClass('active');
            $("#loginRegisterPopup #registerPopup").removeClass('active');
            $("#loginRegisterPopup a[href='#loginPopup']").addClass('active');
            $("#loginRegisterPopup #loginPopup").addClass('show active');

            $("#loginRegisterPopup .oe_login_form").show();
            $(document).mouseup(function (e) {
                if ($(e.target).closest(".modal-body").length === 0) {
                    $("#loginRegisterPopup").removeClass("show modal_shown").hide();
                }
            });
       });
});