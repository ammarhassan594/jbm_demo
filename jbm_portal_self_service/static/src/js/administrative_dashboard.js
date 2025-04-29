odoo.define('jbm_portal_self_service.AdministrativeAffairsServices', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var _t = core._t;


var AdministrativeServicesDashboard = AbstractAction.extend({


    contentTemplate: 'AdministrativeDashboardMain',

     events: {
             'click .administrative_purchase':'administrative_purchase',

    },


        administrative_purchase: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
//            var $action = $(ev.currentTarget);


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

             this.do_action('jbm_portal_self_service.purchase_approval_category_action', options)
        },

   });

    core.action_registry.add('administrative_services_dashboard', AdministrativeServicesDashboard);

return AdministrativeServicesDashboard;

});
