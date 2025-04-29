from datetime import datetime, timedelta

from odoo import http, fields, models
from odoo.http import request


class DepartmentDashboard(http.Controller):

    @http.route("/GetDepartmentData/", auth="public", type="json", methods=["POST"])
    def get_department_data(self, **kwargs):
        data = []
        values = []
        params = request.httprequest.args.to_dict()
        department_id = params.get("departmentID")
        approval_categories = request.env['approval.category'].sudo().search(
            [('is_sla', '=', True), ('sequence_code', '!=', False)])
        approvals = request.env['approval.request'].sudo().search([
            ('category_id', 'in', approval_categories.ids),
            ('request_status', 'in', ['pending', 'under_approval'])]).filtered(lambda x: x.approver_ids)
        # pending_approvals = approvals and approvals.mapped('approver_ids').filtered(lambda x: x.status == 'pending')

        if department_id:
            dept_ids = request.env['hr.department'].sudo().search([('dashboard_id', '=', department_id)])
        else:
            dept_ids = request.env['hr.department'].sudo().search([('dashboard_id', '!=', False)])

        for dept in dept_ids:
            date_deadline_after, data_on_time, data_not_on_time, total_records = 0, 0, 0, 0
            dept_with_child = dept + dept_ids.mapped('child_ids')
            for approval in approvals:
                # pending_approval = approval.mapped('approver_ids').filtered(lambda x: x.status == 'pending')
                # if pending_approval and pending_approval.approve_type == 'user' and approval.user_id.employee_id.department_id == dept.id:
                for line in approval.approver_ids:
                    date_deadline_after += line.date_deadline_after
                    if line.status == 'pending':
                        if ((line.approve_type == 'user' and line.user_id.employee_id.department_id.id in dept_with_child.ids) or
                                (line.approve_type == 'group' and line.group_id.users and line.group_id.users.sorted(key=lambda x:x.sequence)[
                                    0].employee_id.department_id.id in dept_with_child.ids)):
                            approvals -= approval
                            submission_date = approval.date_confirmed
                            SLADueDate_max_date = submission_date + timedelta(
                                days=int(date_deadline_after)) if submission_date else False
                            if SLADueDate_max_date:
                                # in case date_deadline_after == 0 what will be the case since all has to approve at the same time
                                if datetime.now() <= SLADueDate_max_date:
                                    data_on_time += 1
                                    total_records += 1
                                else:
                                    data_not_on_time += 1
                                    total_records += 1

                values = [
                    {
                        "label": "نسبة الإنجاز على الوقت",
                        "data": [data_on_time]
                    },
                    {
                        "label": "نسبة المتأخرة",
                        "data": [data_not_on_time]
                    }]

            data.append({"departmentId": dept.dashboard_id,
                         'departmentName': dept.name,
                         "dataReports": values,
                         "totalRecords": total_records,
                         "labels": ["نسبة الإنجاز على الوقت", "نسبة المتأخرة"],
                         })
        return data

    @http.route("/GetDepartmentConsolidatedData/", auth="public", type="json", methods=["POST"])
    def get_department_consolidated_data(self, **kwargs):
        data = []
        values = []
        params = request.httprequest.args.to_dict()
        department_id = params.get("departmentID")
        consolidated_models = request.env['consolidated.state'].sudo().search([])
        if department_id:
            dept_ids = request.env['hr.department'].sudo().search([('dashboard_id', '=', department_id)])
        else:
            dept_ids = request.env['hr.department'].sudo().search([('dashboard_id', '!=', False)])
        for dept in dept_ids:
            dept_with_child = dept + dept_ids.mapped('child_ids')
            for model_id in consolidated_models:
                pending_line = model_id.consolidated_state_line_ids.filtered(lambda x: x.state == 'process')
                state_value = pending_line.field_state_id.value
                state_field = pending_line.field_id.name or ''

                model_records = request.env[model_id.model_id.model].sudo().search([(state_field, '=', state_value)],
                                                                                   order="create_date asc")

                for record in model_records:
                    data_on_time, data_not_on_time, total_records = 0, 0, 0
                    pending_approval = record.dynamic_approve_request_ids and record.dynamic_approve_request_ids.filtered(
                        lambda x: x.status == 'pending')
                    if ((
                            pending_approval and pending_approval.user_id and pending_approval.user_id.employee_id.department_id.id in dept_with_child.ids) or
                            (pending_approval and pending_approval.group_id.users and pending_approval.group_id.users.sorted(key=lambda x:x.sequence)[
                                0].employee_id.department_id.id in dept_with_child.ids)):
                        consolidated_models -= model_id

                        tracking_values = request.env['mail.tracking.value'].sudo().search(
                            [('model_name', '=', model_id.model_id.model)])
                        max_days = 0
                        max_days += sum(model_id.consolidated_state_line_ids.filtered(lambda x: x.state != 'process' and
                                                                                                x.sequence <= pending_line.sequence).mapped(
                            'time_in_days'))
                        today = datetime.now()
                        if model_id.consolidated_state_line_ids[0].default_state:
                            preparation_date = record.create_date
                            max_date = preparation_date + timedelta(days=int(max_days))
                            if today > max_date:
                                data_not_on_time += 1
                                total_records += 1
                            else:
                                data_on_time += 1
                                total_records += 1
                        else:
                            tracking_record = tracking_values.filtered(
                                lambda x: int(
                                    x.res_id) == record.id and x.selection_new_value_key ==
                                          model_id.consolidated_state_line_ids[0].field_state_id.value)
                            preparation_date = tracking_record and tracking_record[-1].created_on or False
                            max_date = preparation_date and preparation_date + timedelta(days=int(max_days))
                            if preparation_date and max_date:
                                if today < preparation_date:
                                    data_not_on_time += 1
                                    total_records += 1
                                else:
                                    data_on_time += 1
                                    total_records += 1
                    values = [
                        {
                            "label": "على الوقت",
                            "data": [data_on_time]
                        },
                        {
                            "label": "متأخر",
                            "data": [data_not_on_time]
                        }
                    ]

            data.append({"departmentId": dept.dashboard_id,
                         'departmentName': dept.name,
                         "dataReports": values,
                         "totalRecords": total_records,
                         "labels": ["نسبة الإنجاز على الوقت", "نسبة المتأخرة"],
                         })
        return data
