from odoo import models, fields, api, _


class Contract(models.Model):
    _inherit = "hr.contract"

    airport_id = fields.Many2one(comodel_name="world.airport", groups="hr.group_hr_user",
                                 string="Airport")
