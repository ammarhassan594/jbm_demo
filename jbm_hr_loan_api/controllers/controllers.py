# -*- coding: utf-8 -*-


from odoo import http
from odoo.http import request


class EmployeeLoanApi(http.Controller):
    @http.route("/GetEmployeeLoans", auth="public", type="json", methods=["POST"])
    def get_employee(self, **kwargs):

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
            employee_loans = request.env['hr.loan'].sudo().search(
                [('employee_id', '=', employee.id), ('state', '=', 'paid')])
            if employee_loans:
                for loan in employee_loans:
                    print('loan.loan_lines::', len(loan.loan_lines))
                    data.append(
                        {'loan_type': loan.loan_type.name,
                         'loan_amount': loan.loan_amount,
                         'installment_amount': loan.loan_lines[1].amount if len(loan.loan_lines) > 1 else 0,
                         'remaining_loan': loan.balance_amount
                         }
                    )
                # data.update({
                #     employee.name: {loan.name: {
                #         'loan type': loan.loan_type.name,
                #         'loan amount': loan.loan_amount,
                #         'Installment amount': loan.loan_amount - loan.first_paid_amount,
                #         'Remaining of loan': loan.balance_amount,
                #     } for loan in employee_loans}
                # })
        if not data:
            data = "There Is No Loans For This Employee"

        return data
