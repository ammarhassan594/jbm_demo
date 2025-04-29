from odoo import api, fields, models, _

class HrEmployeeCustom(models.Model):
    _inherit = 'hr.employee'

    arrival_date = fields.Date('Arrival Date')
    cancelled_date = fields.Date('Cancelled Date')

