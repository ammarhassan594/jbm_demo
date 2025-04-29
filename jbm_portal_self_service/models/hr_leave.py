from odoo import models, fields, api, _


class InheritHrLeave(models.Model):
    _inherit = 'hr.leave'

    remaining_balance = fields.Float(string="Remaining Balance", compute="_get_remaining_balance")

    @api.depends('holiday_status_id', 'employee_id', 'request_date_from')
    def _get_remaining_balance(self):
        for record in self.sorted('date_from'):
            if record.employee_id and record.holiday_status_id:
                request_date_from = record.request_date_from if record.request_date_from else fields.Date.today()
                year_first_day = request_date_from.replace(day=1, month=1)
                year_last_day = request_date_from.replace(day=31, month=12)
                allocations = self.env['hr.leave.allocation'].search([
                    ('holiday_status_id', '=', record.holiday_status_id.id),
                    ('employee_id', '=', record.employee_id.id),
                    ('state', '=', 'validate'), ('date_from', '>=', year_first_day)
                ]).filtered(lambda allocation:
                            allocation.date_to and allocation.date_to >= request_date_from >= allocation.date_from and allocation.date_to <= year_last_day
                            or (not allocation.date_to and allocation.date_from <= request_date_from))
                leaves = self.search([('holiday_status_id', '=', record.holiday_status_id.id),
                                      ('employee_id', '=', record.employee_id.id),
                                      ('state', '=', 'validate'), ('request_date_from', '>=', year_first_day),
                                      ('request_date_from', '<', request_date_from)])
                allocation_duration_list = allocations.mapped(
                    'number_of_hours_display') if record.holiday_status_id.request_unit == 'hour' else allocations.mapped(
                    'number_of_days')
                leaves_duration_list = leaves.mapped(
                    'number_of_hours_display') if record.holiday_status_id.request_unit == 'hour' else leaves.mapped(
                    'number_of_days')

                remaining_leaves = sum(allocation_duration_list) - sum(leaves_duration_list)
                record.remaining_balance = remaining_leaves
            else:
                record.remaining_balance = 0.0

    @api.model
    def recalculate_leave_remaining_balance(self):
        leaves = self.search([('state', '!=', 'refuse')])
        leaves._get_remaining_balance()
