from odoo import models, fields, api, _

class EligibleForPromotion(models.Model):
    _name = 'eligible.for.promotion'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string="Employee")
    current_grade = fields.Many2one('employee.payscale', string="Current Grade")
    new_grade = fields.Many2one('employee.payscale', string="New Grade")


    @api.model
    def get_eligible_for_promotion(self):
        promotion_rules = self.env['promotion.rules'].search([])
        if promotion_rules:
            for rule in promotion_rules:
                if rule.from_grade_id and rule.degree_id and rule.number_of_actual_work_days:
                    employees = self.env['hr.employee'].search([
                        ('degree_id', '=', rule.degree_id.id),
                        ('actual_duty', '=', rule.number_of_actual_work_days)
                    ])
                    if employees:
                        for employee in employees:
                            contract = self.env['hr.contract'].search([
                                ('employee_id', '=', employee.id),
                                ('state', '=', 'open'),
                                ('payscale_id', '=', rule.from_grade_id.id)],
                                limit=1, order="id DESC")
                            if contract:
                                eligible_promotion = self.env['eligible.for.promotion'].search([
                                    ('employee_id', '=', employee.id),
                                    ('current_grade', '=', rule.from_grade_id.id),
                                    ('new_grade', '=', rule.to_grade_id.id)
                                ])
                                if not eligible_promotion:
                                    self.env['eligible.for.promotion'].sudo().create({
                                        'employee_id': employee.id,
                                        'current_grade': rule.from_grade_id.id,
                                        'new_grade': rule.to_grade_id.id,
                                    })

