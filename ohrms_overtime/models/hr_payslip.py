from datetime import datetime

from odoo import models, api, fields


class PayslipOverTime(models.Model):
    _inherit = 'hr.payslip'

    def calculate_overtime(self, payslip, employee):
        special_ot = 0
        normal_ot = 0
        overtime_allowance = 0
        if payslip:
            overtime = self.env['hr.overtime'].search([('state', '=', 'approved'),
                                                       ('actual_date_from', '=', payslip.date_from),
                                                       ('actual_date_to', '=', payslip.date_to),
                                                       ('employee_id', '=', employee.id)], limit=1)
            normal_ot += overtime.t_normal_hours
            special_ot += overtime.t_special_hours
            # for ovt in overtime:
            #     for line in ovt.overtime_lines:
            #         if line.overtime_type == 'normal' and line.paid:
            #             normal_ot += line.hours
            #         elif line.overtime_type == 'special' and line.paid:
            #             special_ot += line.hours
            total_hours = normal_ot + special_ot
            hour_wage_in_house = employee.contract_id.wage / 30 / 8
            hour_wage_staff = employee.contract_id.wage / 21.75 / 8
            # if rec.employee_id.contract_id.resource_calendar_id.hours_per_day == 0:
            #     rec.employee_id.contract_id.resource_calendar_id.hours_per_day = 8
            # this code is for staff employee
            if employee.wassef_employee_type == 'perm_staff':
                if employee.permanent_staff_employee.name >= 8:
                    if special_ot >= 52:
                        overtime_allowance += special_ot * 1.5 * hour_wage_staff
                    elif total_hours >= 52:
                        total_hours = 52
                        overtime_allowance += (special_ot * 1.5 * hour_wage_staff) + (total_hours - special_ot) * \
                                                  1.25 * hour_wage_staff
                    else:
                        overtime_allowance += special_ot * 1.5 * hour_wage_staff + normal_ot * 1.25 * hour_wage_staff
                elif employee.permanent_staff_employee.name < 8:
                    overtime_allowance = 0
            # this is for in-house employees
            elif employee.wassef_employee_type == 'perm_in_house':
                overtime_allowance += (special_ot * 1.5 * hour_wage_in_house) + (normal_ot * 1.25 * hour_wage_in_house)
        return overtime_allowance

    def get_overtimes(self, payslip, employee):
        return self.env['hr.overtime'].search([('state', '=', 'approved'),
                                               ('actual_date_from', '=', payslip.date_from),
                                               ('actual_date_to', '=', payslip.date_to),
                                               ('employee_id', '=', employee.id)], limit=1)

    def get_sp_overtime_hours_amount(self, payslip, employee):
        special_ot_hours, special_ot_amount, normal_ot = (0, 0, 0)
        if payslip:
            overtime = self.get_overtimes(payslip, employee)
            special_ot_hours += overtime.t_special_hours
            normal_ot += overtime.t_normal_hours
            total_hours = normal_ot + special_ot_hours
            hour_wage = 0
            if employee.wassef_employee_type == 'perm_staff':
                hour_wage = employee.contract_id.wage / 21.75 / 8
            elif employee.wassef_employee_type == 'perm_in_house':
                hour_wage = employee.contract_id.wage / 30 / 8

            if employee.wassef_employee_type == 'perm_staff':
                if employee.permanent_staff_employee.name >= 8:
                    # Need to check business
                    if total_hours >= 52:
                        special_ot_amount += (special_ot_hours * 1.5 * hour_wage) + (total_hours - special_ot_hours) * \
                                             1.25 * hour_wage
                        return special_ot_hours, special_ot_amount
                    else:
                        special_ot_amount = special_ot_hours * 1.5 * hour_wage
                        return special_ot_hours, special_ot_amount
                elif employee.permanent_staff_employee.name < 8:
                    return special_ot_hours, special_ot_amount
            # this is for in-house employees
            elif employee.wassef_employee_type == 'perm_in_house':
                special_ot_amount = special_ot_hours * 1.5 * hour_wage
                return special_ot_hours, special_ot_amount

    def get_normal_overtime_hours_amount(self, payslip, employee):
        normal_ot_hours, normal_ot_amount, special_ot_hours = (0, 0, 0)
        if payslip:
            overtime = self.get_overtimes(payslip, employee)
            special_ot_hours += overtime.t_special_hours
            normal_ot_hours += overtime.t_normal_hours
            total_hours = normal_ot_hours + special_ot_hours
            hour_wage = 0
            if employee.wassef_employee_type == 'perm_staff':
                hour_wage = employee.contract_id.wage / 21.75 / 8
            elif employee.wassef_employee_type == 'perm_in_house':
                hour_wage = employee.contract_id.wage / 30 / 8

            if employee.wassef_employee_type == 'perm_staff':
                if employee.permanent_staff_employee.name >= 8:
                    # Need to check business
                    if special_ot_hours >= 52:
                        return normal_ot_hours, normal_ot_amount
                    elif total_hours >= 52:
                        return normal_ot_hours, normal_ot_amount
                    else:
                        normal_ot_amount = normal_ot_hours * 1.25 * hour_wage
                        return normal_ot_hours, normal_ot_amount
                elif employee.permanent_staff_employee.name < 8:
                    return normal_ot_hours, normal_ot_amount

            # this is for in-house employees
            elif employee.wassef_employee_type == 'perm_in_house':
                normal_ot_amount = normal_ot_hours * 1.25 * hour_wage
                return normal_ot_hours, normal_ot_amount

    # overtime_ids = fields.Many2many('hr.overtime')
    #
    #
    # # @api.onchange('employee_id', 'date_from', 'date_to')
    # # def onchange_employee(self):
    # #     if (not self.employee_id) or (not self.date_from) or (not self.date_to):
    # #         return
    # #     contracts = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)])
    # #     if contracts:
    # #         overtime_cutoff_day_setting = int(self.env['ir.config_parameter'].sudo().get_param('ebs_lb_payroll.overtime_cutoff_day'))
    # #         date_cutoff_from = datetime.strptime(
    # #             str(overtime_cutoff_day_setting) + '/' + str(self.date_to.month - 1) + '/' + str(self.date_to.year), '%d/%m/%Y').date()
    # #         date_cutoff_to = datetime.strptime(
    # #             str(overtime_cutoff_day_setting) + '/' + str(self.date_to.month) + '/' + str(self.date_to.year),
    # #             '%d/%m/%Y').date()
    # #         input_line_ids = self.get_inputs(contracts, date_cutoff_from, date_cutoff_to)
    # #         input_lines = self.input_line_ids.browse([])
    # #         for r in input_line_ids:
    # #             input_lines += input_lines.new(r)
    # #         self.input_line_ids = input_lines
    # #     return
    #
    # @api.model
    # def get_inputs(self, contracts, date_from, date_to):
    #     """
    #     function used for writing overtime record in payslip
    #     input tree.
    #
    #     """
    #     res = []
    #     input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'OV')])
    #     contract = self.contract_id
    #     overtime_id = self.env['hr.overtime'].search([('employee_id', '=', self.employee_id.id),
    #                                                   ('contract_id', '=', self.contract_id.id),
    #                                                   ('state', '=', 'approved'), ('payslip_paid', '=', False),
    #                                                   '|', '&',
    #                                                   ('date_from', '>=', date_from),
    #                                                   ('date_to', '<=', date_to),
    #                                                   '&',
    #                                                   ('date_validated', '>=', date_from),
    #                                                   ('date_validated', '<=', date_to),
    #                                                   ])
    #     hrs_amount = overtime_id.mapped('cash_hrs_amount')
    #     day_amount = overtime_id.mapped('cash_day_amount')
    #     cash_amount = sum(hrs_amount) + sum(day_amount)
    #     if overtime_id:
    #         self.overtime_ids = overtime_id
    #         input_data = {
    #             'name': input_type.name,
    #             'input_type_id': input_type[0].id,
    #             'amount': cash_amount,
    #             'contract_id': contract.id,
    #         }
    #         res.append(input_data)
    #     return res
    #
    # def action_payslip_done(self):
    #     """
    #     function used for marking paid overtime
    #     request.
    #
    #     """
    #     for recd in self.overtime_ids:
    #         if recd.type == 'cash':
    #             recd.payslip_paid = True
    #     return super(PayslipOverTime, self).action_payslip_done()
