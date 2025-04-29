from odoo import api, fields, models, _


class EbsPassportDetails(models.Model):
    _name = 'ebs.passport.details'
    _description = 'EBS Passport Details'

    employee_id = fields.Many2one('hr.employee')
    partner_id = fields.Many2one('res.partner')
    passport_serial_no_id = fields.Many2one('documents.document',string="File")
    issue_date = fields.Date(string='Date Issued')
    place_issue = fields.Char("Place of Issue")
    place_birth = fields.Char("Place of Birth")
    country_passport_id = fields.Many2one('res.country',string="Country of Passport")
    citizenship_id = fields.Many2one('res.country',string="Citizenship")
    double_citizenship_ids = fields.Many2many('res.country',string="Double Country Citizenship")
    passport_type = fields.Selection([('regular','Regular'),('special','Special'),('diplomatic','Diplomatic'),('service','Service')],string="Passport Type")

    passport_name = fields.Char("Passport Name")
    first_name = fields.Char("First Name")
    middle_name = fields.Char("Middle Name")
    last_name_1 = fields.Char("Last Name 1")
    last_name_2 = fields.Char("Last Name 2")
    father_name = fields.Char("Father Name")

    passport_ref_no = fields.Char("Passport Reference Number")
    expiry_date = fields.Date("Expiry Date")

    @api.onchange('passport_serial_no_id')
    def onchange_passport_serial_no_id(self):
        for rec in self:
            if not rec.passport_serial_no_id:
                rec.issue_date = False
                rec.expiry_date = False
                rec.place_birth = False
                rec.passport_ref_no = False
                rec.citizenship_id = False
                document_type = self.env['ebs.document.type'].search([('name', '=', 'Passport')])
                return {
                    'domain': {
                        'passport_serial_no_id': [('document_type_id', '=', document_type.id)]
                    }
                }
            if rec.passport_serial_no_id:
                rec.issue_date = rec.passport_serial_no_id.issue_date
                rec.expiry_date = rec.passport_serial_no_id.expiry_date
                rec.place_birth = rec.passport_serial_no_id.place_of_birth
                rec.passport_ref_no = rec.passport_serial_no_id.passport_no
                rec.citizenship_id = rec.passport_serial_no_id.nationality.id


