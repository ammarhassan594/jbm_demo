from odoo import models, fields, api, _


class HREmployeeCustom(models.Model):
    _name = 'profession.profession'
    _rec_name = 'eng_name'

    _sql_constraints = [
        ("unique_eng_name", "UNIQUE(eng_name)", "Already Exists.")]

    eng_name = fields.Char(string="English Name", required=True)
    arabic_name = fields.Char(string="Arabic Name", required=True)


