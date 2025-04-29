from odoo import api, fields, models, _


class ebsResidencypermit(models.Model):
    _name = 'ebs.residency.permit'
    _description = 'EBS Residency Permit'
    _rec_name = 'occupation'

    employee_id = fields.Many2one('hr.employee', required=1)
    residency_id = fields.Many2one('documents.document', string="Residency Id Number", required=1)
    occupation = fields.Char("Occupation", required=1)
    residency_type = fields.Selection([('entry', 'Entry Visas'), ('work', 'Work Residence Permit'), ('id', 'ID Cards'),
                                       ('family', 'Family Residence Visa'), ('exit', 'Exit Permit'),
                                       ('consular', 'Consular Services')],
                                      string="Residency type", required=1, default='entry')
    Sponsor_name = fields.Char("Sponsor Name", required=1)
    Sponsor_id = fields.Char("Sponsor ID", required=1)
    text = fields.Text("Others/Comments")
    visa_residence_permit = fields.Char("Visa/Residence Permit", required=1)
    visit_visa = fields.Char("Visit Visa", required=1)

    first_name = fields.Char("First Name")
    middle_name = fields.Char("Middle Name")
    last_name_1 = fields.Char("Last Name 1")
    last_name_2 = fields.Char("Last Name 2")
    father_name = fields.Char("Father Name")
    passport_no = fields.Char("Passport No")
