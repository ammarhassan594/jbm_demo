from odoo import api, fields, models


class ebsResidencypermit(models.Model):
    _name = 'ebs.residency.permit'
    _description = 'EBS Residency Permit'
    _rec_name = 'occupation'

    partner_id = fields.Many2one('res.partner', string="Dependendt")
    residency_id = fields.Many2one('documents.document', string="File")
    occupation = fields.Char("Occupation")
    residency_type = fields.Selection([('entry', 'Entry Visas'), ('work', 'Work Residence Permit'), ('id', 'ID Cards'),
                                       ('family', 'Family Residence Visa'), ('exit', 'Exit Permit'),
                                       ('consular', 'Consular Services')],
                                      string="Residency type", default='entry')
    Sponsor_name = fields.Char("Sponsor Name")
    Sponsor_id = fields.Char("Sponsor ID")
    text = fields.Text("Others/Comments")
    visa_residence_permit = fields.Char("Visa/Residence Permit")
    visit_visa = fields.Char("Visit Visa")

    first_name = fields.Char("First Name")
    middle_name = fields.Char("Middle Name")
    last_name_1 = fields.Char("Last Name 1")
    last_name_2 = fields.Char("Last Name 2")
    father_name = fields.Char("Father Name")
    passport_no = fields.Char("Passport No")

    qid_ref_no = fields.Char("QID Reference Number")
    expiry_date = fields.Date("Expiry Date")

    @api.onchange('residency_id')
    def onchange_residency_id(self):
        for rec in self:
            if not rec.residency_id:
                rec.qid_ref_no = False
                rec.expiry_date = False
                rec.residency_type = False
                rec.Sponsor_id = False
                document_type = self.env['ebs.document.type'].search([('meta_data_template', '=', 'QID')])
                return {
                    'domain': {
                        'residency_id': [('document_type_id', '=', document_type.id)]
                    }
                }
            if rec.residency_id:
                rec.qid_ref_no = rec.residency_id.document_number
                rec.expiry_date = rec.residency_id.expiry_date
                rec.residency_type = rec.residency_id.residency_type
                rec.Sponsor_name = rec.residency_id.sponsor_name

