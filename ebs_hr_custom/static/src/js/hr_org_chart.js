odoo.define('ebs_hr_custom.orgchart', function (require) {
    "use strict";
    var HROrgchart = require('web.OrgChart');

    var waseefHROrgchart = HROrgchart.include({

        _onEmployeeRedirect: function (event) {
            var self = this;
            event.preventDefault();
//            var employee_id = parseInt($(event.currentTarget).data('employee-id'));
            return false;
            //        return this._rpc({
            //            model: 'hr.employee',
            //            method: 'get_formview_action',
            //            args: [employee_id],
            //        }).then(function(action) {
            //            return self.do_action(action);
            //        });
        },

    });

    return waseefHROrgchart;
});
