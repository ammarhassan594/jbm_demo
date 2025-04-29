from odoo import api, fields, models, _


class ebsContactIndustries(models.Model):
    _name = 'ebs.contact.industries'
    _description = 'EBS Contact Industries'
    _rec_name = 'industry_id'

    industry_id = fields.Many2one('res.partner.industry', string="Industry")
    budget = fields.Float("Budget")
    deal_sum = fields.Float("Deal Sum", compute='_compute_deal_sum')
    remain_budget = fields.Float("Remaing Budget", compute='_compute_remaining_budget')
    partner_id = fields.Many2one("res.partner")

    @api.depends("industry_id")
    def _compute_deal_sum(self):
        for rec in self:
            deal_sum = 0.00
            for deal in self.env['crm.lead'].search([('industry_id', '=', rec.industry_id.id)]):
                deal_sum += deal.expected_revenue
            rec.deal_sum = deal_sum

    @api.depends("industry_id", "deal_sum", "budget")
    def _compute_remaining_budget(self):
        for rec in self:
            rec.remain_budget = rec.budget - rec.deal_sum
