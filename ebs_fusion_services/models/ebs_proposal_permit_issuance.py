from odoo import api, fields, models, _

class ebsProposalPermitIssuance(models.Model):
    _name = 'ebs.proposal.permit.issuance'
    _description = 'Work Permit Issuance'

    lead_id = fields.Many2one('crm.lead', string='Deal')
    contract_id = fields.Many2one('ebs.crm.proposal', string='Contract')
    issuance_fees = fields.Char(string='Issuance Fees')
    amount = fields.Float(string='Amount')
