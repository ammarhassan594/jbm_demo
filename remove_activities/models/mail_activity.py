from odoo import models, fields, api, _

class InheritMailActivity(models.Model):
    _inherit = 'mail.activity'


    @api.model
    def remove_all_activities(self):
        activities = self.env['mail.activity'].sudo().search([])
        activities.unlink()