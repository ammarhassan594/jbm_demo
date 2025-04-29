from odoo import api, fields, models, _


class OvertimeRate(models.Model):
    _name = "overtime.rate"
    _description = "Overtime Rate"

    type = fields.Selection(string="Type", default="", selection=[('normal', 'Normal Overtime'), ('special', 'Special Overtime'), ],
                            required=True, )

    rate = fields.Float(string="Rate", default=1)
