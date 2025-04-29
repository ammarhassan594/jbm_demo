from odoo import models, fields, api

class InheritHrEmployee(models.Model):
    _inherit = 'hr.employee'

    collaborator = fields.Boolean(string="Collaborator")