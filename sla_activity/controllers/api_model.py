import datetime

from odoo import http, fields, models
from odoo.http import request


class SlaActivityModels(http.Controller):

    @http.route("/GetDataModels/", auth="public", type="json", methods=["POST"])
    def get_data_models(self, **kwargs):
        data = []
        params = request.httprequest.args.to_dict()
        model_name = ''
        return_record = False
        request_code = ''
        department = ''
        if params.get("model_name"):
            model_name = params.get("model_name")
        if params.get("return_record"):
            return_record = params.get("return_record")
        if params.get("request_code"):
            request_code = params.get("request_code")
        if params.get("department"):
            print('dep:::', department)
            department = params.get("department")

        if model_name and model_name == 'approval.request':
            if request_code:
                model_id = request.env['ir.model'].sudo().search([
                    ('model', '=', model_name)
                ])
                state_field = model_id.state_field_id.name if model_id and model_id.state_field_id else False
                state_value = model_id.value_state_field.value if model_id and model_id.value_state_field else False
                approval_type = request.env['approval.category'].sudo().search([
                    ('sequence_code', '=', request_code)
                ], limit=1)
                approval_data = request.env[model_id.model].sudo().search([
                    ('category_id', '=', approval_type.id),
                    ('request_status', 'not in', ['approved', 'refused', 'cancel'])
                ]) if model_id and approval_type else False
                if department:
                    data = approval_data.filtered(
                        lambda record: record.department.id == department) if approval_data else False
                else:
                    data = approval_data if approval_data else False

                if return_record:
                    if return_record == 'false':
                        # total_data = len(data)
                        data_on_time = 0
                        data_not_on_time = 0
                        if data:
                            for record in data:
                                submition_date = record.date_confirmed if record.date_confirmed else False
                                actual_approval_date = record.approval_date if record.approval_date else False
                                sumDueDate_total_days = sum(record.category_id.approver_ids.mapped(
                                    'date_deadline_after')) if record.category_id and record.category_id.approver_ids else False
                                SLADueDate_max_date = submition_date + datetime.timedelta(
                                    days=int(sumDueDate_total_days)) if submition_date else False
                                if SLADueDate_max_date and actual_approval_date:
                                    if actual_approval_date <= SLADueDate_max_date:
                                        data_on_time += 1
                                    else:
                                        data_not_on_time += 1

                        values = [
                            {
                                "label": "نسبة الإنجاز على الوقت",
                                "data": [data_on_time]
                            },
                            {
                                "label": "نسبة المتأخرة",
                                "data": [data_not_on_time]
                            }
                        ]
                        name = ''
                        if model_id.model_type == 'internal':
                            name = 'تخصصى'
                        elif model_id.model_type == 'self_service':
                            name = 'ذاتى'

                        data = {"modelId": model_name,
                                'modelType': name,
                                "title": "Approval Request",
                                "dataReports": values,
                                "labels": ["نسبة الإنجاز على الوقت", "نسبة المتأخرة"],
                                }

                    elif return_record == 'true':
                        new_data = []
                        requestor = model_id.requestor_field_id.name
                        document_number = model_id.record_identifier_api.name
                        subject = model_id.subject_field_id.name
                        if data:
                            for record in data:
                                on_time = False
                                submition_date = record.date_confirmed if record.date_confirmed else False
                                actual_approval_date = record.approval_date if record.approval_date else False
                                sumDueDate_total_days = sum(record.category_id.approver_ids.mapped(
                                    'date_deadline_after')) if record.category_id and record.category_id.approver_ids else False
                                SLADueDate_max_date = submition_date + datetime.timedelta(
                                    days=int(sumDueDate_total_days)) if submition_date else False
                                if SLADueDate_max_date and actual_approval_date:
                                    if actual_approval_date <= SLADueDate_max_date:
                                        on_time = True
                                    else:
                                        on_time = False

                                time_taken = (
                                            actual_approval_date - submition_date).seconds if submition_date and actual_approval_date else False

                                # print('test22:::', model_id.requestor_field_id.name)
                                # print('test:::',
                                #       request.env[model_id.model].sudo()._fields.get(model_id.requestor_field_id.name))
                                # print('test333:::', request.env[model_id.model].sudo()._fields.keys())
                                # x = request.env[model_id.model].sudo()._fields.get(model_id.requestor_field_id.name)

                                # x = record.mapped(request.env[model_id.model].sudo()._fields.get(model_id.requestor_field_id.name))

                                request_url = record.env['ir.config_parameter'].sudo().get_param('web.base.url')
                                request_url += "/web" + "/#id=%s&view_type=form&model=approval.request" % (record.id)

                                is_requester_many2one = isinstance(record._fields[requestor],
                                                                   (fields.Many2one)) if requestor else ''
                                is_requester_char = isinstance(record._fields[requestor],
                                                               (fields.Char)) if requestor else ''
                                if not requestor or not document_number or not subject:
                                    raise ValueError(
                                        "These Fields ( Identifier Api	, Requestor Field, Subject Field) Must be added in the model")
                                if is_requester_many2one and actual_approval_date:
                                    user_id = getattr(record, requestor, None).id
                                    arabic_name = record.env['hr.employee'].search([('user_id', '=', user_id)]).arabic_name
                                    line = {"requestor": arabic_name if requestor else '',
                                            'document_number': getattr(record, document_number,
                                                                       None) if document_number else '',
                                            "request_date": submition_date if submition_date else '',
                                            "time_taken": time_taken / 86400 if time_taken else '',
                                            "subject": getattr(record, subject, None) if subject else '',
                                            "on_time": on_time,
                                            "request_url": request_url}
                                    new_data.append(line)
                                elif is_requester_char and actual_approval_date:
                                    line = {"requestor": getattr(record, requestor, None) if requestor else '',
                                            'document_number': getattr(record, document_number,
                                                                       None) if document_number else '',
                                            "request_date": submition_date if submition_date else '',
                                            "time_taken": time_taken / 86400 if time_taken else '',
                                            "subject": getattr(record, subject, None) if subject else '',
                                            "on_time": on_time,
                                            "request_url": request_url}
                                    new_data.append(line)

                        data = new_data

            else:
                return "Must Add Request Code Of Approval Request Model"

        elif model_name and model_name == 'hr.leave':
            if request_code:
                leave_type = request.env['hr.leave.type'].sudo().search([
                    ('name', '=', request_code)
                ])
                if not leave_type:
                    raise ValueError('Not Found  Request Code(Leave type) Like %s', request_code)
                if leave_type:
                    model_id = request.env['ir.model'].sudo().search([
                        ('model', '=', model_name)
                    ])
                    state_field = model_id.state_field_id.name if model_id and model_id.state_field_id else False
                    state_value = model_id.value_state_field.value if model_id and model_id.value_state_field else False
                    leave_data = request.env[model_id.model].sudo().search([
                        ('holiday_status_id', '=', leave_type.id),
                        (state_field, '!=', state_value)
                    ]) if model_id and state_field and state_value else False
                    if department:
                        data = leave_data.filtered(
                            lambda record: record.department_id.name == department) if leave_data else False
                    else:
                        data = leave_data if leave_data else False

                    if return_record:
                        if return_record == 'false':
                            on_time_data = 0
                            not_on_time_data = 0
                            if data:
                                for record in data:
                                    start_date = record.create_date
                                    sumDueDate = 0
                                    if record.holiday_status_id.leave_validation_type == 'hr':
                                        sumDueDate = record.holiday_status_id.time_off_officer_days
                                    elif record.holiday_status_id.leave_validation_type == 'manager':
                                        sumDueDate = record.holiday_status_id.employee_approver_days
                                    elif record.holiday_status_id.leave_validation_type == 'both':
                                        sumDueDate = record.holiday_status_id.employee_approver_days + record.holiday_status_id.time_off_officer_days
                                    SLADueDate_max = record.create_date + datetime.timedelta(days=int(sumDueDate))
                                    actual_approva_date = record.approval_date if record.approval_date else False

                                    if actual_approva_date and SLADueDate_max:
                                        if actual_approva_date <= SLADueDate_max:
                                            on_time_data += 1
                                        else:
                                            not_on_time_data += 1
                            values = [
                                {
                                    "label": "نسبة الإنجاز على الوقت",
                                    "data": [on_time_data]
                                },
                                {
                                    "label": "نسبة المتأخرة",
                                    "data": [not_on_time_data]
                                }
                            ]

                            name = ''
                            if model_id.model_type == 'internal':
                                name = 'تخصصى'
                            elif model_id.model_type == 'self_service':
                                name = 'ذاتى'

                            data = {"modelId": model_name,
                                    "modelType": name,
                                    "title": "Hr Leave Request",
                                    "dataReports": values,
                                    "labels": ["نسبة الإنجاز على الوقت", "نسبة المتأخرة"]}
                        elif return_record == 'true':
                            new_data = []
                            requestor = model_id.requestor_field_id.name
                            document_number = model_id.record_identifier_api.name
                            subject = model_id.subject_field_id.name
                            if data:
                                for record in data:
                                    on_time = False
                                    start_date = record.create_date
                                    actual_approva_date = record.approval_date if record.approval_date else False
                                    sumDueDate = 0
                                    if record.holiday_status_id.leave_validation_type == 'hr':
                                        sumDueDate += record.holiday_status_id.time_off_officer_days
                                    elif record.holiday_status_id.leave_validation_type == 'manager':
                                        sumDueDate += record.holiday_status_id.employee_approver_days
                                    elif record.holiday_status_id.leave_validation_type == 'both':
                                        sumDueDate += record.holiday_status_id.employee_approver_days + record.holiday_status_id.time_off_officer_days
                                    SLADueDate_max = record.create_date + datetime.timedelta(days=int(sumDueDate))
                                    if actual_approva_date and SLADueDate_max:
                                        if actual_approva_date <= SLADueDate_max:
                                            on_time = True
                                        else:
                                            on_time = False

                                    Time_Taken = (
                                                actual_approva_date - start_date).seconds if actual_approva_date else False

                                    request_url = record.env['ir.config_parameter'].sudo().get_param('web.base.url')
                                    request_url += "/web" + "/#id=%s&view_type=form&model=hr.leave" % (record.id)

                                    is_requester_many2one = isinstance(record._fields[requestor],
                                                                       (fields.Many2one)) if requestor else ''
                                    is_requester_char = isinstance(record._fields[requestor],
                                                                   (fields.Char)) if requestor else ''

                                    if not requestor or not document_number or not subject:
                                        raise ValueError(
                                            "These Fields ( Identifier Api	, Requestor Field, Subject Field)Must be added in the model")

                                    if is_requester_many2one and actual_approva_date:
                                        line = {"requestor": getattr(record, requestor, None).name if requestor else '',
                                                'document_number': getattr(record, document_number,
                                                                           None) if document_number else '',
                                                "request_date": start_date if start_date else '',
                                                "time_taken": Time_Taken / 86400 if Time_Taken else '',
                                                "subject": getattr(record, subject, None) if subject else '',
                                                "on_time": on_time,
                                                "request_url": request_url}
                                        new_data.append(line)
                                    elif is_requester_char and actual_approva_date:
                                        line = {"requestor": getattr(record, requestor, None) if requestor else '',
                                                'document_number': getattr(record, document_number,
                                                                           None) if document_number else '',
                                                "request_date": start_date if start_date else '',
                                                "time_taken": Time_Taken / 86400 if Time_Taken else '',
                                                "subject": getattr(record, subject, None) if subject else '',
                                                "on_time": on_time,
                                                "request_url": request_url}
                                        new_data.append(line)

                            data = new_data
            else:
                raise ValueError('Must Add Request Code(Leave type) Of Hr Leave Model')

        elif model_name and model_name not in ['hr.leave', 'approval.request']:
            model_id = request.env['ir.model'].sudo().search([
                ('model', '=', model_name)
            ])
            advance_approvals = request.env['dynamic.approval'].sudo().search([
                ('model_id', '=', model_id.id), ('is_sla', '=', True)
            ]) if model_id else False
            if advance_approvals:
                state_field = model_id.state_field_id.name if model_id and model_id.state_field_id else False
                state_value = model_id.value_state_field.value if model_id and model_id.value_state_field else False
                if state_field and state_value:
                    model_data = request.env[model_id.model].sudo().search([
                        (state_field, '!=', state_value)
                    ])
                    data = model_data if model_data else False
                    if data:
                        if department:
                            requester_field_id = model_id.requestor_field_id if model_id and model_id.requestor_field_id else False
                            if requester_field_id:
                                if requester_field_id.ttype == 'many2one':
                                    if requester_field_id.relation == 'res.users':
                                        requester_field_name = requester_field_id.name
                                        data = data.filtered(lambda record: getattr(record, requester_field_name,
                                                                                    None).employee_id.department_id.id == int(
                                            department))
                                    elif requester_field_id.relation == 'hr.employee':
                                        requester_field_name = requester_field_id.name
                                        data = data.filtered(lambda record: getattr(record, requester_field_name,
                                                                                    None).department_id.id == int(
                                            department))
                                    elif requester_field_id.relation == 'hr.department':
                                        requester_field_name = requester_field_id.name
                                        data = data.filtered(lambda record: getattr(record, requester_field_name,
                                                                                    None).id == int(
                                            department))
                            else:
                                raise ValueError('Not Value in requester_field_id in model', model_id.name)
                        if return_record:
                            if return_record == 'false':
                                on_time = 0
                                not_on_time = 0
                                for record in data:
                                    if record.dynamic_approve_request_ids:
                                        submition_data = record.dynamic_approve_request_ids[0].create_date
                                        sumDueDate = sum(
                                            record.dynamic_approval_id.approval_level_ids.mapped('in_days')) if \
                                            record.dynamic_approval_id.approval_level_ids else False
                                        SLADueDate_max_date = submition_data + datetime.timedelta(days=int(sumDueDate))
                                        actual_approval_date = record.dynamic_approve_request_ids[-1].approve_date if (
                                            record.dynamic_approve_request_ids[-1].approve_date) else False
                                        if actual_approval_date and SLADueDate_max_date:
                                            if actual_approval_date <= SLADueDate_max_date:
                                                on_time += 1
                                            else:
                                                not_on_time += 1
                                values = [
                                    {
                                        "label": "نسبة الإنجاز على الوقت",
                                        "data": [on_time]
                                    },
                                    {
                                        "label": "نسبة المتأخرة",
                                        "data": [not_on_time]
                                    }
                                ]
                                name = ''
                                if model_id.model_type == 'internal':
                                    name = 'تخصصى'
                                elif model_id.model_type == 'self_service':
                                    name = 'ذاتى'

                                data = {"modelId": model_name,
                                        "modelType": name,
                                        "title": model_id.name,
                                        "dataReports": values,
                                        "labels": ["نسبة الإنجاز على الوقت", "نسبة المتأخرة"],
                                        }
                            elif return_record == 'true':
                                new_data = []
                                requestor = model_id.requestor_field_id.name
                                document_number = model_id.record_identifier_api.name
                                subject = model_id.subject_field_id.name
                                for record in data:
                                    if record.dynamic_approve_request_ids:
                                        on_time = False
                                        submition_data = record.dynamic_approve_request_ids[0].create_date
                                        sumDueDate = sum(
                                            record.dynamic_approval_id.approval_level_ids.mapped('in_days')) if \
                                            record.dynamic_approval_id.approval_level_ids else False

                                        SLADueDate_max_date = submition_data + datetime.timedelta(days=int(sumDueDate))
                                        actual_approval_date = record.dynamic_approve_request_ids[-1].approve_date if (
                                            record.dynamic_approve_request_ids[-1].approve_date) else False
                                        if actual_approval_date and SLADueDate_max_date:
                                            if actual_approval_date <= SLADueDate_max_date:
                                                on_time = True
                                            else:
                                                on_time = False

                                        time_taken = (
                                                    actual_approval_date - submition_data).seconds if submition_data and actual_approval_date else False

                                        request_url = record.env['ir.config_parameter'].sudo().get_param('web.base.url')
                                        request_url += "/web" + "/#id=%s&view_type=form&model=%s" % (
                                        record.id, model_name)

                                        is_requester_many2one = isinstance(record._fields[requestor],
                                                                           (fields.Many2one)) if requestor else ''
                                        is_requester_char = isinstance(record._fields[requestor],
                                                                       (fields.Char)) if requestor else ''

                                        if not requestor or not document_number or not subject:
                                            raise ValueError(
                                                "These Fields ( Identifier Api	, Requestor Field, Subject Field) Must be added in the model")
                                        if is_requester_many2one and actual_approval_date:
                                            line = {
                                                "requestor": getattr(record, requestor, None).name if requestor else '',
                                                'document_number': getattr(record, document_number,
                                                                           None) if document_number else '',
                                                "request_date": submition_data if submition_data else '',
                                                "time_taken": time_taken / 86400 if time_taken else '',
                                                "subject": getattr(record, subject, None) if subject else '',
                                                "on_time": on_time,
                                                "request_url": request_url}
                                            new_data.append(line)
                                        elif is_requester_char and actual_approval_date:
                                            line = {"requestor": getattr(record, requestor, None) if requestor else '',
                                                    'document_number': getattr(record, document_number,
                                                                               None) if document_number else '',
                                                    "request_date": submition_data if submition_data else '',
                                                    "time_taken": time_taken / 86400 if time_taken else '',
                                                    "subject": getattr(record, subject, None) if subject else '',
                                                    "on_time": on_time,
                                                    "request_url": request_url}
                                            new_data.append(line)
                                data = new_data
                else:
                    raise ValueError('Set state_field_id or value_state_field in SLA API of model ', model_id.name)
            else:
                raise ValueError('No SLA Set For This Model')
        return data
