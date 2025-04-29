from odoo import models, fields, api, _


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    dashboard_id = fields.Char(string="Dashboard ID", help="This is the id of the dashboard API", groups="base.group_erp_manager")
