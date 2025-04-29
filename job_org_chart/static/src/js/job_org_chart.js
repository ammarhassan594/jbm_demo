odoo.define('web.JobOrgChart', function (require) {
"use strict";

var AbstractField = require('web.AbstractField');
var concurrency = require('web.concurrency');
var core = require('web.core');
var field_registry = require('web.field_registry');
var session = require('web.session');

var QWeb = core.qweb;
var _t = core._t;

var FieldJobOrgChart = AbstractField.extend({

    events: {
        "click .o_job_redirect": "_onJobRedirect",
        "click .o_job_sub_redirect": "_onJobSubRedirect",
        "click .o_job_more_managers": "_onJobMoreManager"
    },
    /**
     * @constructor
     * @override
     */
    init: function (parent, options) {
        this._super.apply(this, arguments);
        this.dm = new concurrency.DropMisordered();
//        this.employee = null;
        this.job = null;
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------
    /**
     * Get the chart data through a rpc call.
     *
     * @private
     * @param {integer} employee_id
     * @returns {Promise}
     */
    _getOrgData: function () {
        var self = this;
        return this.dm.add(this._rpc({
            route: '/hr/get_org_job_chart',
            params: {
                job_id: this.job,
                context: session.user_context,
            },
        })).then(function (data) {
            return data;
        });
    },
    /**
     * Get subordonates of an employee through a rpc call.
     *
     * @private
     * @param {integer} employee_id
     * @returns {Promise}
     */
    _getSubordinatesData: function (job_id, type) {
        return this.dm.add(this._rpc({
            route: '/hr/get_job_subordinates',
            params: {
                job_id: job_id,
                subordinates_type: type,
                context: session.user_context,
            },
        }));
    },
    /**
     * @override
     * @private
     */

//     for edits **
    _render: function () {
        if (!this.recordData.id) {
            return this.$el.html(QWeb.render("job_org_chart", {
                managers: [],
                children: [],
            }));
        }
        else if (!this.job) {
            // the widget is either dispayed in the context of a hr.employee form or a res.users form
            this.job = this.recordData.job_ids !== undefined ? this.recordData.job_ids.res_ids[0] : this.recordData.id;
        }

        var self = this;
        return this._getOrgData().then(function (orgData) {
            if (_.isEmpty(orgData)) {
                orgData = {
                    managers: [],
                    children: [],
                }
            }
            orgData.view_job_id = self.recordData.id;
            self.$el.html(QWeb.render("job_org_chart", orgData));
            self.$('[data-toggle="popover"]').each(function () {
                $(this).popover({
                    html: true,
                    title: function () {
                        var $title = $(QWeb.render('job_orgchart_emp_popover_title', {
                            job: {
                                name: $(this).data('emp-name'),
                                id: $(this).data('emp-id'),
                            },
                        }));
                        $title.on('click','.o_job_redirect', _.bind(self._onJobRedirect, self));
                        return $title;
                    },
                    container: this,
                    placement: 'left',
                    trigger: 'focus',
                    content: function () {
                        var $content = $(QWeb.render('hr_orgchart_job_popover_content', {
                            job: {
                                id: $(this).data('emp-id'),
                                name: $(this).data('emp-name'),
                                direct_sub_count: parseInt($(this).data('emp-dir-subs')),
                                indirect_sub_count: parseInt($(this).data('emp-ind-subs')),
                            },
                        }));
                        $content.on('click',
                            '.o_job_sub_redirect', _.bind(self._onJobSubRedirect, self));
                        return $content;
                    },
                    template: QWeb.render('hr_orgchart_job_popover', {}),
                });
            });
        });
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    _onJobMoreManager: function(event) {
        event.preventDefault();
        this.job = parseInt($(event.currentTarget).data('job-id'));
        this._render();
    },
    /**
     * Redirect to the employee form view.
     *
     * @private
     * @param {MouseEvent} event
     * @returns {Promise} action loaded
     */
    _onJobRedirect: function (event) {
        var self = this;
        event.preventDefault();
        var job_id = parseInt($(event.currentTarget).data('job-id'));
        return this._rpc({
            model: 'hr.job',
            method: 'get_formview_action',
            args: [job_id],
        }).then(function(action) {
            return self.do_action(action);
        });
    },
    /**
     * Redirect to the sub employee form view.
     *
     * @private
     * @param {MouseEvent} event
     * @returns {Promise} action loaded
     */
    _onJobSubRedirect: function (event) {
        event.preventDefault();
        var job_id = parseInt($(event.currentTarget).data('emp-id'));
        var job_name = $(event.currentTarget).data('emp-name');
        var type = $(event.currentTarget).data('type') || 'direct';
        var self = this;
        if (job_id) {
            this._getSubordinatesData(job_id, type).then(function(data) {
                var domain = [['id', 'in', data]];
                return self._rpc({
                    model: 'hr.job',
                    method: 'get_formview_action',
                    args: [job_id],
                }).then(function(action) {
                    action = _.extend(action, {
                        'name': _t('Job Position'),
                        'view_mode': 'kanban,list,form',
                        'views':  [[false, 'kanban'], [false, 'list'], [false, 'form']],
                        'domain': domain,
                        'context': {
                            'default_parent_id': job_id,
                        }
                    });
                    delete action['res_id'];
                    return self.do_action(action);
                });
            });
        }
    },
});

field_registry.add('job_org_chart', FieldJobOrgChart);

return FieldJobOrgChart;

});
