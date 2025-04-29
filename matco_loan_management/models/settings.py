# -*- coding: utf-8 -*-
from odoo import models, fields, api,_


class LoanSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    loan_installments = fields.Integer(string="Loan Installments",
                                       config_parameter='matco_loan_management.loan_installments')

    # def set_values(self):
    #     result = super(PayrollHrSettings, self).set_values()
    #     self.env['ir.config_parameter'].set_param('ebs_lb_payroll.cutoff_day', self.cutoff_day)
    #     self.env['ir.config_parameter'].set_param('ebs_lb_payroll.leave_cutoff_day', self.leave_cutoff_day)
    #     self.env['ir.config_parameter'].set_param('ebs_lb_payroll.overtime_cutoff_day', self.overtime_cutoff_day)
    #     # self.env['ir.config_parameter'].set_param('ebs_lb_payroll.ooredoo_template', self.ooredoo_template)
    #     return result
    # 
    # @api.model
    # def get_values(self):
    #     result = super(PayrollHrSettings, self).get_values()
    #     day = int(self.env['ir.config_parameter'].sudo().get_param('ebs_lb_payroll.cutoff_day'))
    #     leave_day = int(self.env['ir.config_parameter'].sudo().get_param('ebs_lb_payroll.leave_cutoff_day'))
    #     overtime_day = int(self.env['ir.config_parameter'].sudo().get_param('ebs_lb_payroll.overtime_cutoff_day'))
    #     # ooredoo_temp = int(self.env['ir.config_parameter'].sudo().get_param('ebs_lb_payroll.ooredoo_template'))
    #     result.update(
    #         cutoff_day=day,
    #         leave_cutoff_day=leave_day,
    #         overtime_cutoff_day=overtime_day,
    #     )
    #     return result


# class ResCompanyCustom(models.Model):
#     _inherit = 'res.company'
#
#     loan_installments = fields.Integer(string="Loan Installments")

