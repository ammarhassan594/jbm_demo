from odoo import fields, models, api


class LogNoteWizard(models.TransientModel):
    _name = 'log.note.reject.wizard'
    _description = 'Description'

    reason = fields.Text('Reason', required=True)

    # related_appraisal = fields.Many2one('hr.appraisal', 'Related Appraisal')

    def log_and_reject(self):
        for rec in self:
            record = rec.env[rec._context.get('active_model')].browse(rec._context.get('active_ids'))
            if record:
                record.reject_reason = rec.reason
                record.state_reject()
