from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PermissionConfig(models.Model):
    _name = 'permission.config'

    permission_leave_type = fields.Selection([
        ('site_permission', 'Site Permission'),
        ('business_permission', 'Business Permission'),
        ('personal_permission', 'Personal Permission')], string='Permission Type', required=True)
    is_attendance = fields.Boolean(string="Attendance")
    max_hours = fields.Float(string="Max Hours", default=0)
    leave_type_id = fields.Many2one(comodel_name="hr.leave.type")


