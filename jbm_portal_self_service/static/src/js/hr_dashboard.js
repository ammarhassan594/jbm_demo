odoo.define('jbm_portal_self_service.DashboardRewrite', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var _t = core._t;


var HrServicesDashboard = AbstractAction.extend({


    contentTemplate: 'HrDashboardMain',

     events: {
             'click .hr_leaves':'hr_leaves',
             'click .hr_permissions':'hr_permissions',
             'click .hr_loans':'hr_loans',
             'click .hr_allowances':'hr_allowances',
             'click .hr_certificate':'hr_certificate',
             'click .hr_resignation':'hr_resignation',
             'click .hr_clearances':'hr_clearances',
             'click .hr_approval_attendance':'hr_approval_attendance',
             'click .hr_change_data':'hr_change_data',
             'click .hr_job_card':'hr_job_card',
             'click .hr_work_start':'hr_work_start',
             'click .hr_performance_grievance':'hr_performance_grievance',
             'click .hr_attendance':'hr_attendance',
             'click .hr_contact':'hr_contact',
             'click .hr_attendance_record':'hr_attendance_record',
             'click .hr_violation_balance':'hr_violation_balance',
             'click .hr_appraisal':'hr_appraisal',
             'click .insurance_request':'insurance_request',
             'click .training_course':'training_course',
             'click .over_time':'over_time',

    },


        hr_leaves: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
//            var $action = $(ev.currentTarget);


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

             this.do_action({
                        name: _t("إجازات الموظفين"),
                        type: 'ir.actions.act_window',
                        res_model: 'hr.leave',
                        view_mode: 'tree,form,calendar',
                        views: [[false, 'list'],[false, 'form']],
                        target: 'current'
                    }, options)
        },
        hr_permissions: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

                          this.do_action('jbm_portal_self_service.hr_permissions_action', options)
        },

        hr_loans: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
//            var $action = $(ev.currentTarget);


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

             this.do_action({
                        name: _t("السلف"),
                        type: 'ir.actions.act_window',
                        res_model: 'hr.loan',
                        view_mode: 'tree,form',
                        views: [[false, 'list'],[false, 'form']],
                        target: 'current'
                    }, options)
        },

        hr_allowances: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
//            var $action = $(ev.currentTarget);


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

             this.do_action({
                        name: _t("المزايا الوظيفية"),
                        type: 'ir.actions.act_window',
                        res_model: 'allowance.request',
                        view_mode: 'tree,form',
                        views: [[false, 'list'],[false, 'form']],
                        target: 'current'
                    }, options)
        },

        hr_certificate: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
//            var $action = $(ev.currentTarget);


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

             this.do_action('jbm_portal_self_service.certification_portal_approval_category_action', options)
        },


        hr_resignation: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
//            var $action = $(ev.currentTarget);


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

             this.do_action('jbm_portal_self_service.resignation_portal_approval_category_action', options)
        },



        hr_clearances: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
//            var $action = $(ev.currentTarget);


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

             this.do_action('jbm_portal_self_service.clearances_portal_approval_category_action', options)
        },

        hr_approval_attendance: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

                          this.do_action('jbm_portal_self_service.attendance_approval_category_action', options)
        },


        hr_change_data: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

                          this.do_action('jbm_portal_self_service.change_data_approval_category_action', options)
        },

        hr_job_card: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

                          this.do_action('jbm_portal_self_service.job_card_approval_category_action', options)
        },

        hr_work_start: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

                          this.do_action('jbm_portal_self_service.work_start_approval_category_action', options)
        },


        hr_performance_grievance: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

                          this.do_action('jbm_portal_self_service.performance_grievance_approval_category_action', options)
        },

        hr_attendance: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

                          this.do_action('hr_attendance.hr_attendance_action', options)
        },


        hr_attendance_record: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

                          this.do_action('attendance_api_new.action_machine_attendance_record2', options)
        },

        hr_violation_balance: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

                          this.do_action('ake_attendance_sheet.hr_employee_violation_balance_tree_action', options)
        },

        hr_contact: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

                          this.do_action('jbm_portal_self_service.self_service_contact', options)
        },

        hr_appraisal: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

                          this.do_action('jbm_hr_appraisal.action_hr_appraisal_primary', options)
        },

        insurance_request: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
//            var $action = $(ev.currentTarget);


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

             this.do_action('jbm_portal_self_service.insurance_request_category_action', options)
        },

        training_course: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
//            var $action = $(ev.currentTarget);


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

             this.do_action('jbm_portal_self_service.training_course_category_action', options)
        },

        over_time: function(ev){
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
//            var $action = $(ev.currentTarget);


            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

             this.do_action('jbm_portal_self_service.over_time_category_action', options)
        },


   });

    core.action_registry.add('hr_services_dashboard', HrServicesDashboard);

return HrServicesDashboard;

});
