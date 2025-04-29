from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AllowanceType(models.Model):
    _name = "allowance.type"
    _description = "Selection many2one field in allowance request"

    _sql_constraints = [
        ('code_u_code', 'unique (u_code)', "Code Already exists !"),
    ]

    name = fields.Char(string='Name', readonly=False)
    code = fields.Char(string='Code', readonly=True)
    num_of_months = fields.Integer(string='Number Of Months', required=False)
    paid_seperator = fields.Boolean("Paid Separator", default=True)
    u_code = fields.Char(string="Purpose Code")
    sponsor_ids = fields.Many2many(comodel_name="hr.employee.sponsor", string="Sponsorship", )
    enable_payslip = fields.Boolean(string="Enable In Payslip")

    age_from = fields.Float(string="Age From")
    age_to = fields.Float(string="Age To")
    month = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ], string='Month')
    total_days_in_year = fields.Integer(string="Total Days In Year", default=365)
    # number_of_dependent = fields.Integer(string="Number.Dependents", default=0)
    adult_fare_age_from = fields.Integer(string="Adult fare age from", default=1)
    adult_fare_age_to = fields.Integer(string="Adult fare age to", default=1)
    child_fare_age_from = fields.Integer(string="Child fare age from", default=1)
    child_fare_age_to = fields.Integer(string="Child fare age to", default=1)
    infant_fare_age_from = fields.Integer(string="Infant fare age from", default=1)
    infant_fare_age_to = fields.Integer(string="Infant fare age to", default=1)

    @api.constrains('total_days_in_year')
    def _check_total_days_in_year(self):
        for record in self:
            if record.code == 'leave' and record.total_days_in_year < 1:
                raise ValidationError(_('Total days in year must be greater than 1'))

    @api.constrains('adult_fare_age_from', 'adult_fare_age_to')
    def _check_adult_fare_age(self):
        for record in self:
            if record.code == 'ticket' and record.adult_fare_age_from and record.adult_fare_age_to and \
                    record.adult_fare_age_from >= record.adult_fare_age_to:
                raise ValidationError(_('Adult fare age from must be less than Adult fare age to'))

    @api.constrains('child_fare_age_from', 'child_fare_age_to')
    def _check_child_fare_age(self):
        for record in self:
            if record.code == 'ticket' and record.child_fare_age_from and record.child_fare_age_to and \
                    record.child_fare_age_from >= record.child_fare_age_to:
                raise ValidationError(_('Child fare age from must be less than Child fare age to'))

    @api.constrains('infant_fare_age_from', 'infant_fare_age_to')
    def _check_infant_fare_age(self):
        for record in self:
            if record.code == 'ticket' and record.infant_fare_age_from and record.infant_fare_age_from and \
                    record.infant_fare_age_from >= record.infant_fare_age_to:
                raise ValidationError(_('Infant fare age from must be less than Infant fare age to'))

    @api.constrains('child_fare_age_from', 'infant_fare_age_to')
    def _check_child_infant_fare_age(self):
        for record in self:
            if record.code == 'ticket' and record.child_fare_age_from and record.infant_fare_age_to and \
                    record.infant_fare_age_to > record.child_fare_age_from:
                raise ValidationError(_('Infant fare age to must be less than Child fare age from'))

    @api.constrains('adult_fare_age_from', 'child_fare_age_to')
    def _check_child_adult_fare_age(self):
        for record in self:
            if record.code == 'ticket' and record.adult_fare_age_from and record.child_fare_age_to and \
                    record.child_fare_age_to > record.adult_fare_age_from:
                raise ValidationError(_('Child fare age to must be less than Adult fare age from'))

    @api.constrains('age_from', 'infant_fare_age_from')
    def _check_age_from_infant_fare_age(self):
        for record in self:
            if record.code == 'ticket' and record.age_from and record.infant_fare_age_from and \
                    record.infant_fare_age_from < record.age_from:
                raise ValidationError(_('Infant fare age from must be bigger than Age from'))

    @api.constrains('age_to', 'adult_fare_age_to')
    def _check_age_to_adult_fare_age(self):
        for record in self:
            if record.code == 'ticket' and record.age_to and record.adult_fare_age_to and \
                    record.adult_fare_age_to > record.age_to:
                raise ValidationError(_('Adult fare age to must be less than Age to'))
