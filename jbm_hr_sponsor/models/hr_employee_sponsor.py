from odoo import models, fields, api, _


class HrEmployeeSponsor(models.Model):
    _name = 'hr.employee.sponsor'

    name = fields.Char(string="Name", required=True)
    payer_bank_short_name = fields.Char(string="Payer Bank Short Name", required=True)
    payer_iban = fields.Char(string="Payer IBAN", required=True)
    payer_qid = fields.Char(string="Payer QID")
    employer_eid = fields.Char(string="Employer EID", required=True)
    payer_eid = fields.Char(string="Payer EID", required=True)
