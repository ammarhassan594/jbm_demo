from odoo import models, fields, api, _

class InheritResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    bonus_month = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ], string='Month of Bonus')

    @api.model
    def get_values(self):
        res = super(InheritResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        bonus_month = params.get_param('bonus_month')
        res.update(
            bonus_month=bonus_month,
        )
        return res


    def set_values(self):
        super(InheritResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("bonus_month", self.bonus_month)