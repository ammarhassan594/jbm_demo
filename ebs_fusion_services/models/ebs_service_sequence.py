from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime

class ebsSequence(models.Model):
    _inherit = 'ir.sequence'

    service_id = fields.Many2one('ebs.crm.service','Service')


