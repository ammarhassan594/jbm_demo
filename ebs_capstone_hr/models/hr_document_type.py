from odoo import models, fields, api,_


class DocumentType(models.Model):
    _name = 'ebs.hr.document.type'
    _description = 'Document Type'

    name = fields.Char(string='Name', required=True)
    has_reminder = fields.Boolean(string='Has Reminder')
    days = fields.Integer(string='Reminder Days', default='90')
    template_id = fields.Many2one('mail.template', string='Template')
