from odoo import api, fields, models, _

class ebsProposalSalaryStructure(models.Model):
    _name = 'ebs.proposal.salary.structure'
    _description = 'Monthly Salary Breakdown'

    lead_id = fields.Many2one('crm.lead', string='Deal')
    contract_id = fields.Many2one('ebs.crm.proposal', string='Contract')
    annual_salary = fields.Float(string='Annual Salary')
    monthly_salary = fields.Float(string='Monthly Salary')
    monthly_gross = fields.Float(string='Basic Salary')
    housing_allowance = fields.Float(string='Housing Allowance')
    transportation_allowance = fields.Float(string='Transportation Allowance')
    eos_gratuity = fields.Float(string='End Of Service Gratuity', compute='compute_eos_amount')
    eos_monthly_fee = fields.Float(string='End Of Service Monthly Fee', compute='compute_eos_amount')
    other_allowance = fields.Float(string='Other Allowance')

    @api.onchange('housing_allowance','transportation_allowance', 'eos_gratuity', 'other_allowance','monthly_gross','eos_monthly_fee')
    def cal_monthly_salary_onchange(self):
        for rec in self:
            rec.monthly_salary = rec.monthly_gross + rec.housing_allowance + rec.transportation_allowance + rec.other_allowance

    @api.onchange('monthly_salary')
    def onchange_monthly_salary(self):
        for rec in self:
            rec.annual_salary = rec.monthly_salary * 12

    @api.depends('monthly_gross')
    def compute_eos_amount(self):
        for rec in self:
            rec.eos_monthly_fee = rec.monthly_gross * 21 / 30 / 12
            rec.eos_gratuity = rec.monthly_gross * 21 / 30


