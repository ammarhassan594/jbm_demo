from odoo import models, fields, api, _

class InheritHrAttendnace(models.Model):
    _name = 'hr.attendance'
    _inherit = ['hr.attendance', 'dynamic.integration.mix']