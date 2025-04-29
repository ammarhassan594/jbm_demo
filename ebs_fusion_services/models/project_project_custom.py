from odoo import api, fields, models, _

class ProjectCustom(models.Model):
    _inherit = 'project.project'

    for_services = fields.Boolean('For Services')
