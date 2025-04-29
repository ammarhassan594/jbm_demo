from odoo import fields, models, api, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    allowance_request_ids = fields.One2many('allowance.request', 'employee_id')
    count_allowance = fields.Integer('Allowance Count', compute="_get_allowance_count")
    ticket_allowance_created = fields.Boolean(default=False)
    furniture_allowance_created = fields.Boolean(default=False)

    def _get_allowance_count(self):
        for rec in self:
            if rec.allowance_request_ids:
                rec.count_allowance = len(rec.allowance_request_ids)
            else:
                rec.count_allowance = 0

    def _employee_auto_create_leave_allowance(self, cron_date, leave_allowance_type):
        leave_allowance = self.env['allowance.request'].create({
            'employee_id': self.id,
            'allowance_type': leave_allowance_type.id,
            'date': cron_date,
            'payment_date': cron_date,
            'automatic_leave_allowance': True,
        })
        leave_allowance._get_eligible_amount()
        leave_allowance.action_confirm()
        leave_allowance.action_first_approve()
        leave_allowance.action_first_approve()
        leave_allowance.action_approve()
        return True
