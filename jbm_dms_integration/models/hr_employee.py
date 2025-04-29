from odoo import fields, models, api


class DmsHrEmployee(models.Model):
    _name = 'hr.employee'
    _inherit = ['hr.employee', 'dms.integration.mix']


