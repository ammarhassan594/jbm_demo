from odoo import api, fields, models, _


class EbsPassportDetails(models.Model):
    _name = 'ebs.passport.details'
    _description = 'EBS Passport Details'

    employee_id = fields.Many2one('hr.employee', required=1)
    passport_serial_no_id = fields.Many2one('documents.document', string="Passport Serial Number", required=1)
    place_issue = fields.Char("Place of Issue", required=1)
    place_birth = fields.Char("Place of Birth", required=1)
    country_passport_id = fields.Many2one('res.country', string="Country of Passport", required=1)
    citizenship_id = fields.Many2one('res.country', string="Citizenship", required=1)
    double_citizenship_ids = fields.Many2many('res.country', string="Double Country Citizenship")
    passport_type = fields.Selection(
        [('regular', 'Regular'), ('special', 'Special'), ('diplomatic', 'Diplomatic'), ('service', 'Service')],
        string="Passport Type", required=1)

    passport_name = fields.Char("Passport Name", readonly=1)
    first_name = fields.Char("First Name")
    middle_name = fields.Char("Middle Name")
    last_name_1 = fields.Char("Last Name 1")
    last_name_2 = fields.Char("Last Name 2")
    father_name = fields.Char("Father Name")
