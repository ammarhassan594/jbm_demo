odoo.define('sla_activity_type.SlaActivityType', function (require) {
"use strict";

    var core = require('web.core');
    var Widget = require('web.Widget');
    var rpc = require('web.rpc');
    var Dialog = require('web.Dialog');

    var _t = core._t;
    console.log('test sla');

    var YourWidget = Widget.extend({
        events: {
            'click .o_ChatterTopbar_buttonScheduleActivityType': 'openWizard',
        },

        openWizard: function () {
            rpc.query({
                model: 'your.model.name',
                method: 'your_wizard_function_name',
                args: [this.recordID],  // Pass any required arguments
            }).then(function (result) {
                // Handle the result if needed
                // For example, you can display a message or update the UI
                if (result) {
                    // Do something with the result
                }
            });
        },
    });

    return YourWidget;
});


