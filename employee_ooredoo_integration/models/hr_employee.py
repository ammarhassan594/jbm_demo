from odoo import models, fields, api, _

class InheritHrEmployee(models.Model):
    _name = 'hr.employee'
    _inherit = ['hr.employee', 'dynamic.integration.mix']