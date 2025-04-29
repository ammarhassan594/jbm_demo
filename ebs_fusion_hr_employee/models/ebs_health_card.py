from odoo import api, fields, models, _


class EbsHealthCard(models.Model):
    _name = 'ebs.health.card'
    _description = 'EBS Health Card'
    _rec_name = 'name'

    employee_id = fields.Many2one('hr.employee')
    name = fields.Char("Name", required=1)
    nationality_id = fields.Many2one('res.country', string="Nationality")
    passport_serial_no_id = fields.Many2one('documents.document', string="Passport Serial Number")
    qid_serial_no_id = fields.Many2one('documents.document', string="QID Serial Number")
    hc_serial_no_id = fields.Many2one('documents.document', string="HC Serial Number")
    text = fields.Text("Others/Comments")
