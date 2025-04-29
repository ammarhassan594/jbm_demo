from odoo import api, fields, models, _


class EbsFamilyDetails(models.Model):
    _name = 'ebs.family.details'
    _description = 'EBS Family Details'
    _rec_name = 'relation_with_dependent'

    employee_id = fields.Many2one('hr.employee')
    partner_id = fields.Many2one('res.partner')
    relation_with_dependent = fields.Selection([('Wife','Wife'),('Child','Child')],string='Relation with Dependant',default='Wife')
    first_name = fields.Char("First Name",required=1)
    middel_name = fields.Char("Middle Name",required=1)
    last_name = fields.Char("Last Name",required=1)
    dob = fields.Date("Date of Birth")
    nationality_id = fields.Many2one('res.country', string='Nationality')
    home_number = fields.Char(string='Home Number')
    mobile_number = fields.Char(string='Mobile Number')
    alt_mobile_number = fields.Char(string='Alternate Mobile Number')
    emergency_no = fields.Char(string='Emergency Contact number')
    company_email = fields.Char(string='Company Email address')
    personal_email = fields.Char(string='Personal Email Address')
    permanent_address = fields.Text("Permanent Address")
    current_address = fields.Text("Current Address")

    blood_group = fields.Selection([('a+','A+'),('o+','O+'),('b+','B+'),('ab+','AB+'),
                                    ('a-','A-'),('o-','O-'),('b-','B-'),('ab-','AB-')],"Blood Group")
    passport_id = fields.Many2one('documents.document', string="Passport Serial Number")
    place_issue = fields.Char("Place of Issue")
    place_birth = fields.Char("Place of Birth")
    country_passport_id = fields.Many2one('res.country', string="Country Of Passport")
    citizenship_id = fields.Many2one('res.country', string="Citizenship")
    double_citizenship_ids = fields.Many2many('res.country', string="Double Country Citizenship")
    passport_type = fields.Selection([('regular','Regular'),('special','Special'),('diplomatic','Diplomatic'),('service','Service')],string="Passport Type")
    profession_id = fields.Many2one('hr.job',string="Profession")
    work_status = fields.Char("Work Status")
    text = fields.Text("Others/Comments")