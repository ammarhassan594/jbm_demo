from odoo import models, fields, api, _
from odoo.addons.resource.models.resource import HOURS_PER_DAY


class Allocation(models.Model):
    _inherit = 'hr.leave.allocation'

    @api.depends('number_of_days', 'employee_id')
    def _compute_number_of_hours_display(self):
        for allocation in self:
            if allocation.number_of_days:
                allocation.number_of_hours_display = allocation.number_of_days * (
                        allocation.employee_id.sudo().resource_id.calendar_id.hours_per_day or HOURS_PER_DAY)
            else:
                allocation.number_of_hours_display = 0.0
