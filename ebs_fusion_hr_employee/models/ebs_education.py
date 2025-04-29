from odoo import api, fields, models, _


class EbsEducation(models.Model):
    _name = 'ebs.education'
    _description = 'EBS Education'
    _rec_name = 'education_type_id'

    employee_id = fields.Many2one('hr.employee')

    certificates_id = fields.Many2one('documents.document', string="Certificate")
    year_passing = fields.Date("Year of Passing (Date of Issue)")
    university_institute = fields.Char("University/Institute")
    grade = fields.Char("Grade")
    attested_education_certificate_id = fields.Many2one('documents.document', string="Attested Education Certificate")
    training_certificate_id = fields.Many2one('documents.document', string="Training Certificate")
    no_certificate = fields.Integer(string="No. of Certificates")
    education_spatial_environment = fields.Char(string="Education and Spatial Environment")
    nortarized_certificate_id = fields.Many2one('documents.document', string="Notarized qualification certificate")
    qualification_employees_staff = fields.Char("Qualification of Employees and Staff")

    candidate_transcript = fields.Many2one('documents.document', string="Candidate(s) Transcript")
    candidate_university_letter_id = fields.Many2one('documents.document', string="Candidate's University Letter")
    text = fields.Text("Others/Comments")

    education_type_id = fields.Many2one('education.type', string="Education type")
    certificate_type_id = fields.Many2one('certificate.type', string="Certificates Type")
    education_certificate_id = fields.Many2one('documents.document', string="Education Certificate")

    @api.onchange('certificates_id')
    def onchange_certificates_id(self):
        for rec in self:
            if not rec.certificates_id:
                rec.year_passing = False
                rec.university_institute = False

                return {
                    'domain': {
                        'certificates_id': [('document_type_name', '=', 'Education Certificates')]
                    }
                }
            if rec.certificates_id:
                rec.university_institute = rec.certificates_id.university
                rec.year_passing = rec.certificates_id.year_of_graduation


class EducationType(models.Model):
    _name = 'education.type'
    _description = 'Education Type'

    name = fields.Char(string="Name")


class CertificateType(models.Model):
    _name = 'certificate.type'
    _description = 'Certification Type'

    name = fields.Char(string="Name")
