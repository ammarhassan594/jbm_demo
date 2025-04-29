from odoo import api, fields, models, _


class LabourQuotaDetails(models.Model):
    _name = 'labour.quota.details'
    _description = 'Labour Quota Details'

    application_no = fields.Char(string='Application No.')
    vp_no = fields.Char(string='VP number')
    application_date = fields.Date(string='Application Date')
    expiry_date = fields.Date(string='Expiry Date')
    renewal_reminder = fields.Boolean(string='Renewal Reminder')
    attachment_id = fields.Many2one('documents.document', string="Attachment", required=True)
    partner_id = fields.Many2one('res.partner')

    nationality_id = fields.Many2one('res.country', string="Nationality")
    job_id = fields.Many2one('hr.job', string="Job Title")
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),

    ], default="male", string="Gender")
    no = fields.Char("No")
    quantity = fields.Char('QTY')
    moi_ref = fields.Char("MOI Ref#")



class QCSingleWindowFacility(models.Model):
    _name = 'qc.single.window.facility'
    _description = 'QC Window Facility'

    appointed_agent = fields.Many2one('res.partner',string='Appointed Agent')
    expiry_date = fields.Date(string='Expiry Date')
    renewal_reminder = fields.Boolean(string='Renewal Reminder')
    attachment_id = fields.Many2one('documents.document', string="Attachment", required=True)
    partner_id = fields.Many2one('res.partner')