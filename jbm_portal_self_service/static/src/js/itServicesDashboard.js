odoo.define('jbm_portal_self_service.itServicesDashboard', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var _t = core._t;


var itServices_Dashboard = AbstractAction.extend({


    contentTemplate: 'itDashboardMain',

     events: {

             'click .it_access':'it_access',
             'click .it_approval':'it_approval',
             'click .it_equipment':'it_equipment',

    },

        it_access: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

                          this.do_action('jbm_portal_self_service.access_approval_category_action', options)
        },


        it_approval: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

                          this.do_action('jbm_portal_self_service.it_approval_category_action', options)
        },

        it_equipment: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
//            var $action = $(ev.currentTarget);


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

             this.do_action('jbm_portal_self_service.it_equipment_category_action', options)
        },




   });

    core.action_registry.add('it_services_dashboard', itServices_Dashboard);

return itServices_Dashboard;

});
