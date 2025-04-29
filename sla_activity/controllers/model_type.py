import datetime

from odoo import http
from odoo.http import request


class SlaActivityModelsType(http.Controller):

    @http.route("/GetDataModelType/", auth="public", type="json", methods=["POST"])
    def get_data_model_type(self, **kwargs):
        data = []
        params = request.httprequest.args.to_dict()

        self_service_number = 0
        self_service_on_time = 0
        self_service_not_on_time = 0

        internal_number = 0
        internal_on_time = 0
        internal_not_on_time = 0

        department = ''
        if params.get("department"):
            department = params.get("department")

        approval_request = request.env['ir.model'].sudo().search([
            ('model', '=', 'approval.request')
        ])
        state_field = approval_request.state_field_id.name
        state_value = approval_request.value_state_field.value

        approval_data = request.env[approval_request.model].sudo().search([
            ('request_status', 'not in', ['approved', 'refused', 'cancel']), ('category_id.is_sla', '=', True), ('category_id.sequence_code', '!=', False)
        ]) if approval_request else False

        if approval_data:
            if department:
                approval_data = approval_data.filtered(lambda record: record.department.id == department)

            for record in approval_data:
                submition_date = record.date_confirmed if record.date_confirmed else False
                actual_approval_date = record.approval_date if record.approval_date else False
                sumDueDate_total_days = sum(record.category_id.approver_ids.mapped(
                    'date_deadline_after')) if record.category_id and record.category_id.approver_ids else False
                SLADueDate_max_date = submition_date + datetime.timedelta(
                    days=int(sumDueDate_total_days)) if submition_date else False
                if SLADueDate_max_date and actual_approval_date:
                    if approval_request.model_type:
                        print("id", record.id)
                        print("sequence", record.category_id.sequence_code)
                        internal_number += 1
                        if actual_approval_date <= SLADueDate_max_date:
                            internal_on_time += 1
                        else:
                            internal_not_on_time += 1

        data = [
            {'model_type': 'internal',
             'total_number_of_records': internal_number,
             'on_time': internal_on_time,
             'not_on_time': internal_not_on_time,

             }]
        return data
