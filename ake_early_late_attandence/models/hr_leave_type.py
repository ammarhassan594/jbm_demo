from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrLeaveTypeCustom(models.Model):
    _inherit = "hr.leave.type"

    is_casual_leave_type = fields.Boolean(string="Is Casual leave type")

    virtual_remaining_leaves = fields.Float(
        compute='_compute_leaves', search='_search_virtual_remaining_leaves', string='Virtual Remaining Time Off',
        help='Maximum Time Off Allowed - Time Off Already Taken - Time Off Waiting Approval')

    @api.constrains('is_casual_leave_type','request_unit')
    def check_is_casual_leave_type(self):
        for record in self:
            if record.is_casual_leave_type and len(self.search([('is_casual_leave_type', '=', True)])) > 1:
                raise UserError(_('Casual leave type is already exist'))
                # TODO check if this is a requirement on AKE
            # elif record.is_casual_leave_type and record.request_unit != 'hour':
            #     raise UserError(_('Casual leave type in taken leave must be hours'))



    @api.depends_context('employee_id', 'default_employee_id')
    def _compute_leaves(self):
        data_days = {}
        employee_id = self._get_contextual_employee_id()

        if employee_id:
            data_days = (self.get_employees_days(employee_id)[employee_id[0]] if isinstance(employee_id, list) else
                         self.get_employees_days([employee_id])[employee_id])

        for holiday_status in self:
            result = data_days.get(holiday_status.id, {})
            holiday_status.max_leaves = result.get('max_leaves', 0)
            holiday_status.leaves_taken = result.get('leaves_taken', 0)
            holiday_status.remaining_leaves = result.get('remaining_leaves', 0)
            holiday_status.virtual_remaining_leaves = result.get('remaining_leaves', 0)
            holiday_status.virtual_leaves_taken = result.get('virtual_leaves_taken', 0)
