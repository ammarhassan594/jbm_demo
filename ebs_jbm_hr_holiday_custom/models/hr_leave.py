# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date


class HrLeaveCustom(models.Model):
    _inherit = "hr.leave"

    approval_date = fields.Datetime(string="Approval Date")
    phone_number_on_leave = fields.Char(string="Phone number while on leave")
    address_during_leave = fields.Char(string="Address during leave")
    return_date = fields.Date(string="Return Date")

    @api.constrains('date_from')
    def past_leave_constrains(self):
        for rec in self:
            if rec.holiday_status_id.add_validation_past_leave and rec.date_from and rec.date_from.date() < date.today():
                raise UserError(_('you cannot submit a past leave request in this leave type'))

    @api.constrains('return_date')
    def return_date_constrains(self):
        for rec in self:
            if rec.holiday_status_id.is_permission:
                if rec.return_date and rec.request_date_from and rec.return_date < rec.request_date_from:
                    raise UserError(_('return date must be equal or greater than date from'))
            elif rec.return_date and rec.request_date_from and rec.return_date <= rec.request_date_from:
                raise UserError(_('return date must be greater than date from'))

    def action_validate(self):
        if self.holiday_status_id.leave_validation_type == 'both':
            if self.state != 'validate1':
                raise ValidationError("Leave need to be approved by {manager} first".format(manager=self.employee_ids.leave_manager_id.name))
        if self.state == 'validate':
            self.approval_date = datetime.datetime.now()
        return super(HrLeaveCustom, self).action_validate()

    @api.depends('state', 'employee_id', 'department_id')
    def _compute_can_approve(self):
        res = super(HrLeaveCustom, self)._compute_can_approve()

        # for holiday in self:
        #     if holiday.can_approve and holiday.state == 'confirm':
        #         if holiday.validation_type in ['both', 'manager'] and \
        #                 self.env.user != holiday.employee_id.leave_manager_id and holiday.employee_id.leave_manager_id:
        #             holiday.can_approve = False
        #         if holiday.validation_type in ['both', 'manager'] and \
        #                 not holiday.employee_id.leave_manager_id:
        #             holiday.can_approve = True
        #         elif holiday.validation_type == 'hr' and \
        #                 self.env.user != holiday.holiday_status_id.responsible_id:
        #             holiday.can_approve = False
        #     elif holiday.can_approve and holiday.state == 'validate1' and \
        #             self.env.user != holiday.holiday_status_id.responsible_id:
        #         holiday.can_approve = False

        return res

    def _get_employee_custody(self):
        self.ensure_one()
        custody = ''
        internal_picking = self.env['stock.picking.type'].search([('code', '=', 'internal')])
        if self.user_id:
            related_picking = self.env['stock.picking'].search(
                [('partner_id', '!=', False), ('partner_id', '=', self.user_id.partner_id.id),
                 ('picking_type_id', 'in', internal_picking.ids),
                 ('state', '=', 'done')])
            custody_lines = related_picking.move_line_ids_without_package.filtered(
                lambda line: line.lot_id and not line.move_id.returned_move_ids)
            custody = ','.join(custody_lines.mapped('product_id.name'))
        return custody

    def _get_last_leave_date(self):
        self.ensure_one()
        last_leave_date = ''
        last_leaves = self.sudo().search(
            [('holiday_status_id', '=', self.holiday_status_id.id), ('state', '=', 'validate'),
             ('request_date_to', '<=', self.request_date_from),
             ('employee_id', '=', self.employee_id.id)]).sorted('request_date_from')

        if last_leaves:
            last_leave_date = last_leaves[-1].request_date_from.strftime('%d/%m/%Y')
        return last_leave_date

    def _get_casual_balance_values(self):
        self.ensure_one()
        return_data = {}
        if self.holiday_status_id.is_casual_leave_type:
            employee_calender = self.employee_id.contract_id.resource_calendar_id if self.employee_id.contract_id else self.employee_id.resource_calendar_id
            average_working_hours = employee_calender.hours_per_day
            if average_working_hours:
                request_date_from = self.request_date_from if self.request_date_from else fields.Date.today()
                year_first_day = request_date_from.replace(day=1, month=1)
                year_last_day = request_date_from.replace(day=31, month=12)
                allocations = self.env['hr.leave.allocation'].search([
                    ('holiday_status_id', '=', self.holiday_status_id.id),
                    ('employee_id', '=', self.employee_id.id),
                    ('state', '=', 'validate'), ('date_from', '>=', year_first_day)
                ]).filtered(lambda allocation:
                            allocation.date_to and allocation.date_to >= request_date_from >= allocation.date_from and allocation.date_to <= year_last_day
                            or (not allocation.date_to and allocation.date_from <= request_date_from))
                year_allocation_days = sum(allocations.mapped('number_of_hours_display'))
                return_data.update({
                    'year_allocation_days': year_allocation_days / average_working_hours,
                    'consumed_allocation_days': (year_allocation_days - self.remaining_balance) / average_working_hours,
                    'leave_duration': self.number_of_hours_display / average_working_hours,
                    'remaining_balance': self.remaining_balance / average_working_hours
                })
        return return_data
