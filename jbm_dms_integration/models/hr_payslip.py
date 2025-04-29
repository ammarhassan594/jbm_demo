from odoo import fields, models, api


class DmsHrPayslip(models.Model):
    _name = 'hr.payslip'

    _inherit = ['hr.payslip', 'dms.integration.mix']
