from odoo import models, fields, api, _


class HrEmployeeSponsor(models.Model):
    _name = 'hr.employee.sponsor'

    name = fields.Char(string="Name", default="", required=True)
    payer_bank_short_name = fields.Char(string="Payer Bank Short Name", default="", required=True)
    payer_iban = fields.Char(string="Payer IBAN", default="", required=True)
    payer_qid = fields.Char(string="Payer QID", default="", required=True)
    payer_eid = fields.Char(string="Payer EID", default="", required=True)
    is_sponsor_by_wassef = fields.Boolean("Sponsor By Wassef")
    # emp_ids = fields.One2many(comodel_name="hr.employee", inverse_name="sponsor", string="", required=False, )