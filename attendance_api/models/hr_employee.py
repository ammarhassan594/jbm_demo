from odoo import models, fields, api, _


class HrEmployeeCustom(models.Model):
    _inherit = 'hr.employee'

    punch_user_id = fields.Char(string="Punch User ID")

