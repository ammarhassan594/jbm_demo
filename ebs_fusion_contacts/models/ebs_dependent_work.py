from odoo import api, fields, models, _

class EbsDependentWork(models.Model):
    _name = 'ebs.dependent.work'
    _description = 'EBS Dependent Work'

    partner_id = fields.Many2one('res.partner')
    family_detail_id = fields.Many2one("ebs.family.details",string='Name',required=1)
    dependent_id = fields.Many2one('documents.document',string="Dependent ID No")
    work_permit_id = fields.Many2one('documents.document',string="Work Permit No")
    company_phone = fields.Char("Company Phone")
    working_address = fields.Text("Working Address")
    text = fields.Text("Others/Comments")

    first_name = fields.Char("First Name")
    middle_name = fields.Char("Middle Name")
    last_name_1 = fields.Char("Last Name 1")
    last_name_2 = fields.Char("Last Name 2")
    father_name = fields.Char("Father Name")
    passport_no = fields.Char("Passport No")

