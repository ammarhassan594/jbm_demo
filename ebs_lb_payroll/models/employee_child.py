# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date, datetime


def get_year():
    current_year = datetime.now().year
    if datetime.now().month > 6:
        return current_year + 1
    else:
        return current_year


class EmployeeChild(models.Model):
    _name = 'hr.emp.child'
    _description = 'Employee Child'

    name = fields.Char(
        string='Name',
        required=True)

    date_of_birth = fields.Date(
        string='Date of Birth',
        required=False)

    is_student = fields.Boolean(
        string='Is Student',
        required=False, default=False)

    emp_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=False)
    relation = fields.Selection(string="Relation", selection=[('spouse', 'Spouse'), ('child', 'Child')], default='child'
                                , required=False)
    qid = fields.Char(
        string='QID')
    passport_number = fields.Char(
        string='Passport Number')
    passport_issue_date = fields.Date(
        string='Passport Issue Date')
    passport_issue_place = fields.Char(
        string='Passport Issue Place')
    hamad_card_number = fields.Char("Hamad Card Number")
    Hamad_card_expiry_date = fields.Date("Hamad Card Expiry Date")
    Passport_expiry_date = fields.Date("Passport Expiry Date")
    insurance_details = fields.Char("Insurance Details")
    school_name = fields.Char()
    age = fields.Float(compute='_get_age', store=False)
    QID_expiry_date = fields.Date("QID Expiry Date")
    QID_attachment = fields.Binary("QID Attachment")

    @api.depends('date_of_birth')
    def _get_age(self):
        for rec in self:
            if rec.date_of_birth:
                date_jun = datetime(get_year(), 6, 30, 0, 0, 0).date()
                age_cust = (date_jun - rec.date_of_birth).days / 365
                rec.age = age_cust
            else:
                rec.age = 99
