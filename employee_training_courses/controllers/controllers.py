# -*- coding: utf-8 -*-
from datetime import datetime, date

from odoo import http
from odoo.http import request


def parse_date(date_string):
    try:
        # Try to parse with time format
        new_date = datetime.strptime(date_string, '%d/%m/%Y %H:%M:%S')
    except ValueError:
        try:
            # Try to parse without time format
            new_date = datetime.strptime(date_string, '%d/%m/%Y')
        except ValueError:
            raise ValueError("Invalid date format")

    return new_date


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


class EmployeeTrainingCourses(http.Controller):
    @http.route('/GetEmployeeTrainingCourses/', auth="public", type="json", methods=["POST"])
    def get_employee_training_courses(self, **kw):
        params = request.httprequest.args.to_dict()
        data = []
        if params.get("date_from") and params.get("date_to") and params.get("username"):
            try:
                date_from = parse_date(params.get('date_from'))
                date_from = date_from.strftime("%m/%d/%Y %H:%M:%S")

                date_to = parse_date(params.get('date_to'))
                date_to = date_to.strftime("%m/%d/%Y %H:%M:%S")
            except Exception as e:
                return {
                    'message': 'Invalid date format',
                    'error': 'date format must be DD/MM/YYYY HH:MM:SS or DD/MM/YYYY',
                    'code': 500,
                    'http_status': 500,
                }

            username = params.get("username")
            user = request.env['res.users'].sudo().search([
                ('login', '=', username)
            ])
            if user:
                employee = request.env['hr.employee'].sudo().search([
                    ('user_id', '=', user.id)
                ], limit=1)

                if employee:
                    courses = request.env['employee.course'].sudo().search([
                        ('employee_id', '=', employee.id),
                        ('date_taken', '>=', date_from),
                        ('date_taken', '<=', date_to)
                    ])
                    courses = courses.read([])
                    for c in courses:
                        data.append(serialize_data(c))
        return data
