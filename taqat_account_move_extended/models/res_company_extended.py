from odoo import models, fields, api, _


class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    analytic_account_id = fields.Many2one('account.analytic.account', "Analytic Account")
