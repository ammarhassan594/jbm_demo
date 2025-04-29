# -*- coding: utf-8 -*-
import calendar
from datetime import datetime

from odoo import http
from odoo.http import request


class PayslipApi(http.Controller):
    @http.route('/GetEmployeePayslip/', auth="public", type="json", methods=["POST"])
    def get_employee_payslip(self, **kw):
        params = request.httprequest.args.to_dict()
        payslip_lines = []
        if params.get("year") and params.get("month") and params.get("username"):
            year = int(params.get("year"))
            month = int(params.get("month"))
            month_first_day = datetime(year, month, 1)
            last_day = calendar.monthrange(month_first_day.year, month_first_day.month)[1]
            month_last_day = datetime(year, month, last_day)

            username = params.get("username")
            user = request.env['res.users'].sudo().search([
                ('login', '=', username)
            ])
            if user:
                employee = request.env['hr.employee'].sudo().search([
                    ('user_id', '=', user.id)
                ])

                if employee:
                    payslip = request.env['hr.payslip'].sudo().search([
                        ('date_from', '<=', month_first_day),
                        ('date_to', '>=', month_last_day),
                        ('employee_id', '=', employee.id),
                        ('state', '=', 'paid'),
                    ], limit=1)
                    if payslip:
                        for line in payslip.line_ids:
                            if line.amount and line.category_id.code not in ('NET', 'COMP'):
                                payslip_lines.append(
                                    {'id': line.id, 'name': line.salary_rule_id.name, 'amount': line.amount})
        return payslip_lines
