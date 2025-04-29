from odoo import models, fields, api, _

class EmployeeCertificate(models.Model):
    _name = 'employee.certificate'
    
    name = fields.Char("Certificate Name", required=True)
    arabic_name = fields.Char("Certificate Name in Arabic")
    university_name = fields.Char("University Name")
    university_name_in_arabic = fields.Char("University Name in Arabic")
    graduation_year = fields.Char("Graduation Year", required=True)
    employee_id = fields.Many2one("hr.employee")
    qualification_type = fields.Selection(
        [('bachelors', 'Bachelors'), ('high_diploma', 'High Diploma'), ('diploma', 'Diploma'),
         ('high_school', 'High School'), ('intermediate_school', 'Intermediate School'), ('masters', 'Masters')])