from odoo import api, fields, models, _



class CrmStage(models.Model):
    _inherit = 'crm.stage'

    hubspot_id = fields.Char("Hubspot ID")
    is_lost = fields.Boolean("Is Lost Stage?")
    probability = fields.Float("Probability")
    code = fields.Integer('Code')