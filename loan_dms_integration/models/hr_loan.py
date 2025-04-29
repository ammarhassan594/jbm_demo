from odoo import models


class Loans(models.Model):
    _name = 'hr.loan'
    _inherit = ['hr.loan', 'dms.integration.mix']
