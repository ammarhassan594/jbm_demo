from odoo import models, fields, api, tools, _


class HrPayslipCustom(models.Model):
    _inherit = 'hr.payslip'

    allowance_request_ids = fields.Many2many(comodel_name='allowance.request', string="Allowance Requests")


    def get_EOSB_advance_allowance(self, payslip, employee):
        eligible_amount = 0
        if payslip:
            employee_allownace = self.env['allowance.request'].search([('employee_id', '=', employee.id),
                                                                       ('allowance_type.code', '=', 'eosb'),
                                                                       ('payment_date', '>=', payslip.date_from),
                                                                       ('payment_date', '<=', payslip.date_to),
                                                                       ('state', '=', 'approved'),
                                                                       ('allowance_type.enable_payslip', '=', True)], limit=1)
            if employee_allownace:
                eligible_amount += employee_allownace.eligible_amount
                if payslip.allowance_request_ids:
                    alw_ids = payslip.allowance_request_ids.ids + [employee_allownace.id]
                    payslip.allowance_request_ids = [(4, alw_ids)]
                else:
                    payslip.allowance_request_ids = [(4, employee_allownace.id)]
        return eligible_amount

    def get_education_allowance(self, payslip, employee):
        eligible_amount = 0
        if payslip:
            employee_allownace = self.env['allowance.request'].search([('employee_id', '=', employee.id),
                                                                       ('allowance_type.code', '=', 'education'),
                                                                       ('payment_date', '>=', payslip.date_from),
                                                                       ('payment_date', '<=', payslip.date_to),
                                                                       ('state', '=', 'approved'),
                                                                       ('allowance_type.enable_payslip', '=', True)], limit=1)
            if employee_allownace:
                eligible_amount += employee_allownace.eligible_amount
                if payslip.allowance_request_ids:
                    alw_ids = payslip.allowance_request_ids.ids + [employee_allownace.id]
                    payslip.allowance_request_ids = [(4, alw_ids)]
                else:
                    payslip.allowance_request_ids = [(4, employee_allownace.id)]
        return eligible_amount

    def get_furniture_maintenance_allowance(self, payslip, employee):
        eligible_amount = 0
        if payslip:
            employee_allownace = self.env['allowance.request'].search([('employee_id', '=', employee.id),
                                                                       ('allowance_type.code', '=', 'maintenance'),
                                                                       ('payment_date', '>=', payslip.date_from),
                                                                       ('payment_date', '<=', payslip.date_to),
                                                                       ('state', '=', 'approved'),
                                                                       ('allowance_type.enable_payslip', '=', True)], limit=1)
            if employee_allownace:
                eligible_amount += employee_allownace.eligible_amount
                if payslip.allowance_request_ids:
                    alw_ids = payslip.allowance_request_ids.ids + [employee_allownace.id]
                    payslip.allowance_request_ids = [(4, alw_ids)]
                else:
                    payslip.allowance_request_ids = [(4, employee_allownace.id)]
        return eligible_amount


    def get_mobilization_allowance(self, payslip, employee):
        eligible_amount = 0
        if payslip:
            employee_allownace = self.env['allowance.request'].search([('employee_id', '=', employee.id),
                                                                       ('allowance_type.code', '=', 'mobilization'),
                                                                       ('payment_date', '>=', payslip.date_from),
                                                                       ('payment_date', '<=', payslip.date_to),
                                                                       ('state', '=', 'approved'),
                                                                       ('allowance_type.enable_payslip', '=', True)], limit=1)
            if employee_allownace:
                eligible_amount += employee_allownace.eligible_amount
                if payslip.allowance_request_ids:
                    alw_ids = payslip.allowance_request_ids.ids + [employee_allownace.id]
                    payslip.allowance_request_ids = [(4, alw_ids)]
                else:
                    payslip.allowance_request_ids = [(4, employee_allownace.id)]
        return eligible_amount


    def get_business_training_trip_allowance(self, payslip, employee):
        eligible_amount = 0
        if payslip:
            employee_allownace = self.env['allowance.request'].search([('employee_id', '=', employee.id),
                                                                       ('allowance_type.code', '=', 'trip'),
                                                                       ('payment_date', '>=', payslip.date_from),
                                                                       ('payment_date', '<=', payslip.date_to),
                                                                       ('state', '=', 'approved'),
                                                                       ('allowance_type.enable_payslip', '=', True)], limit=1)
            if employee_allownace:
                eligible_amount += employee_allownace.eligible_amount
                if payslip.allowance_request_ids:
                    alw_ids = payslip.allowance_request_ids.ids + [employee_allownace.id]
                    payslip.allowance_request_ids = [(4, alw_ids)]
                else:
                    payslip.allowance_request_ids = [(4, employee_allownace.id)]
        return eligible_amount

    def get_furniture_allowance(self, payslip, employee):
        eligible_amount = 0
        if payslip:
            employee_allownace = self.env['allowance.request'].search([('employee_id', '=', employee.id),
                                                                       ('allowance_type.code', '=', 'furniture'),
                                                                       ('payment_date', '>=', payslip.date_from),
                                                                       ('payment_date', '<=', payslip.date_to),
                                                                       ('state', '=', 'approved')], limit=1)
            if employee_allownace:
                eligible_amount += employee_allownace.eligible_amount
                if payslip.allowance_request_ids:
                    alw_ids = payslip.allowance_request_ids.ids + [employee_allownace.id]
                    payslip.allowance_request_ids = [(4, alw_ids)]
                else:
                    payslip.allowance_request_ids = [(4, employee_allownace.id)]
        return eligible_amount

    def get_maintenance_allowance(self, payslip, employee):
        eligible_amount = 0
        if payslip:
            employee_allownace = self.env['allowance.request'].search([('employee_id', '=', employee.id),
                                                                       ('allowance_type.code', '=', 'maintenance'),
                                                                       ('payment_date', '>=', payslip.date_from),
                                                                       ('payment_date', '<=', payslip.date_to),
                                                                       ('state', '=', 'approved')], limit=1)
            if employee_allownace:
                eligible_amount += employee_allownace.approved_amount
                if payslip.allowance_request_ids:
                    alw_ids = payslip.allowance_request_ids.ids + [employee_allownace.id]
                    payslip.allowance_request_ids = [(4, alw_ids)]
                else:
                    payslip.allowance_request_ids = [(4, employee_allownace.id)]
        return eligible_amount

    def get_ticket_allowance(self, payslip, employee):
        eligible_amount = 0
        if payslip:
            employee_allownace = self.env['allowance.request'].search([('employee_id', '=', employee.id),
                                                                       ('allowance_type.code', '=', 'ticket'),
                                                                       ('effective_date', '>=', payslip.date_from),
                                                                       ('effective_date', '<=', payslip.date_to),
                                                                       ('state', '=', 'approved')])

            if employee_allownace:
                eligible_amount += sum(employee_allownace.mapped('eligible_amount'))
                if payslip.allowance_request_ids:
                    payslip.allowance_request_ids = [(4, employee_allownace.ids)]
                else:
                    payslip.allowance_request_ids = [(4, employee_allownace.ids)]
        return eligible_amount

    def action_payslip_done(self):
        payslip = super(HrPayslipCustom, self).action_payslip_done()
        self._action_paid_allowance_request()
        return payslip

    def _action_paid_allowance_request(self):
        for rec in self:
            if rec.state == 'done':
                for request in rec.allowance_request_ids:
                    if request.state == 'approved':
                        request.state = 'paid'
