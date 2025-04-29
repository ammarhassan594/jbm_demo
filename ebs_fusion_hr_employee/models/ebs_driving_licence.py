from odoo import api, fields, models, _
from datetime import date,datetime


class EbsDrivingLicence(models.Model):
    _name = 'ebs.driving.licence'
    _description = 'EBS Driving Licence'
    _rec_name = 'vehicle_used'

    employee_id = fields.Many2one('hr.employee')

    vehicle_used = fields.Char("Vehicle to be used")
    licence_type = fields.Selection([('international','International'),('local','Local')],string='Licence Type')
    licence_serial_id = fields.Many2one('documents.document', string="Driving Licence Serial Number")
    form_individual_licence = fields.Char(string="Form for Individual licensing")
    text = fields.Text("Others/Comments")

    driving_ref_no = fields.Char("Driving Reference Number")
    expiry_date = fields.Date("Expiry Date")

    @api.onchange('licence_serial_id')
    def onchange_licence_serial_id(self):
        for rec in self:
            rec.expiry_date = rec.licence_serial_id.expiry_date





