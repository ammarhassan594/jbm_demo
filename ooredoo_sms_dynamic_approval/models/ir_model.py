from odoo import models, fields, api, _

class InheritIrModel(models.Model):
    _inherit = 'ir.model'

    sms_receiver_id = fields.Many2one('ir.model.fields', string="SMS Receiver")