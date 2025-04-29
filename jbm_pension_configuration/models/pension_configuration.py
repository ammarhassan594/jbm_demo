from odoo import api, fields, models, _


class PensionConfig(models.Model):
    _name = "pension.config"
    _description = "Pension Configuration"
    _rec_name = "country_id"

    country_id = fields.Many2one(comodel_name="res.country", string="Country")

    employee_basic = fields.Float(string="Employee Basic %", default=0.0)
    employee_basic_limit = fields.Float(string="limit", default=0.0)
    employee_social = fields.Float(string="Employee Social %", default=0.0)
    employee_social_limit = fields.Float(string="limit", default=0.0)
    employee_housing = fields.Float(string="Employee Housing %", default=0.0)
    employee_housing_limit = fields.Float(string="limit", default=0.0)
    employee_transport = fields.Float(string="Employee Transport %", default=0.0)
    employee_transport_limit = fields.Float(string="limit", default=0.0)
    employee_mobile = fields.Float(string="Employee Mobile %", default=0.0)
    employee_mobile_limit = fields.Float(string="limit", default=0.0)
    employer_basic = fields.Float(string="Employer Basic %", default=0.0)
    employer_basic_limit = fields.Float(string="limit", default=0.0)
    employer_social = fields.Float(string="Employer Social %", default=0.0)
    employer_social_limit = fields.Float(string="limit", default=0.0)
    employer_housing = fields.Float(string="Employee Housing %", default=0.0)
    employer_housing_limit = fields.Float(string="limit", default=0.0)
    employer_transport = fields.Float(string="Employee Transport %", default=0.0)
    employer_transport_limit = fields.Float(string="limit", default=0.0)
    employer_mobile = fields.Float(string="Employee Mobile %", default=0.0)
    employer_mobile_limit = fields.Float(string="limit", default=0.0)
    employee_max_limit = fields.Float(string="Employee Max Limit", default=0.0)
    applied_on_date = fields.Date(string="Applied on Date: ")
    code = fields.Char(related="country_id.code", string="Code")

    _sql_constraints = [
        ('country_unique', 'unique (country_id)', 'Country must be unique')
    ]
