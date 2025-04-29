from odoo import models, fields, api


class InheritHrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    def action_validate(self):
        for allocation in self:
            if allocation.sudo().employee_ids:
                employee_model = self.sudo().env['ir.model'].search([
                    ('model', '=', 'hr.employee')
                ])
                if employee_model:
                    ooredo_employee_conf = self.sudo().env['dynamic.integration.configuration'].sudo().search([
                        ('model_id', '=', employee_model.id)
                    ])
                    if ooredo_employee_conf:
                        allocations = self.env['hr.leave.allocation'].sudo().search([])
                        max_leaves = False
                        leaves_taken = False
                        message = ''
                        for employee in allocation.sudo().employee_ids:
                            allocations = allocations.filtered(lambda record: employee in record.employee_ids and
                                                                              record.holiday_status_id.id == allocation.holiday_status_id.id and
                                                                              record.date_from.year == allocation.date_from.year)
                            if allocations:
                                max_leaves = sum(allocations.mapped('max_leaves'))
                                leaves_taken = sum(allocations.mapped('leaves_taken'))

                                remaining_leaves = max_leaves - leaves_taken
                                message = "تم إضافة رصيد (%s)، الرصيد الجديد: (%s) ." % (
                                    allocation.sudo().holiday_status_id.with_context(lang="ar_001").name, allocation.number_of_days_display)
                            if allocation.number_of_days > 0:
                                employee.sudo().with_context(message=message).send_sms_message()
        return super(InheritHrLeaveAllocation, self).action_validate()
