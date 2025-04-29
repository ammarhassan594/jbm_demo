# -*- coding: utf-8 -*-


from odoo import http
from odoo.http import request
from datetime import datetime, date
def serialize_data(data):
    if not isinstance(data, dict):
        return {}
    new_data = {}
    for key, value in data.items():
        if isinstance(value, tuple):
            new_data[key] = value[1]
        elif isinstance(value, (datetime, date)):
            new_data[key] = value.strftime("%d/%m/%Y %H:%M:%S")
        else:
            new_data[key] = value if value else ''
    return new_data


class EmployeePromotionApi(http.Controller):
    @http.route("/GetEmployeeGrade", auth="public", type="json", methods=["POST"])
    def get_employee_promotion(self, **kwargs):
        promotions =[]
        data = []
        params = request.httprequest.args.to_dict()
        if params.get("username"):
            username = params.get("username")
            user = request.env['res.users'].sudo().search([
                ('login', '=', username)
            ])
            if user:
                employees = request.env['hr.employee'].sudo().search([
                    ('user_id', '=', user.id)
                ])
                if not employees:
                    data = "There Is No Employee Has This Username"
        else:
            employees = request.env['hr.employee'].sudo().search([])
        for employee in employees:
            employee_promotions = request.env['employee.promotion'].sudo().search(
                [('employee_id', '=', employee.id), ('state', '=', 'approve')])
            if employee_promotions:
                data = []
                for promotion in employee_promotions:
                    promotions.append(
                        {
                            'grade': promotion.new_payscale_id.description if promotion.new_payscale_id else '',
                            'date_assigned': promotion.date_start,
                            'notes': promotion.description if promotion.description else ''
                        }
                    )
                for p in promotions:
                    data.append(serialize_data(p))

            # data.update({
            #     employee.name: {promotion.name: {
            #         'grade': promotion.new_payscale_id.name if promotion.new_payscale_id else '',
            #         'date_assigned': promotion.date_start,
            #         'notes': promotion.description
            #     } for promotion in employee_promotions}
            # })

            if not data:
                data = "There Is No Promotions For This Employee"

        return data
