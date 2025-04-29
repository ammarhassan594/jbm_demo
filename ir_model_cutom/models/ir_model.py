from odoo import models, fields

class InheritModel(models.Model):

    _inherit = 'ir.model'

    send_activity_mail = fields.Boolean(string="Send Email Activity")
    field_name = fields.Many2one('ir.model.fields')
    field_type = fields.Many2one('ir.model.fields')

