# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
from odoo.osv import expression


class LeaveReport(models.Model):
    _inherit = "hr.leave.report"

    leave_type = fields.Selection([
        ('allocation', 'Allocation Request'),
        ('request', 'Leave Request')
        ], string='Request Type', readonly=True)

    @api.model
    def action_time_off_analysis(self):
        domain = [('holiday_type', '=', 'employee')]

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


class HolidaysType(models.Model):
    _inherit = "hr.leave.type"
    _description = "Leave Type"

    request_unit = fields.Selection([
        ('day', 'Day'), ('half_day', 'Half Day'), ('hour', 'Hours')],
        default='day', string='Take Leave in', required=True)
    create_calendar_meeting = fields.Boolean(string="Display Leave in Calendar", default=True)
    leave_notif_subtype_id = fields.Many2one('mail.message.subtype', string='Leave Notification Subtype', default=lambda self: self.env.ref('hr_holidays.mt_leave', raise_if_not_found=False))
