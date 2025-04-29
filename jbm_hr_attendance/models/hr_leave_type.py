from odoo import api, fields, models, _


class Leave(models.Model):
    _inherit = 'hr.leave.type'

    days_based_on = fields.Selection(
        string='Days Based On', default='working_days' ,selection=[('calendar_days', 'Calendar Days'),
                                                                  ('working_days', 'Working Days') ,])
