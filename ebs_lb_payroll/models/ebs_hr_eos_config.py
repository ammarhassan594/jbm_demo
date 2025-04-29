from odoo import models, fields


class EosConfig(models.Model):
    _name = 'ebs.hr.eos.config'
    _description = 'Ebs Hr Eos Config'

    name = fields.Char('Name')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    working_days = fields.Integer('Working days', default=21)
    salary_days = fields.Integer('Salary days')
    paid_leaves_ids = fields.Many2many('hr.leave.type', string='Paid Leaves', domain="[('is_unpaid','=',False)]")
    unpaid_leave_account_id = fields.Many2one('account.account', 'Unpaid Leave Account')
    paid_leave_account_id = fields.Many2one('account.account', 'Paid Leave Account')
    closing_account_id = fields.Many2one('account.account', 'Closing Account')
    gratuity_account_id = fields.Many2one('account.account', 'Gratuity Account')
    entitlements_types_ids = fields.Many2many('ebs.hr.eos.other.entitlements.types','eos_config_entitlements_types', string='Entitlements types')
    notice_period_ids = fields.One2many('ebs.eos.notice.period','eos_config_id', string='Notice Periods')
    eligible_after_years = fields.Float(string='Eligible After in years', default=1.0)


