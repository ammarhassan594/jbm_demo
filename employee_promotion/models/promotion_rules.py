import logging
from odoo import models, fields, api, _
from datetime import date
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class PromotionRules(models.Model):
    _name = "promotion.rules"
    _rec_name = 'degree_id'

    from_grade_id = fields.Many2one('employee.payscale', string="From Grade", required=True)
    to_grade_id = fields.Many2one('employee.payscale', string="To Grade", required=True)
    degree_id = fields.Many2one('hr.recruitment.degree', string="Degree", required=True)
    number_of_actual_work_days = fields.Integer(string="Number Of Actual Work Days", required=True)
    contract_marital_status = fields.Selection([
        ('married', 'Married'),
        ('single', 'Single'),
    ], string="Contract Marital Status")
    extra_amount = fields.Float(string="Extra Amount")

    @api.model
    def schedule_promotion_rules(self):
        promotion_rules = self.env['promotion.rules'].search([
            ('from_grade_id', '!=', False),
            ('degree_id', '!=', False),
            ('number_of_actual_work_days', '>', 0),
            ('to_grade_id', '!=', False),
        ])
        _logger.info("----> Running Employee Promotions")
        for rule in promotion_rules:
            # if all((rule.from_grade_id, rule.degree_id, rule.number_of_actual_work_days, rule.to_grade_id)):
            employees = self.env['hr.employee'].search([
                ('degree_id', '=', rule.degree_id.id),
                # ('actual_duty', '>=', rule.number_of_actual_work_days),
                ('contract_id.payscale_id', '=', rule.from_grade_id.id),
                ('contract_status', '=', rule.contract_marital_status),
            ])
            promotion = self.env['employee.promotion']
            if employees:
                for employee in employees:
                    _logger.info("Employee {}".format(employee))
                    same_rule = promotion.search(
                        [('employee_id', '=', employee.id), ('promotion_rule_id', '=', rule.id)])
                    if same_rule:
                        continue
                    if employee.promotion_ids.filtered(lambda x: x.date_start and x.promotion_rule_id):
                        employee_promotions = employee.promotion_ids.filtered(lambda x: x.date_start). \
                            sorted(key=lambda x: x.date_start, reverse=True)
                        _logger.info("Employee Promotions {}".format(employee_promotions))
                        last_promotion = employee_promotions and employee_promotions[0]
                        _logger.info("last_promotion {}".format(last_promotion))
                        today = fields.Date.context_today(employee)
                        _logger.info("last_promotion.date_start {}".format(last_promotion.date_start))
                        _logger.info("today {}".format(today))

                        if today < last_promotion.date_start:
                            continue
                        actual_duty = (today - last_promotion.date_start).days + 1
                        _logger.info("actual_duty {}".format(actual_duty))

                        if actual_duty >= rule.number_of_actual_work_days:
                            promotion.create({
                                'employee_id': employee.id,
                                'contract_status_new': rule.contract_marital_status
                                if rule.contract_marital_status else False,
                                'old_payscale_id': rule.from_grade_id.id,
                                'new_payscale_id': rule.to_grade_id.id,
                                'date_start': last_promotion.date_start + relativedelta(
                                    days=actual_duty),
                                'state': 'draft',
                                'promotion_rule_id': rule.id,
                            })
                    elif employee.actual_duty >= rule.number_of_actual_work_days:
                        _logger.info("First Employee Promotion ")
                        _logger.info("employee {}".format(employee))
                        _logger.info("rule {}".format(rule))
                        promotion.create({
                            'employee_id': employee.id,
                            'contract_status_new': rule.contract_marital_status if rule.contract_marital_status else False,
                            'old_payscale_id': rule.from_grade_id.id,
                            'new_payscale_id': rule.to_grade_id.id,
                            'date_start': employee.joining_date + relativedelta(
                                days=rule.number_of_actual_work_days),
                            'state': 'draft',
                            'promotion_rule_id': rule.id,
                        })
