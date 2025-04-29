# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    orientation = fields.Boolean(string="Orientation")
    employee_system_ids = fields.One2many(comodel_name="hr.employee.system", inverse_name="employee_id",
                                          string="Employee Systems")
    employee_procedure_ids = fields.One2many(comodel_name="hr.employee.procedure", inverse_name="employee_id",
                                             string="Employee Procedures")


class HrEmployeeSystem(models.Model):
    _name = "hr.employee.system"
    _description = "Employee Systems Lines"

    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee", ondelete="cascade")
    employee_system_id = fields.Many2one(comodel_name="employee.system", string="System", required=True)
    link = fields.Char(string="Link", required=True)


class EmployeeSystem(models.Model):
    _name = "employee.system"
    _description = "Employee Systems"

    name = fields.Char(string="System", required=True)


class HrEmployeeProcedure(models.Model):
    _name = "hr.employee.procedure"
    _description = "Employee Procedure"

    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee", ondelete="cascade")
    procedure_name_id = fields.Many2one(comodel_name="internal.regulations", string="Procedure Name", required=True)
