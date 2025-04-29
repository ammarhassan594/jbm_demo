import datetime

from odoo import http, fields, models
from odoo.http import request
from datetime import timedelta, datetime


class SlaActivityModels(http.Controller):

    @http.route("/GetConsolidatedModels/", auth="public", type="json", methods=["POST"])
    def get_consolidated_models(self, **kwargs):
        data = []

        models = request.env['consolidated.state'].sudo().search([])
        for model in models:
            data.append(
                {
                    "model": model.model_id.model,
                    "name": model.model_id.with_context(lang="ar_001").name,
                }
            )
        return data

    @http.route("/GetConsolidatedData/", auth="public", type="json", methods=["POST"])
    def get_consolidated_data(self, **kwargs):
        params = request.httprequest.args.to_dict()
        models = False
        return_record = False
        data = []
        data_filtered = {}
        model_name = params.get("model_name") or ''
        return_record = params.get("return_record")
        if model_name:
            models = request.env['consolidated.state'].sudo().search([
                ('model_id', '=', model_name)
            ])
        else:
            models = request.env['consolidated.state'].sudo().search([])

        for model_id in models:
            # duplicate_state = self.check_if_there_is_repetition(model_id)
            # if duplicate_state:
            #     lines = model_id.consolidated_state_line_ids.filtered(lambda x: x.condition_type).sorted(
            #         key=lambda x: x.sequence)
            #     lines = model_id.consolidated_state_line_ids.sorted(
            #         key=lambda x: x.sequence)
            # else:
            lines = model_id.consolidated_state_line_ids
            state_values = model_id.consolidated_state_line_ids and {line.field_state_id.value: line.time_in_days for
                                                                     line in lines} or ''
            state_values_keys = list(state_values.keys())
            state_field = model_id.consolidated_state_line_ids and model_id.consolidated_state_line_ids[
                0].field_id.name or ''

            model_data = request.env[model_id.model_id.model].sudo().search([(state_field, 'in', state_values_keys)],
                                                                            order="create_date asc")
            # model_data = model_data.filtered(lambda x: x.id == 73)
            data_on_time = 0
            data_not_on_time = 0
            total_records = 0
            tracking_values = request.env['mail.tracking.value'].sudo().search(
                [('model_name', '=', model_id.model_id.model)])

            if model_data and return_record != 'true':
                for record in model_data:
                    max_days = 0
                    is_conditioned = False
                    record_state = getattr(record, lines[0].field_state_id.field_id.name, None)
                    lines_data = lines.filtered(lambda x: x.field_state_id.value == record_state)
                    for line in lines_data:
                        max_days += line.time_in_days
                        # record_state = getattr(record, line.field_state_id.field_id.name, None)
                        if line.condition_type and not line.is_condition_matched(record):
                            continue
                        if line.default_state:
                            preparation_date = record.create_date
                            max_date = preparation_date + timedelta(days=int(max_days))
                            today = datetime.now()
                            if today > max_date:
                                data_not_on_time += 1
                                total_records += 1
                                print('record', record.id, line.field_state_id.value, max_date, today)
                            else:
                                data_on_time += 1
                                total_records += 1

                        else:
                            tracking_record = tracking_values.filtered(
                                lambda x: int(
                                    x.res_id) == record.id and x.selection_new_value_key == line.field_state_id.value)
                            first_state = model_id.consolidated_state_line_ids[0]
                            if first_state and first_state.default_state:
                                submit_date = record.create_date
                            else:
                                first_state_tracking_record = tracking_values.filtered(
                                    lambda x: int(
                                        x.res_id) == record.id and x.selection_new_value_key == first_state.field_state_id.value)
                                submit_date = first_state_tracking_record and first_state_tracking_record[
                                    -1].created_on or False

                            preparation_date = tracking_record and tracking_record[-1].created_on or False
                            max_date = submit_date and submit_date + timedelta(days=int(max_days))
                            if preparation_date and max_date:
                                if preparation_date > max_date:
                                    data_not_on_time += 1
                                    total_records += 1
                                else:
                                    data_on_time += 1
                                    total_records += 1

                        if preparation_date:
                            if data_filtered.get(record.create_date.year):
                                if data_filtered.get(record.create_date.year).get(record.create_date.month):
                                    data_filtered[record.create_date.year][record.create_date.month] += 1
                                else:
                                    data_filtered.get(record.create_date.year).update({record.create_date.month: 1})
                            else:
                                data_filtered.update({record.create_date.year: {record.create_date.month: 1}})
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

                data.append({"modelId": model_id.model_id.model,
                             "title": model_id.model_id.with_context(lang="ar_001").name,
                             "total_records": total_records,
                             "dataReports": values,
                             "data_filtered": data_filtered,
                             "labels": ["على الوقت", "متأخر"],
                             })
                return data

            elif model_data and return_record:
                for record in model_data:
                    max_days = 0
                    is_conditioned = False

                    record_state = getattr(record, lines[0].field_state_id.field_id.name, None)
                    lines_data = lines.filtered(lambda x: x.field_state_id.value == record_state)
                    for line in lines_data:
                        max_days += line.time_in_days
                        # record_state = getattr(record, line.field_state_id.field_id.name, None)
                        requestor = model_id.requestor_field_id.name
                        document_number = model_id.record_identifier_api.name
                        if line.condition_type and not line.is_condition_matched(record):
                            continue

                        if line.default_state:
                            preparation_date = record.create_date
                            max_date = preparation_date + timedelta(days=int(max_days))
                            today = datetime.now()
                            time_taken = (today - preparation_date).total_seconds() if max_date else False
                            request_url = record.env['ir.config_parameter'].sudo().get_param('web.base.url')
                            request_url += "/web" + "/#id=%s&view_type=form&model=%s" % (
                                record.id, model_id.model_id.model)
                            print("record11", record)

                            is_requester_many2one = isinstance(record._fields[requestor],
                                                               (fields.Many2one)) if requestor else ''
                            is_requester_char = isinstance(record._fields[requestor],
                                                           (fields.Char)) if requestor else ''
                            if not requestor or not document_number:
                                return "These Fields ( Identifier Field, Requestor Field) Must be added in the model"
                            if is_requester_many2one and max_date and time_taken:
                                line = {
                                    'document_number': getattr(record, document_number,
                                                               None) if document_number else '',
                                    "requestor": getattr(record, requestor, None).name if requestor else '',
                                    "request_date": preparation_date if preparation_date else '',
                                    "on_time": False if today > max_date else True,
                                    "state": line.state,
                                    "time_taken": time_taken / 3600 if time_taken else '',
                                    "request_url": request_url
                                }
                                data.append(line)
                            elif is_requester_char and max_date and time_taken:
                                line = {
                                    'document_number': getattr(record, document_number,
                                                               None) if document_number else '',
                                    "requestor": getattr(record, requestor, None) if requestor else '',
                                    "request_date": preparation_date if preparation_date else '',
                                    "on_time": False if today > max_date else True,
                                    "state": line.state,
                                    "time_taken": time_taken / 3600 if time_taken else '',
                                    "request_url": request_url
                                }
                                data.append(line)

                        else:
                            tracking_record = tracking_values.filtered(
                                lambda x: int(
                                    x.res_id) == record.id and x.selection_new_value_key == line.field_state_id.value)
                            first_state = model_id.consolidated_state_line_ids[0]
                            if first_state and first_state.default_state:
                                submit_date = record.create_date
                            else:
                                first_state_tracking_record = tracking_values.filtered(
                                    lambda x: int(
                                        x.res_id) == record.id and x.selection_new_value_key == first_state.field_state_id.value)
                                submit_date = first_state_tracking_record and first_state_tracking_record[
                                    -1].created_on or False
                            preparation_date = tracking_record and tracking_record[-1].created_on or False
                            max_date = submit_date and submit_date + timedelta(days=int(max_days))
                            time_taken = (
                                    preparation_date - submit_date).total_seconds() if preparation_date else False
                            # print('record', record.id, preparation_date, max_date, time_taken)
                            print("record11", record)
                            request_url = record.env['ir.config_parameter'].sudo().get_param('web.base.url')
                            request_url += "/web" + "/#id=%s&view_type=form&model=%s" % (
                                record.id, model_id.model_id.model)
                            is_requester_many2one = isinstance(record._fields[requestor],
                                                               (fields.Many2one)) if requestor else ''
                            is_requester_char = isinstance(record._fields[requestor],
                                                           (fields.Char)) if requestor else ''
                            if not requestor or not document_number:
                                return "These Fields ( Identifier Field, Requestor Field) Must be added in the model"
                            if is_requester_many2one and max_date and time_taken:
                                user_id = getattr(record, requestor, None).id
                                arabic_name = record.env['hr.employee'].search(
                                    [('user_id', '=', user_id)]).arabic_name
                                line = {
                                    'document_number': getattr(record, document_number,
                                                               None) if document_number else '',
                                    "requestor": arabic_name if requestor else '',
                                    "request_date": submit_date if submit_date else '',
                                    "on_time": False if preparation_date > max_date else True,
                                    "state": line.state,
                                    "time_taken": time_taken / 3600 if time_taken else '',
                                    "request_url": request_url
                                }
                                data.append(line)
                            elif is_requester_char and max_date and time_taken:
                                line = {
                                    'document_number': getattr(record, document_number,
                                                               None) if document_number else '',
                                    "requestor": getattr(record, requestor, None) if requestor else '',
                                    "request_date": submit_date if submit_date else '',
                                    "on_time": False if preparation_date > max_date else True,
                                    "state": line.state,
                                    "time_taken": time_taken / 3600 if time_taken else '',
                                    "request_url": request_url
                                }
                                data.append(line)

                return data
        return data

    @http.route("/GetDataWithState/", auth="public", type="json", methods=["POST"])
    def get_consolidated_state_data(self, **kwargs):
        params = request.httprequest.args.to_dict()
        models = False
        data = []
        data_reports = []
        data_filtered = {}
        model_name = params.get("model_name") or ''
        if model_name:
            models = request.env['consolidated.state'].sudo().search([
                ('model_id', '=', model_name)
            ])
        else:
            # models = request.env['consolidated.state'].sudo().search([])
            return "You have to pass the model name to proceed"

        for model_id in models:
            duplicate_state = self.check_if_there_is_repetition(model_id)
            # if duplicate_state:
            #     lines = model_id.consolidated_state_line_ids.filtered(lambda x: x.condition_type).sorted(
            #         key=lambda x: x.sequence)
            # else:
            lines = model_id.consolidated_state_line_ids
            state_values = model_id.consolidated_state_line_ids and {line.field_state_id.value: line.time_in_days for
                                                                     line in lines} or ''
            state_values_keys = list(state_values.keys())
            state_field = model_id.consolidated_state_line_ids and model_id.consolidated_state_line_ids[
                0].field_id.name or ''

            model_data = request.env[model_id.model_id.model].sudo().search([(state_field, 'in', state_values_keys)],
                                                                            order='create_date asc')
            # model_data = model_data.filtered(lambda x: x.id == 245)
            data_on_time = 0
            data_not_on_time = 0
            total_records = 0
            tracking_values = request.env['mail.tracking.value'].sudo().search(
                [('model_name', '=', model_id.model_id.model)])

            if model_data:
                for record in model_data:
                    max_days = 0
                    record_state = getattr(record, lines[0].field_state_id.field_id.name, None)
                    lines_data = lines.filtered(lambda x: x.field_state_id.value == record_state)
                    for line in lines_data:
                        max_days += line.time_in_days
                        record_state = getattr(record, line.field_state_id.field_id.name, None)
                        if record_state == line.field_state_id.value:
                            if line.condition_type and not line.is_condition_matched(record):
                                continue

                            if line.default_state:
                                preparation_date = record.create_date
                                max_date = preparation_date + timedelta(days=int(max_days))
                                today = datetime.now()
                                if today <= max_date:
                                    if data_filtered.get(line.state):
                                        if data_filtered.get(line.state).get('total_records') and data_filtered.get(
                                                line.state).get('on_time'):
                                            data_filtered[line.state]["total_records"] += 1
                                            data_filtered[line.state]["on_time"] += 1
                                        else:
                                            data_filtered[line.state]["total_records"] = data_filtered[line.state].get(
                                                "total_records", 0) + 1
                                            data_filtered[line.state]["on_time"] = data_filtered[line.state].get(
                                                "on_time", 0) + 1
                                    else:
                                        data_filtered.update({line.state: {
                                            "total_records": 1,
                                            "on_time": 1,
                                            "not_on_time": 0}})
                                else:
                                    if data_filtered.get(line.state):
                                        if data_filtered.get(line.state).get('total_records') and data_filtered.get(
                                                line.state).get('not_on_time'):
                                            data_filtered[line.state]["total_records"] += 1
                                            data_filtered[line.state]["not_on_time"] += 1
                                        else:
                                            data_filtered[line.state]["total_records"] = data_filtered[line.state].get(
                                                "total_records", 0) + 1
                                            data_filtered[line.state]["not_on_time"] = data_filtered[line.state].get(
                                                "on_time", 0) + 1
                                    else:
                                        data_filtered.update({line.state: {
                                            "total_records": 1,
                                            "on_time": 0,
                                            "not_on_time": 1}})
                            else:
                                tracking_record = tracking_values.filtered(
                                    lambda x: int(
                                        x.res_id) == record.id and x.selection_new_value_key == line.field_state_id.value)
                                first_state = model_id.consolidated_state_line_ids[0]
                                if first_state and first_state.default_state:
                                    submit_date = record.create_date
                                else:
                                    first_state_tracking_record = tracking_values.filtered(
                                        lambda x: int(
                                            x.res_id) == record.id and x.selection_new_value_key == first_state.field_state_id.value)
                                    submit_date = first_state_tracking_record and first_state_tracking_record[
                                        -1].created_on or False
                                preparation_date = tracking_record and tracking_record[-1].created_on or False
                                max_date = submit_date and submit_date + timedelta(days=int(max_days))
                                if preparation_date:
                                    if max_date > preparation_date:
                                        if data_filtered.get(line.state):
                                            if data_filtered.get(line.state).get('total_records') and data_filtered.get(
                                                    line.state).get('on_time'):
                                                data_filtered[line.state]["total_records"] += 1
                                                data_filtered[line.state]["on_time"] += 1
                                            else:
                                                data_filtered[line.state]["total_records"] = data_filtered[
                                                                                                 line.state].get(
                                                    "total_records", 0) + 1
                                                data_filtered[line.state]["on_time"] = data_filtered[line.state].get(
                                                    "on_time", 0) + 1

                                        else:
                                            data_filtered.update({line.state: {
                                                "total_records": 1,
                                                "on_time": 1,
                                                "not_on_time": 0}})

                                    else:
                                        if data_filtered.get(line.state):
                                            if data_filtered.get(line.state).get('total_records') and data_filtered.get(
                                                    line.state).get('not_on_time'):
                                                data_filtered[line.state]["total_records"] += 1
                                                data_filtered.get(line.state)["not_on_time"] += 1
                                            else:
                                                data_filtered[line.state]["total_records"] = data_filtered[
                                                                                                 line.state].get(
                                                    "total_records", 0) + 1
                                                data_filtered[line.state]["not_on_time"] = data_filtered[
                                                                                               line.state].get(
                                                    "on_time", 0) + 1
                                        else:
                                            data_filtered.update({line.state: {
                                                "total_records": 1,
                                                "on_time": 0,
                                                "not_on_time": 1}})

                data.append({"modelId": model_name,
                             "title": model_id.model_id.with_context(lang="ar_001").name,
                             "dataReports": data_filtered,
                             })

        return data

    def check_if_there_is_repetition(self, model_id):
        states = model_id.consolidated_state_line_ids.mapped('field_state_id').mapped('value')
        if len(model_id.consolidated_state_line_ids) != len(states):
            return True
        return False
