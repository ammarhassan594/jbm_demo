from odoo import api, fields, models, _


class EbsInsurance(models.Model):
    _name = 'ebs.insurance'
    _description = 'EBS Insurance'
    _rec_name = 'name_insurer'

    employee_id = fields.Many2one('hr.employee', required=1)
    name_insurer = fields.Char("Name of the Insurer", required=1)
    provider = fields.Char("Provider", required=1)
    type_insurance = fields.Selection(
        [('car', 'Motor (Car)'), ('medical', 'Medical'), ('life_insurance', 'Life Insurance'),
         ('building', 'Building'), ('assets', 'Assets'),
         ('general', 'General'), ('workplace compensation', 'Workplace Compensation')], string="Type of Insurance",
        required=1)
    insurance_covered = fields.Char("Insurance Covered for", required=1)
    issue_date = fields.Date("Issue Date", required=1)
    valid_till = fields.Date("Valid Till", required=1)
    exceptions = fields.Char("Exceptions", required=1)
    text = fields.Text("Others/Comments")
    policy_no = fields.Char('Policy Number', required=1)
