from odoo import models, fields, api


class HREmployeeCustom(models.Model):
    _inherit = "hr.employee"

    letter_ids = fields.One2many('jbm.letter.request', 'employee_id',
                                 string='Letter Requests', readonly=True)
    letter_count = fields.Integer(compute='_compute_letter_count', string='Letters Count',
                                  groups="base.group_user")

    def _compute_letter_count(self):
        for employee in self:
            employee.letter_count = len(employee.letter_ids)

