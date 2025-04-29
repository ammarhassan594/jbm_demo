from odoo import api, fields, models, _


class EbsVisaDetails(models.Model):
    _name = 'ebs.visa.details'
    _description = 'EBS Visa Details'
    _rec_name = 'application_no'

    employee_id = fields.Many2one('hr.employee')
    image_1920 = fields.Binary("Passport Photo")
    application_no = fields.Char("Application Number")
    visa_no = fields.Char("Visa Number")
    visa_type = fields.Selection(
        [('work', 'Work'), ('business', 'Business'), ('visit', 'Visit'), ('project', 'Project'), ('other', 'Other')],
        string='Visa Type', default='work')

    visa_serial_no_id = fields.Many2one('documents.document', string="Visa Serial Number")
    certificate_id = fields.Many2one('documents.document', string="Certificate")
    date_entry = fields.Date("Date of Entry")
    after_entry = fields.Date("After Entry")
    visa_valid_till = fields.Date("Visa Valid till")
    profession_id = fields.Many2one('hr.job', string="Profession")
    emp_name = fields.Char("Employers Name")
    main_official_name = fields.Char("Name of the Main Official")
    representative_name = fields.Char("Name and data of the PRO representative")
    manager_id = fields.Many2one('hr.employee', string="Name of the Responsible Manager")
    text = fields.Text("Others/Comments")
    blood_group = fields.Selection([('o-', 'O-'), ('o+', 'O+'), ('a-', 'A-'), ('a+', 'A+'),
                                    ('b-', 'B-'), ('b+', 'B+'), ('ab-', 'AB-'), ('Ab+', 'AB+'), ], string="Blood Group")
    recidency_type = fields.Char(string='Residency type')
    sponsor_name = fields.Char(string='Sponsor Name')
    sponsor_id = fields.Char(string='Sponsor ID')
