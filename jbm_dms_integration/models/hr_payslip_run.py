from odoo import fields, models, api


class DmsHrPayslipRun(models.Model):
    _name = 'hr.payslip.run'

    _inherit = ['hr.payslip.run', 'dms.integration.mix']
