odoo.define('ebs_hr_custom.FormController', function (require) {
"use strict";

var BasicController = require('web.BasicController');
var FormController = require('web.FormController');
var core = require('web.core');
var Dialog = require('web.Dialog');
var dialogs = require('web.view_dialogs');
var rpc = require('web.rpc');
var _t = core._t;
var qweb = core.qweb;

var core = require('web.core');
var QWeb = core.qweb;
var field_utils = require("web.field_utils")
var session = require('web.session');
var rpc = require('web.rpc')
var widgetRegistry = require('web.widget_registry');
var Widget = require('web.Widget');

var schedule_date_widget = Widget.extend({
	template: 'schedule_date_widget',
	events:{
	    'click .save-record':'saveRecord',
	    'click .close-modal':'closeModal',
    },
	 init: function (parent, employee_id, changes) {
	    this.employee_id = employee_id
	    this.changes = changes
	    this.parent = parent
        return this._super.apply(this, arguments);
    },
    start: function () {
        var self = this;
        return this._super.apply(self, arguments).then(() => {
            $(self.$el).modal('show');
            $(self.$el).on('hidden.bs.modal', _.bind(self.destroy, self));
        });
    },
    saveRecord: function(){
        var self = this;
        var employee_id = this.employee_id
        var changes = this.changes
        var schedule_date;
        var fieldValue = document.getElementById("schedule_date").value;
        var model;
        if(this.parent.modelName && this.parent.modelName == 'hr.employee' || this.parent.modelName == 'hr.contract'){
            model = this.parent.modelName
        }
        if(!fieldValue){
             alert("Please select date.");
             return false;
        }
        else{
            schedule_date = fieldValue;
            this._rpc({
                model: model,
                method: "action_write_effective_date",
                args: [employee_id, schedule_date],
            })
            .then(function (result){
                self.save();
            });
        }
    },
    save: function(){
        this.parent.saveRecord();
        $(self.$el).modal('hide');
        location.reload();
    },
    closeModal:function(ev){
        location.reload();
    },
});

widgetRegistry.add("schedule_date_widget", schedule_date_widget)

FormController.include({
    display_popup: function(employee_id, changes, changed){
        if(changed.length > 0){
            var ScheduleDateWidget= new schedule_date_widget(this, employee_id, changes);
            ScheduleDateWidget.appendTo(this.$el);
        }else{
            this.saveRecord().then(this._enableButtons.bind(this)).guardedCatch(this._enableButtons.bind(this));
        }
    },
    _onSave: function (ev) {
        ev.stopPropagation(); // Prevent x2m lines to be auto-saved
        this._disableButtons();
        var is_new =  this.model.isNew(this.handle)
        var changes = this.model.localData[this.handle]._changes
        var changed = []
        var emp_fields_list = ['registration_number', 'name', 'main_project', 'marital', 'department_id', 'sponsorship_type', 'sponsor', 'payroll_group',
        'permanent_staff_employee', 'contract_status', 'country_id', 'job_id', 'gender', 'parent_id', 'line_manager_id']
        var contract_fields_list = ['registration_number', 'employee_id', 'permanent_staff_employee', 'payroll_group', 'resource_calendar_id']
        var self = this;
        if(changes){
            var changedFields = Object.keys(changes);
            const intersection = changedFields.filter(element => emp_fields_list.includes(element));
            const contract_intersection = changedFields.filter(element => contract_fields_list.includes(element));
            if(this.modelName == "hr.employee" && !is_new && intersection.length > 0){
                var changedFields = Object.keys(changes);
                self.display_popup(this.model.localData[this.handle].res_id, changes, changedFields);
            }else if(this.modelName == "hr.contract" && !is_new && contract_intersection.length > 0){
                var changedFields = Object.keys(changes);
                self.display_popup(this.model.localData[this.handle].res_id, changes, changedFields);
            }
            else{
                this.saveRecord().then(this._enableButtons.bind(this)).guardedCatch(this._enableButtons.bind(this));
            }
        }else{
            this.saveRecord().then(this._enableButtons.bind(this)).guardedCatch(this._enableButtons.bind(this));
        }
    },
});

});
