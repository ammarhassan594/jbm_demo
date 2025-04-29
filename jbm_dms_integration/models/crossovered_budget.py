from odoo import models


class DmsCrossOveredBudget(models.Model):
    _name = 'crossovered.budget'
    _inherit = ['crossovered.budget', 'dms.integration.mix']
