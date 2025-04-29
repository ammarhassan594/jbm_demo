from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime, time
from odoo.addons.resource.models.resource_mixin import timezone_datetime
from odoo.osv import expression


class HRLeaveReportCustom(models.Model):
    _inherit = "hr.leave.report"

    # can_approve_leave = fields.Boolean(string="Can Approve", default=False, compute='_can_approve', store=True)

    # override this action to change the string from time off analysis to leave analysis
    @api.model
    def action_time_off_analysis(self):
        domain = [('holiday_type', '=', 'employee'), ('state', 'in', ['validate'])]

        if self.env.context.get('active_ids'):
            domain = expression.AND([
                domain,
                [('employee_id', 'in', self.env.context.get('active_ids', []))]
            ])

        return {
            'name': _('Leave Analysis'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.leave.report',
            'view_mode': 'tree,form,pivot',
            'search_view_id': self.env.ref('hr_holidays.view_hr_holidays_filter_report').id,
            'domain': domain,
            'context': {
                'search_default_group_type': True,
                'search_default_year': True
            }
        }
