from odoo import api, fields, models, _


class EBS_hr_employee_e_contract(models.Model):
    _name = 'hr.employee.econtract'
    _description = 'HR Employee Econtract'

    employee_id = fields.Many2one('hr.employee')
    fullname = fields.Char("Fullname")

    employees_address = fields.Text("Employees Address")
    zone_no = fields.Char("Zone No")
    street_no = fields.Char("Street No")
    building_no = fields.Char("Building No")

    nationality_id = fields.Many2one('res.country', "Nationality")
    passport_number = fields.Char("Passport Number")
    work_visa_number = fields.Char("Work Visa Number")
    qatar_id = fields.Char("Qatar Id")
    joining_date = fields.Date("Joining Date")
    basic_salary = fields.Char("Basic Salary")
    food_allowance = fields.Char("Food Allowance")
    housing_allowance = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Housing Allowance")
    transportation_allowance = fields.Char("Transportation Allowance")
    other_allownce = fields.Char("Other Allowance")
    total_salary = fields.Char("Total Salary")
    probation_period = fields.Char("Probation Period")
    contract_duration = fields.Char("Contract Duration")
    ticket_eligibility = fields.Char("Contract Duration")
