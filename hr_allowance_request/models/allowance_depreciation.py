from odoo import fields, models, api


class AllowanceDepreciation(models.Model):
    _name = 'allowance.depreciation'
    _description = 'lines depends on eligible amount and number of months in allowance type '

    date = fields.Date( string='Date', required=False)
    amount = fields.Monetary(string='Amount')
    allowance_id = fields.Many2one('allowance.request', string='Allowance_id', required=False)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, help="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id)