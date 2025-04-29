from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    fusion_employee_receivable = fields.Many2one('account.account', string="Main Company Employee Receivable", )
    fusion_employee_payable = fields.Many2one('account.account', string="Main Company Employee Payable")
    outsourced_employee_receivable = fields.Many2one('account.account', string="Outsourced Employee Receivable")
    outsourced_employee_payable = fields.Many2one('account.account', string="Outsourced Employee Payable")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def set_current_company(self):
        return [('company_id', '=', self.env.company.id)]

    fusion_employee_receivable = fields.Many2one('account.account', string="Main Company Employee Receivable",
                                                 related='company_id.fusion_employee_receivable', readonly=False,
                                                 domain=set_current_company)
    fusion_employee_payable = fields.Many2one('account.account', string="Main Company Employee Payable",
                                              related='company_id.fusion_employee_payable', readonly=False,
                                              domain=set_current_company)
    outsourced_employee_receivable = fields.Many2one('account.account', string="Outsourced Employee Receivable",
                                                     related='company_id.outsourced_employee_receivable',
                                                     readonly=False, domain=set_current_company)
    outsourced_employee_payable = fields.Many2one('account.account', string="Outsourced Employee Payable",
                                                  related='company_id.outsourced_employee_payable', readonly=False,
                                                  domain=set_current_company)
