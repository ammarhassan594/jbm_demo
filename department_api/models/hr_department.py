from odoo import models, fields, api, _


class InheritHrDepartment(models.Model):
    _inherit = 'hr.department'
    sort_priority = fields.Integer(string="Sort Priority")
