# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import date

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


class LeaveApi(http.Controller):
    @http.route('/GetEmployeeLeaves/', auth='public', type="json", methods=["POST"])
    def get_employee_leaves(self, **kw):
        params = request.httprequest.args.to_dict()
        leaves = []
        data = []
        if params.get("username") and params.get("date_from") and params.get("date_to"):
            username = params.get("username")
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

            user = request.env['res.users'].sudo().search([
                ('login', '=', username)
            ])
            if user:
                employee = request.env['hr.employee'].sudo().search([
                    ('user_id', '=', user.id)
                ])
                if employee:
                    leaves = request.env['hr.leave'].sudo().search([
                        ('date_from', '>=', date_from),
                        ('date_to', '<=', date_to),
                        ('employee_id', '=', employee.id),
                        ('state', '=', 'validate')
                    ])
                    if leaves:
                        # leaves_data = leaves.read(['employee_id', 'date_from', 'date_to', 'number_of_days','holiday_status_id'])
                        # for leave_data in leaves_data:
                        for leave_data in leaves:
                            data.append({
                                "employee_id": leave_data.employee_id.name,
                                "date_from": leave_data.date_from if leave_data.date_from else '',
                                "date_to": leave_data.date_to if leave_data.date_to else '',
                                "number_of_days": leave_data.number_of_days,
                                "holiday_status_id": leave_data.holiday_status_id.name,
                            })
                            # data.append(serialize_data(leave_data))
        return data

    @http.route('/GetEmployeeBalance/', auth='public', type="json", methods=["POST"])
    def get_employee_balance(self, **kw):
        params = request.httprequest.args.to_dict()
        duration_balance = []
        if params.get("username"):
            username = params.get("username")
            user = request.env['res.users'].sudo().search([
                ('login', '=', username)
            ])
            if user:
                employee = request.env['hr.employee'].sudo().search([
                    ('user_id', '=', user.id)
                ], limit=1)
                if employee:
                    today = date.today()
                    now = datetime.now()
                    allocations = request.env['hr.leave.allocation'].sudo().search([
                        ('date_from', '<=', today),
                        ('state', '=', 'validate'),
                        ('employee_id', '=', employee.id)
                    ]).filtered(lambda x: x.date_from.year == date.today().year)
                    allocation_leave_type = allocations.mapped('holiday_status_id')
                    for leave_type in allocation_leave_type:
                        alloca = allocations.filtered(lambda x: x.holiday_status_id == leave_type)
                        balance = sum(alloca.mapped('remaining_leaves'))
                        if alloca.holiday_status_id.request_unit == 'hour' and employee.contract_id and employee.contract_id.resource_calendar_id and \
                                employee.contract_id.resource_calendar_id.hours_per_day:
                            hours_per_day = employee.contract_id.resource_calendar_id.hours_per_day
                            balance /= hours_per_day
                        duration_balance.append({'leave_type': leave_type.name,
                                                 'balance': balance})

        return duration_balance
