odoo.define('business_appointment_tus.disable_fields', function(require) {
    "use strict";
    $(document).ready(function() {
         $('select[name="x_oz_cbaf_3"]').css('pointer-events','none')
    });
});

//odoo.define('business_appointment_tus.disable_fields', function(require) {
//    "use strict";
//    $(document).ready(function() {
//        debugger
//         $('select[name="x_oz_cbaf_3"]').prop('disabled', true);
//        debugger;
//        $(document).on('click', '.btn_forward_checkout', function(e) {
//            $('select[name="x_oz_cbaf_3"]').prop('disabled', false);
//        });
//    });
//});
