import datetime
from datetime import date, datetime
from odoo.exceptions import ValidationError
from odoo.tools import float_compare
from odoo import fields, models, api, _


class LeaveDetails(models.Model):
    _inherit = 'hr.leave'

    date_validated = fields.Datetime(string='Validated On', store=True)
    unpaid_leave_id = fields.Many2one('hr.leave', string='Related Unpaid leave')
    approve_validate = fields.Boolean('Approval', default=False)
    number_of_days_boolean = fields.Boolean('Number of Days Boolean', default=False)

    def action_approve(self):
        self.approve_validate = True
        res = super(LeaveDetails, self).action_approve()
        self.approve_validate = False
        if self.unpaid_leave_id:
            self.unpaid_leave_id.action_approve()
        return res

    def action_validate(self):
        """
        function for calculating leaves and updating
        probation period upon the leave days

        """
        self.approve_validate = True
        res = super(LeaveDetails, self).action_validate()
        self.approve_validate = False
        for rec in self:
            contract = self.env['hr.contract'].search(
                [('employee_id', '=', rec.employee_id.id),
                 ('state', '=', 'probation')], limit=1)
            # check valid contract and probation details.
            if contract and contract.probation_id:
                training_dtl = contract.probation_id
                leave_type = self.env.ref('hr_holidays.holiday_status_unpaid')
                no_of_days = 0
                leave_info = []

                # calculating half day leave :
                if rec.request_unit_half:
                    for half in contract.half_leave_ids:
                        leave_info.append(half.id)
                    leave_info.append(rec.id)
                    contract.write({'half_leave_ids': leave_info})
                    if len(contract.half_leave_ids) == 2:
                        no_of_days = 1
                        contract.half_leave_ids = False

                # calculating full day leaves and updating period :
                if rec.holiday_status_id.id == leave_type.id \
                        and contract.state == "probation" and training_dtl and \
                        not rec.request_unit_half and not rec.request_unit_hours:
                    from_date = date(rec.request_date_from.year,
                                     rec.request_date_from.month,
                                     rec.request_date_from.day)
                    to_date = date(rec.request_date_to.year,
                                   rec.request_date_to.month,
                                   rec.request_date_to.day)
                    if from_date >= training_dtl.start_date and \
                            to_date <= training_dtl.end_date:
                        updated_date = training_dtl.end_date + datetime.timedelta(
                            days=rec.number_of_days)
                        leave_info = []
                        for leave in training_dtl.leave_ids:
                            leave_info.append(leave.id)
                        leave_info.append(rec.id)
                        training_dtl.write({
                            'end_date': updated_date,
                            'state': "extended",
                            'leave_ids': leave_info
                        })
                        contract.write({'trial_date_end': updated_date})

                # updating period based on half day leave:
                elif rec.holiday_status_id.id == leave_type.id \
                        and contract.state == "probation" and training_dtl \
                        and rec.request_unit_half:
                    from_date = date(rec.request_date_from.year,
                                     rec.request_date_from.month,
                                     rec.request_date_from.day)
                    if training_dtl.end_date >= from_date >= training_dtl.start_date:
                        updated_date = training_dtl.end_date + datetime.timedelta(
                            days=no_of_days)
                        for leave in training_dtl.leave_ids:
                            leave_info.append(leave.id)
                        leave_info.append(rec.id)
                        training_dtl.write({
                            'end_date': updated_date,
                            'state': "extended",
                            'leave_ids': leave_info
                        })
                        contract.write({'trial_date_end': updated_date})
            if rec.unpaid_leave_id:
                rec.unpaid_leave_id.action_validate()
        return res

    @api.constrains('state', 'number_of_days', 'holiday_status_id')
    def _check_holidays(self):
        for holiday in self:
            if not holiday.approve_validate and not holiday.number_of_days_boolean:
                if holiday.holiday_type != 'employee' or not holiday.employee_id or holiday.holiday_status_id.allocation_type == 'no':
                    continue
                leave_days = holiday.holiday_status_id.get_days(holiday.employee_id.id)[holiday.holiday_status_id.id]
                leave_round = round(leave_days['remaining_leaves'])
                max_leaves = round(leave_days['max_leaves'])
                leaves_taken = round(leave_days['leaves_taken'])
                # virtual_remaining_leaves_round = round(leave_days['virtual_remaining_leaves'])
                if max_leaves - leaves_taken == leave_round and holiday.holiday_status_id.exceed_allocation_days:
                    from_date = datetime.strptime(
                        str(holiday.request_date_from) + ' 00:00:00',
                        "%Y-%m-%d %H:%M:%S")
                    to_date = datetime.strptime(
                        str(holiday.request_date_to) + ' 00:00:00',
                        "%Y-%m-%d %H:%M:%S")
                    sorted_working_days =sorted(holiday.employee_id.resource_calendar_id._work_intervals_days(from_date, to_date))
                    if len(sorted_working_days) > leave_round:
                        annual_leave_end_date = sorted_working_days[leave_round-1]
                        unpaid_leave_start_date = sorted_working_days[leave_round]
                        if holiday.number_of_days > leave_round:
                            unpaid_leaves = holiday.number_of_days - leave_round
                            time_off_type = self.env['hr.leave.type'].search([('code', '=', 'UNPAID')])
                            unpaid_leave_end_date = holiday.request_date_to
                            holiday.write({
                                'request_date_to': annual_leave_end_date.strftime("%Y-%m-%d"),
                                'number_of_days': leave_round,
                                'number_of_days_boolean': True
                            })
                            unpaid_leave_request = self.env['hr.leave'].create({
                                'employee_id': holiday.employee_id.id,
                                'holiday_status_id': time_off_type.id,
                                'holiday_type': 'employee',
                                'department_id': holiday.employee_id.department_id.id or '',
                                'request_date_from': unpaid_leave_start_date,
                                'request_date_to': unpaid_leave_end_date,
                                'number_of_days': unpaid_leaves,
                                'number_of_days_boolean': True
                            })
                            holiday.unpaid_leave_id = unpaid_leave_request
                    else:
                        return True
                # I can not explain why comment this code but D)
                # else:
                #     raise ValidationError(_('The number of remaining time off is not sufficient for this time off type.\n'
                #                             'Please also check the time off waiting for validation.'))

    '''
    @api.constrains('date_from', 'date_to', 'state', 'employee_id')
    def _check_date(self):
        for holiday in self:
            domain = [
                ('request_date_from', '<', holiday.request_date_from),
                ('request_date_to', '>', holiday.request_date_to),
                ('employee_id', '=', holiday.employee_id.id),
                ('id', '!=', holiday.id),
                ('state', 'not in', ['cancel', 'refuse']),
            ]
            nholidays = self.search_count(domain)
            if nholidays:
                raise ValidationError(_('You can not set 2 times off that overlaps on the same day for the same employee.'))
    '''

class LeaveType(models.Model):
    _inherit = 'hr.leave.type'

    exceed_allocation_days = fields.Boolean(string='Exceed Allocation Days')
