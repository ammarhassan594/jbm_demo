# -*- coding: utf-8 -*-
from datetime import date
from odoo import fields, models, api, _
from odoo.exceptions import Warning, UserError
from sys import platform
from datetime import datetime
from dateutil import relativedelta
from pytz import timezone


class EmployeeGratuity(models.Model):
    _inherit = 'hr.gratuity'

    # Create Payslip
    def create_payslip(self):
        last_payslip = self.env['hr.payslip'].search([('employee_id', '=', self.employee_id.id)], limit=1)
        att_sheets = self.env['attendance.sheet'].search([('employee_id', '=', self.employee_id.id),
                                                          ('actual_date_to', '>', last_payslip.date_to)])
        for each_att_sheet in att_sheets:
            if self.employee_id.status in ['suspended', 'terminated', 'terminated_w_reason', 'resigned']:
                payslip = self.env['hr.payslip']
                # for att_sheet in each_att_sheet:
                if each_att_sheet.payslip_id:
                    new_payslip = each_att_sheet.payslip_id
                    continue

                employee = each_att_sheet.employee_id
                salary_rules = []
                res = {
                    'name': 'draft',
                    'contract_id': employee.contract_id.id,
                    'employee_id': employee.id,
                    'gratuity_id': self.id,
                    'has_gratuity': True,
                    'date_from': each_att_sheet.actual_date_from,
                    'date_to': each_att_sheet.actual_date_to,
                    'actual_day_from': each_att_sheet.actual_date_from,
                    'actual_day_to': each_att_sheet.actual_date_to,
                    'remarks': each_att_sheet.note,
                }
                if each_att_sheet.batch_id and each_att_sheet.batch_id.payslip_batch_id:
                    res['payslip_run_id'] = each_att_sheet.batch_id.payslip_batch_id.id
                new_payslip = payslip.create(res)
                # add Accommodation Allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'ACCOMM')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.accommodation_allowance
                })
                # add Transport Allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'TRA')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.transportation_allowance
                })
                # add Food Allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'FOOD')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.food_allowance
                })
                # add site Allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'Site')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.site_allowance
                })
                # add mobile Allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'MOBILE')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.mobile_allowance
                })
                # add other Allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'OTHER')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.other_allowance
                })
                # add ticket Allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'TICKET')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.ticket_allowance
                })

                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LAUNDRY')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.laundry_allowance
                })
                # add Earning Settlement Allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'EARNING')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.earning_allowance
                })

                # add Social Allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'SOCIAL')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.social_allowance
                })
                # add leave advance Allowance

                # add furniture Allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'FURNITURE')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.furniture_allowance
                })

                # add leave basic salary allowance to
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADW')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.leave_advance_wage
                })
                # add leave accommodation allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADACM')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.leave_advance_accommodation
                })
                # add leave mobile allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADMO')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.leave_advance_mobile_allowance
                })
                # add leave food allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADFDW')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.leave_advance_food_allowance
                })
                # add leave site allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADSTW')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.leave_advance_site_allowance
                })
                # add leave transportation allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADTRW')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.leave_advance_transport_allowance
                })
                # add leave other allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADOTHW')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.leave_advance_other_allowance
                })
                # add leave uniform allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADUNIFORM')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.leave_advance_uniform_allowance
                })
                # add leave social allowance
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADSOC')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': each_att_sheet.leave_advance_social_allowance
                })
                # add leave wage deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADWD')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.leave_advance_wage_ded
                })
                # add leave accommodation deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADACMD')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.leave_advance_accommodation_ded
                })
                # add leave mobile deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADMOD')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.leave_advance_mobile_ded
                })
                # add leave food deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADFDWD')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.leave_advance_food_ded
                })
                # add leave site deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADSTWD')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.leave_advance_site_ded
                })
                # add leave transportation deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADTRWD')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -
                    each_att_sheet.leave_advance_transport_ded
                })
                # add leave other deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADOTHWD')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.leave_advance_other_ded
                })
                # add leave uniform deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADUNID')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.leave_advance_uniform_ded
                })
                # add leave social deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LADSOCD')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.leave_advance_social_ded
                })
                # add Basic Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'BASICDED')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.basic_deduction
                })
                # add Other Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'OTHERDED')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.other_deduction
                })

                # add Transport Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'TRANSDED')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.transportation_deduction
                })
                # add Accommodation Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'ACCOMMDED')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.accommodation_deduction
                })
                # add Mobile Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'MOBILEDED')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.mobile_deduction
                })
                # add Laundry Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'UNIFORMDED')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.uniform_deduction
                })
                # add Social Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'SOCIALDED')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.social_deduction
                })
                # add Site Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'SITEDED')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.site_deduction
                })
                # add overtime Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'OVERTDED')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.overtime_deduction
                })
                # add Deduction Settlement
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'SETTLEDED')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.deduction_settlements
                })
                # add Loan Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LO')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.loan_deduction
                })
                # add Car Loan Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LOANDED')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.car_loan_deduction
                })
                # add Marriage Loan Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'MARLOANDED')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.marriage_loan_deduction
                })
                # add Leave Advance Payment Deduction
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LAP')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.advance_leave_count_days
                })
                # add Employee Pension
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'PE')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.pension_employee
                })
                # add Employer Pension
                acc_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'PER')], limit=1)
                salary_rules.append({
                    'code': acc_input_type.code,
                    'contract_id': each_att_sheet.contract_id.id,
                    'input_type_id': acc_input_type.id,
                    'payslip_id': new_payslip.id,
                    'sequence': 1,
                    'amount': -each_att_sheet.pension_employer
                })
                self.env['hr.payslip.input'].create(salary_rules)
                new_payslip.compute_sheet()
                self.attendance_sheets = [(4, each_att_sheet.id)]
