odoo.define('jbm_letter_request.DashboardLetterRequest', function (require) {
"use strict";
var DashboardRewrite = require('jbm_portal_self_service.DashboardRewrite');

console.log('DashboardRewrite ', DashboardRewrite)

DashboardRewrite.include({

    hr_certificate: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

             this.do_action('jbm_letter_request.letter_request_self_service_user_act_window', options)
        },


});

return DashboardRewrite;
});