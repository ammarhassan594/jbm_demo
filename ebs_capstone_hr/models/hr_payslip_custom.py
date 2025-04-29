from odoo import models, fields, api, _


class PayslipInheritForSponsor(models.Model):
    _inherit = 'hr.payslip'

    emp_sponsor = fields.Many2one(comodel_name="hr.employee.sponsor", related="employee_id.waseef_sponsor", string="Employee Sponsor",
                                  required=False)
