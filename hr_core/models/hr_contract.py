from odoo import fields, models, api


class Contract(models.Model):
    _inherit = 'hr.contract'

    related_compensation = fields.One2many('hr.compensation', 'related_contract', string='Related Compensation',
                                           domain=[('state', '=', 'active')])
