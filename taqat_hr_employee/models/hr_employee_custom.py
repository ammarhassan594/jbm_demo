from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    emp_serial_number = fields.Char('Employee Number')
    nationality = fields.Char(string="nationality", related="country_id.nationality", store=True)

    @api.model
    def create(self, vals):
        # For Generating Sequence For Employee
        rec = super(HrEmployeeInherit, self).create(vals)
        rec.emp_serial_number = self.env['ir.sequence'].next_by_code('employee.sequence')
        return rec

    def state_approve(self):
        if any(self.document_o2m.filtered(lambda x: x.status == 'na')):
            raise UserError("You can't approve because in document status there is NA")
        else:
            return super(HrEmployeeInherit, self).state_approve()
