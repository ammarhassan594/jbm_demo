from datetime import datetime
from dateutil.relativedelta import relativedelta


from odoo import models, fields, api, _

class InheritHrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def get_yearly_bonus(self, payslip, employee):
        number_of_worked_days = 0
        bonus_amount = 0.0
        current_date = payslip.date_to
        bonus_configuration = self.env['bonus.configuration'].search([
            ('bonus_month', '=', current_date.month)
        ])
        if bonus_configuration:
            nationality = employee.country_id.code if employee.country_id else False
            if nationality:
                if nationality == 'QA':
                    bonus_configuration = bonus_configuration.filtered(lambda config: config.allowed_for == 'qatari' or config.allowed_for == 'both')
                else:
                    bonus_configuration = bonus_configuration.filtered(
                        lambda config: config.allowed_for == 'not_qatari' or config.allowed_for == 'both')
                joining_date = employee.joining_date if employee.joining_date else False
                # current_date = datetime.now().date()
                if joining_date:
                    delta = current_date - joining_date
                    number_of_worked_days = delta.days
                    if number_of_worked_days > 0:
                        bonus_configuration = bonus_configuration.filtered(lambda config: config.number_of_days_from <= number_of_worked_days <= config.number_of_days_to )
                        if bonus_configuration:
                            if bonus_configuration.bonus_type == 'percentage' and bonus_configuration.percentage:
                                bonus_amount = payslip.contract_id.wage * bonus_configuration.percentage
                            elif bonus_configuration.bonus_type == 'fixed_amount' and bonus_configuration.amount:
                                bonus_amount = bonus_configuration.amount
        return bonus_amount