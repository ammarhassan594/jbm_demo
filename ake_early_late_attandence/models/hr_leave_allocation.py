from odoo import models, fields, api, _


class Allocation(models.Model):
    _inherit = 'hr.leave.allocation'

    _sql_constraints = [
        ('duration_check',
         "CHECK( ( number_of_days != 0 AND allocation_type='regular') or (allocation_type != 'regular'))",
         "The duration must not be equal to 0."),
    ]
    remaining_leaves = fields.Float(compute='_compute_leaves', string="Remaining Leave")
    payslip_id = fields.Many2one(comodel_name='hr.payslip', string='Payslip',
                                   ondelete="cascade")

    @api.depends('employee_id', 'holiday_status_id', 'taken_leave_ids.number_of_days', 'taken_leave_ids.state')
    def _compute_leaves(self):
        res = super(Allocation, self)._compute_leaves()
        for rec in self:
            rec.remaining_leaves = rec.max_leaves - rec.leaves_taken
        return res
