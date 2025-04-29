from odoo import api, fields, models, _


class EbsWorkmenCompensation(models.Model):
    _name = 'ebs.workmen.compensation'
    _description = 'EBS Workmen Compensation'

    policy_number = fields.Char(string='Policy Number')
    employee_id = fields.Many2one('hr.employee', string='Name of the Insurance Client')
    company_id = fields.Many2one('res.company', related='employee_id.company_id', store=True)
    list_of_beneficiary = fields.Text(string='List of Beneficiary')
    currency_id = fields.Many2one(related='company_id.currency_id', store=True)
    value = fields.Monetary(string='Value', currency_field='currency_id')
    file = fields.Many2one('documents.document', string='File')
