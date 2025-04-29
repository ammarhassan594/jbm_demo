from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BonusConfiguration(models.Model):
    _name = 'bonus.configuration'

    number_of_days_from = fields.Integer(required=True)
    number_of_days_to = fields.Integer(required=True)
    bonus_month = fields.Selection([
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
    ], string='Month of Bonus', required=True)
    percentage = fields.Float(string="Percentage of Basic Salary")
    amount = fields.Float(string="Amount")
    bonus_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount')
    ], required=True)

    allowed_for = fields.Selection([
        ('qatari', 'Qatari'),
        ('not_qatari', 'Not Qatari'),
        ('both', 'Both')
    ], required=True)

    @api.constrains('number_of_days_from', 'number_of_days_to', 'bonus_type', 'percentage', 'amount')
    def _action_validate_number_days(self):
        for record in self:
            if not record.number_of_days_from > 0 or not record.number_of_days_to > 0:
                raise ValidationError('Number Of Days Must Be Not Equal 0!')
            if not record.number_of_days_from < record.number_of_days_to:
                raise ValidationError('Number of Days From must be less than Number of Days To!')
            if record.bonus_type == 'percentage' and record.percentage == 0.0:
                raise ValidationError('Percentage Must be not equal 0.0%')
            if record.bonus_type == 'fixed_amount' and record.amount <= 0.0:
                raise ValidationError('Amount Must be not equal 0!')