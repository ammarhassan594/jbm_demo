odoo.define('jbm_portal_self_service.SelfService', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var _t = core._t;


var SelfServiceDashboard = AbstractAction.extend({


    contentTemplate: 'SelfServiceDashboardMain',

     events: {
             'click .hr_service':'hr_service',
             'click .management_service':'management_service',
             'click .it_service':'it_service',
    },


        hr_service: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
//            var $action = $(ev.currentTarget);


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

             this.do_action('jbm_portal_self_service.hr_services_action_dashboard', options)
        },

        management_service: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
//            var $action = $(ev.currentTarget);


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

             this.do_action('jbm_portal_self_service.administrative_services_action_dashboard', options)
        },
        it_service: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
//            var $action = $(ev.currentTarget);


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

             this.do_action('jbm_portal_self_service.it_services_action_dashboard', options)
        },


   });

    core.action_registry.add('self_service_dashboard', SelfServiceDashboard);

return SelfServiceDashboard;

});
