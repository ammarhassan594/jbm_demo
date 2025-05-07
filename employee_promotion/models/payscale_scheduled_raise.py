from datetime import date
import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class PayscaleScheduledRaise(models.Model):
    _name = "payscale.scheduled.raise"

    name = fields.Char(string="Description")
    payscale_id = fields.Many2one('employee.payscale', string="Payscale")
    fixed_amount = fields.Float(string="Fixed Amount")
    percentage = fields.Float(string="Percentage")
    start_date = fields.Date(string="Start Date")
    actual_days = fields.Integer(string="Actual Days")
    extra_amount = fields.Float('Extra Amount')

    _sql_constraints = [('uniq_payscale_id',
                         'unique(payscale_id)',
                         'Payscale scheduled raise must be unique per payscale')]

    @api.constrains('percentage', 'fixed_amount')
    def _field_validation(self):
        for record in self:
            if record.percentage < 0 or record.fixed_amount < 0:
                raise ValidationError('Fixed Amount and Percentage cannot be Negative!')
            if record.percentage > 1.0:
                raise ValidationError('Percentage Cannot be more than 100%!')

    @api.onchange('percentage')
    def _change_percentage(self):
        for record in self:
            if record.percentage > 0.0:
                record.fixed_amount = 0.0

    @api.onchange('fixed_amount')
    def _change_amount(self):
        for record in self:
            if record.fixed_amount > 0.0:
                record.percentage = 0.0

    @api.model
    def schedule_payscale_raise(self):
        current_day = date.today()
        payscale_raises = self.env['payscale.scheduled.raise'].search([
            ('start_date', '<=', current_day)
        ])
        if payscale_raises:
            for payscale_raise in payscale_raises:
                contracts = self.env['hr.contract'].search([
                    ('payscale_id', '=', payscale_raise.payscale_id.id),
                    ('state', '=', 'open')
                ])
                basic_max = payscale_raise.payscale_id.basic_to
                if contracts:
                    for contract in contracts:
                        # promotions = self.env['employee.promotion'].search([
                        #     ('payscale_scheduled_raise_id', '=', payscale_raise.id), ('employee_id', '=', contract.employee_id.id)
                        # ])
                        # if promotions:
                        #     continue
                        if contract.employee_id.promotion_ids.filtered(
                                lambda x: x.date_start and x.payscale_scheduled_raise_id):
                            employee_promotions = contract.employee_id.promotion_ids.filtered(
                                lambda x: x.date_start and x.payscale_scheduled_raise_id). \
                                sorted(key=lambda x: x.date_start, reverse=True)
                            _logger.info("Employee Promotions {}".format(employee_promotions))
                            last_promotion = employee_promotions and employee_promotions[0]
                            _logger.info("last_promotion {}".format(last_promotion))
                            today = fields.Date.context_today(contract.employee_id)
                            _logger.info("last_promotion.date_start {}".format(last_promotion.date_start))
                            _logger.info("today {}".format(today))
                            if today < last_promotion.date_start:
                                continue
                            actual_duty = (today - last_promotion.date_start).days + 1
                            _logger.info("actual_duty {}".format(actual_duty))

                            if actual_duty >= payscale_raise.actual_days:
                                rais_amount = 0.0
                                if payscale_raise.fixed_amount > 0.0:
                                    rais_amount = contract.wage + payscale_raise.fixed_amount
                                elif payscale_raise.percentage > 0.0:
                                    rais_amount = (payscale_raise.percentage * contract.wage) + contract.wage

                                if rais_amount > 0.0 and rais_amount < basic_max:
                                    new_contract = contract.copy()
                                    employee = new_contract.employee_id

                                    if new_contract:
                                        contract.write({
                                            'date_end': last_promotion.date_start + relativedelta(
                                                days=payscale_raise.actual_days - 1),
                                            'state': 'close',
                                        })
                                        new_contract.write({
                                            'date_start': last_promotion.date_start + relativedelta(
                                                days=payscale_raise.actual_days),
                                            'date_end': last_promotion.date_start + relativedelta(
                                                days=payscale_raise.actual_days,
                                                years=int(new_contract.contract_validity)),
                                            'wage': rais_amount,
                                            'state': 'open',
                                        })

                                        new_promotion = self.env['employee.promotion'].create({
                                            'employee_id': new_contract.employee_id.id,
                                            'contract_status_new': new_contract.employee_id.contract_status if new_contract.employee_id.contract_status else False,
                                            'old_payscale_id': new_contract.payscale_id.id,
                                            'new_payscale_id': new_contract.payscale_id.id,
                                            'date_start': last_promotion.date_start + relativedelta(
                                                days=payscale_raise.actual_days),
                                            'contract_id': contract.id,
                                            'new_contract_id': new_contract.id,
                                            'wage_new': new_contract.wage,
                                            'furniture_allowance': contract.furniture_alw,
                                            'education_allowance': contract.education_alw,
                                            'payscale_scheduled_raise_id': payscale_raise.id,
                                            # 'exceptional_promotion': True,
                                        })
                                        if new_promotion:
                                            new_promotion.write({
                                                'state': 'approve'
                                            })
                                            new_promotion._get_payscale_grade_values()

                                elif rais_amount > 0.0 and rais_amount >= basic_max:
                                    if contract.wage < basic_max and rais_amount == basic_max:
                                        # rais_amount = (basic_max - contract.wage) + contract.wage
                                        new_contract = contract.copy()
                                        employee = new_contract.employee_id
                                        if new_contract:
                                            contract.write({
                                                'date_end': last_promotion.date_start + relativedelta(
                                                    days=payscale_raise.actual_days - 1),
                                                'state': 'close',
                                            })

                                            new_contract.write({
                                                'date_start': last_promotion.date_start + relativedelta(
                                                    days=payscale_raise.actual_days),
                                                'date_end': last_promotion.date_start + relativedelta(
                                                    days=payscale_raise.actual_days,
                                                    years=int(new_contract.contract_validity)),
                                                'wage': rais_amount,
                                                'state': 'open',
                                            })
                                            new_promotion = self.env['employee.promotion'].create({
                                                'employee_id': new_contract.employee_id.id,
                                                'contract_status_new': new_contract.employee_id.contract_status if new_contract.employee_id.contract_status else False,
                                                'old_payscale_id': new_contract.payscale_id.id,
                                                'new_payscale_id': new_contract.payscale_id.id,
                                                'date_start': last_promotion.date_start + relativedelta(
                                                    days=payscale_raise.actual_days),
                                                'contract_id': contract.id,
                                                'wage_new': new_contract.wage,
                                                'furniture_allowance': contract.furniture_alw,
                                                'education_allowance': contract.education_alw,
                                                'new_contract_id': new_contract.id,
                                                'payscale_scheduled_raise_id': payscale_raise.id,
                                                # 'exceptional_promotion': True,
                                            })
                                            if new_promotion:
                                                new_promotion.write({
                                                    'state': 'approve'
                                                })
                                                new_promotion._get_payscale_grade_values()

                                    elif contract.wage < basic_max and rais_amount > basic_max:
                                        new_contract = contract.copy()
                                        employee = new_contract.employee_id
                                        amount = (payscale_raise.extra_amount - (
                                                basic_max - contract.wage)) if payscale_raise.extra_amount else 0
                                        if new_contract:
                                            # if payscale_raise.fixed_amount > 0.0:
                                            #     amount += payscale_raise.fixed_amount
                                            # elif payscale_raise.percentage > 0.0:
                                            #     amount += payscale_raise.percentage * contract.wage
                                            contract.write({
                                                'date_end': last_promotion.date_start + relativedelta(
                                                    days=payscale_raise.actual_days - 1),
                                                'state': 'close',
                                            })

                                            new_contract.write({
                                                'date_start': last_promotion.date_start + relativedelta(
                                                    days=payscale_raise.actual_days),
                                                'date_end': last_promotion.date_start + relativedelta(
                                                    days=payscale_raise.actual_days,
                                                    years=int(new_contract.contract_validity)),
                                                # 'extra_amount': amount,
                                                'wage': basic_max,
                                                'end_of_basic_salary_bonus': (
                                                                                     rais_amount - basic_max) + contract.end_of_basic_salary_bonus,
                                                'state': 'open',
                                            })
                                            new_promotion = self.env['employee.promotion'].create({
                                                'employee_id': new_contract.employee_id.id,
                                                'contract_status_new': new_contract.employee_id.contract_status if new_contract.employee_id.contract_status else False,
                                                'old_payscale_id': new_contract.payscale_id.id,
                                                'new_payscale_id': new_contract.payscale_id.id,
                                                'date_start': last_promotion.date_start + relativedelta(
                                                    days=payscale_raise.actual_days),
                                                'contract_id': contract.id,
                                                'wage_new': new_contract.wage,
                                                'furniture_allowance': contract.furniture_alw,
                                                'education_allowance': contract.education_alw,
                                                'new_contract_id': new_contract.id,
                                                'payscale_scheduled_raise_id': payscale_raise.id,
                                                # 'exceptional_promotion': True,
                                            })
                                            if new_promotion:
                                                new_promotion.write({
                                                    'state': 'approve'
                                                })
                                                new_promotion._get_payscale_grade_values()

                                    elif contract.wage == basic_max:
                                        new_contract = contract.copy()
                                        employee = new_contract.employee_id
                                        if new_contract:
                                            # if payscale_raise.fixed_amount > 0.0:
                                            #     amount += payscale_raise.fixed_amount
                                            # elif payscale_raise.percentage > 0.0:
                                            #     amount += payscale_raise.percentage * contract.wage
                                            contract.write({
                                                'date_end': last_promotion.date_start + relativedelta(
                                                    days=payscale_raise.actual_days - 1),
                                                'state': 'close',
                                            })
                                            new_contract.write({
                                                'date_start': last_promotion.date_start + relativedelta(
                                                    days=payscale_raise.actual_days),
                                                'date_end': last_promotion.date_start + relativedelta(
                                                    days=payscale_raise.actual_days,
                                                    years=int(new_contract.contract_validity)),
                                                # 'extra_amount': payscale_raise.extra_amount,
                                                'end_of_basic_salary_bonus': (
                                                                                     rais_amount - basic_max) + contract.end_of_basic_salary_bonus,
                                                'state': 'open',
                                            })
                                            new_promotion = self.env['employee.promotion'].create({
                                                'employee_id': new_contract.employee_id.id,
                                                'contract_status_new': new_contract.employee_id.contract_status if new_contract.employee_id.contract_status else False,
                                                'old_payscale_id': new_contract.payscale_id.id,
                                                'new_payscale_id': new_contract.payscale_id.id,
                                                'date_start': last_promotion.date_start + relativedelta(
                                                    days=payscale_raise.actual_days),
                                                'contract_id': contract.id,
                                                'wage_new': new_contract.wage,
                                                'furniture_allowance': contract.furniture_alw,
                                                'education_allowance': contract.education_alw,
                                                'new_contract_id': new_contract.id,
                                                'payscale_scheduled_raise_id': payscale_raise.id,
                                                # 'exceptional_promotion': True,
                                            })
                                            if new_promotion:
                                                new_promotion.write({
                                                    'state': 'approve'
                                                })
                                                new_promotion._get_payscale_grade_values()


                        elif contract.employee_id.actual_duty and contract.employee_id.actual_duty >= payscale_raise.actual_days and (
                                contract.employee_id.joining_date + relativedelta(
                            days=payscale_raise.actual_days)) <= date.today():
                            rais_amount = 0.0
                            if payscale_raise.fixed_amount > 0.0:
                                rais_amount = contract.wage + payscale_raise.fixed_amount
                            elif payscale_raise.percentage > 0.0:
                                rais_amount = (payscale_raise.percentage * contract.wage) + contract.wage

                            if rais_amount > 0.0 and rais_amount < basic_max:
                                new_contract = contract.copy()
                                employee = new_contract.employee_id

                                if new_contract:
                                    contract.write({
                                        'date_end': employee.joining_date + relativedelta(
                                            days=payscale_raise.actual_days - 1) if employee.joining_date >= contract.date_start else contract.date_start + relativedelta(
                                            days=payscale_raise.actual_days - 1),
                                        'state': 'close',
                                    })
                                    new_contract.write({
                                        'date_start': employee.joining_date + relativedelta(
                                            days=payscale_raise.actual_days) if employee.joining_date > contract.date_start else contract.date_start + relativedelta(
                                            days=payscale_raise.actual_days),
                                        'date_end': employee.joining_date + relativedelta(
                                            days=payscale_raise.actual_days, years=int(
                                                new_contract.contract_validity)) if employee.joining_date > contract.date_start else contract.date_start + relativedelta(
                                            days=payscale_raise.actual_days, years=int(new_contract.contract_validity)),
                                        'wage': rais_amount,
                                        'state': 'open',
                                    })

                                    new_promotion = self.env['employee.promotion'].create({
                                        'employee_id': new_contract.employee_id.id,
                                        'contract_status_new': new_contract.employee_id.contract_status if new_contract.employee_id.contract_status else False,
                                        'old_payscale_id': new_contract.payscale_id.id,
                                        'new_payscale_id': new_contract.payscale_id.id,
                                        'date_start': new_contract.date_start,
                                        'contract_id': contract.id,
                                        'wage_new': new_contract.wage,
                                        'furniture_allowance': contract.furniture_alw,
                                        'education_allowance': contract.education_alw,
                                        'new_contract_id': new_contract.id,
                                        'payscale_scheduled_raise_id': payscale_raise.id,
                                        # 'exceptional_promotion': True,
                                    })
                                    if new_promotion:
                                        new_promotion.write({
                                            'state': 'approve'
                                        })
                                        new_promotion._get_payscale_grade_values()
                            elif rais_amount > 0.0 and rais_amount >= basic_max:
                                if contract.wage < basic_max and rais_amount == basic_max:
                                    # rais_amount = (basic_max - contract.wage) + contract.wage
                                    new_contract = contract.copy()
                                    employee = new_contract.employee_id
                                    if new_contract:
                                        contract.write({
                                            'date_end': employee.joining_date + relativedelta(
                                                days=payscale_raise.actual_days - 1),
                                            'state': 'close',
                                        })

                                        new_contract.write({
                                            'date_start': employee.joining_date + relativedelta(
                                                days=payscale_raise.actual_days),
                                            'date_end': employee.joining_date + relativedelta(
                                                days=payscale_raise.actual_days,
                                                years=int(new_contract.contract_validity)),
                                            'wage': rais_amount,
                                            'state': 'open',
                                        })
                                        new_promotion = self.env['employee.promotion'].create({
                                            'employee_id': new_contract.employee_id.id,
                                            'contract_status_new': new_contract.employee_id.contract_status if new_contract.employee_id.contract_status else False,
                                            'old_payscale_id': new_contract.payscale_id.id,
                                            'new_payscale_id': new_contract.payscale_id.id,
                                            'date_start': employee.joining_date + relativedelta(
                                                days=payscale_raise.actual_days),
                                            'contract_id': contract.id,
                                            'wage_new': new_contract.wage,
                                            'furniture_allowance': contract.furniture_alw,
                                            'education_allowance': contract.education_alw,
                                            'new_contract_id': new_contract.id,
                                            'payscale_scheduled_raise_id': payscale_raise.id,
                                            # 'exceptional_promotion': True,
                                        })
                                        if new_promotion:
                                            new_promotion.write({
                                                'state': 'approve'
                                            })
                                            new_promotion._get_payscale_grade_values()

                                elif contract.wage < basic_max and rais_amount > basic_max:
                                    new_contract = contract.copy()
                                    employee = new_contract.employee_id
                                    amount = (payscale_raise.extra_amount - (
                                            basic_max - contract.wage)) if payscale_raise.extra_amount else 0
                                    if new_contract:
                                        # if payscale_raise.fixed_amount > 0.0:
                                        #     amount += payscale_raise.fixed_amount
                                        # elif payscale_raise.percentage > 0.0:
                                        #     amount += payscale_raise.percentage * contract.wage
                                        contract.write({
                                            'date_end': employee.joining_date + relativedelta(
                                                days=payscale_raise.actual_days - 1),
                                            'state': 'close',
                                        })

                                        new_contract.write({
                                            'date_start': employee.joining_date + relativedelta(
                                                days=payscale_raise.actual_days),
                                            'date_end': employee.joining_date + relativedelta(
                                                days=payscale_raise.actual_days,
                                                years=int(new_contract.contract_validity)),
                                            # 'extra_amount': amount,
                                            'wage': basic_max,
                                            'end_of_basic_salary_bonus': (
                                                                                 rais_amount - basic_max) + contract.end_of_basic_salary_bonus,
                                            'state': 'open',
                                        })
                                        new_promotion = self.env['employee.promotion'].create({
                                            'employee_id': new_contract.employee_id.id,
                                            'contract_status_new': new_contract.employee_id.contract_status if new_contract.employee_id.contract_status else False,
                                            'old_payscale_id': new_contract.payscale_id.id,
                                            'new_payscale_id': new_contract.payscale_id.id,
                                            'date_start': employee.joining_date + relativedelta(
                                                days=payscale_raise.actual_days),
                                            'contract_id': contract.id,
                                            'new_contract_id': new_contract.id,
                                            'wage_new': new_contract.wage,
                                            'furniture_allowance': contract.furniture_alw,
                                            'education_allowance': contract.education_alw,
                                            'payscale_scheduled_raise_id': payscale_raise.id,
                                            # 'exceptional_promotion': True,
                                        })
                                        if new_promotion:
                                            new_promotion.write({
                                                'state': 'approve'
                                            })
                                            new_promotion._get_payscale_grade_values()

                                elif contract.wage == basic_max:
                                    new_contract = contract.copy()
                                    employee = new_contract.employee_id
                                    if new_contract:
                                        # if payscale_raise.fixed_amount > 0.0:
                                        #     amount += payscale_raise.fixed_amount
                                        # elif payscale_raise.percentage > 0.0:
                                        #     amount += payscale_raise.percentage * contract.wage
                                        contract.write({
                                            'date_end': employee.joining_date + relativedelta(
                                                days=payscale_raise.actual_days - 1) if employee.joining_date >= contract.date_start else contract.date_start + relativedelta(
                                                days=payscale_raise.actual_days - 1),
                                            'state': 'close',
                                        })
                                        new_contract.write({
                                            'date_start': employee.joining_date + relativedelta(
                                                days=payscale_raise.actual_days) if employee.joining_date > contract.date_start else contract.date_start + relativedelta(
                                                days=payscale_raise.actual_days),
                                            'date_end': employee.joining_date + relativedelta(
                                                days=payscale_raise.actual_days, years=int(
                                                    new_contract.contract_validity)) if employee.joining_date > contract.date_start else contract.date_end + relativedelta(
                                                days=payscale_raise.actual_days - 1),
                                            # 'extra_amount': payscale_raise.extra_amount,
                                            'end_of_basic_salary_bonus': (
                                                                                 rais_amount - basic_max) + contract.end_of_basic_salary_bonus,
                                            'state': 'open',
                                        })
                                        new_promotion = self.env['employee.promotion'].create({
                                            'employee_id': new_contract.employee_id.id,
                                            'contract_status_new': new_contract.employee_id.contract_status if new_contract.employee_id.contract_status else False,
                                            'old_payscale_id': new_contract.payscale_id.id,
                                            'new_payscale_id': new_contract.payscale_id.id,
                                            'date_start': new_contract.date_start,
                                            'contract_id': contract.id,
                                            'new_contract_id': new_contract.id,
                                            'wage_new': new_contract.wage,
                                            'furniture_allowance': contract.furniture_alw,
                                            'education_allowance': contract.education_alw,
                                            'payscale_scheduled_raise_id': payscale_raise.id,
                                            # 'exceptional_promotion': True,
                                        })
                                        if new_promotion:
                                            new_promotion.write({
                                                'state': 'approve'
                                            })
                                            new_promotion._get_payscale_grade_values()
