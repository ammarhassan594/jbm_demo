from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class DocumentsCycle(models.Model):
    _name = 'document.cycle'
    _description = 'Document Cycle'

    employee_id = fields.Many2one('hr.employee',string='Name')
    job_id = fields.Many2one('hr.job',string='Job Position',related='employee_id.job_id')
    from_date = fields.Datetime(string='Check-out Date')
    to_date = fields.Datetime(string='Check-in Date')
    signature = fields.Binary(string='Signature')
    notes = fields.Text(string='Notes')
    document_id = fields.Many2one('documents.document')

    @api.constrains('to_date')
    def validate_to_date(self):
        if self.from_date >= self.to_date:
            raise ValidationError('Check-in date must be selected after check-out date.')

