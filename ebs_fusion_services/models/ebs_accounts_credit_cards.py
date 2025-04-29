from odoo import api, fields, models, _


class ebsAccountCreditCards(models.Model):
    _name = 'ebs.accounts.credit.cards'
    _description = 'EBS Account Credit Cards'

    name = fields.Char(string='Name', required=True)
    account_id = fields.Many2one(comodel_name='account.account', string='Account', required=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company')
    journal_id = fields.Many2one(comodel_name='account.journal', string='Journal', required=True)
