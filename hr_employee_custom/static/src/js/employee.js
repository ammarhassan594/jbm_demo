odoo.define('hr_employee_custom.employee', function (require) {
    "use strict";

    var session = require('web.session');
    var BasicView = require('web.BasicView');
    BasicView.include({
        init: function (viewInfo, params) {
            var self = this;
            this._super.apply(this, arguments);
            // var model = self.controllerParams.modelName == 'hr.employee' ? 'True' : 'False';
            // if (model == "True") {
                session.user_has_group('security_rules.group_fusion_employee').then(function (has_group) {
                    if (has_group) {
                        self.controllerParams.archiveEnabled = 'False' in viewInfo.fields;
                    } else {
                        self.controllerParams.archiveEnabled = 'active' in viewInfo.fields;
                    }
                });
            // } else {
            //     self.controllerParams.archiveEnabled = 'active' in viewInfo.fields;
            // }
        },
    });


});