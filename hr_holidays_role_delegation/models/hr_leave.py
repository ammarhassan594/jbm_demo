import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime


class InheritHrLeave(models.Model):
    _inherit = "hr.leave"

    def _check_role_delegation(self, user):
        current_date = datetime.today()
        role_delegation = False
        if user:
            role_delegation = self.env['roles.delegation'].sudo().search([
                ('date_from', '<=', current_date),
                ('date_to', '>=', current_date),
                ('delegate_from', '=', user.id),
                ('state', '=', 'approved')
            ])
        if role_delegation:
            return role_delegation.delegate_to
        else:
            return False

    @api.depends('state', 'employee_id', 'department_id')
    def _compute_can_approve(self):
        res = super(InheritHrLeave, self)._compute_can_approve()

        for holiday in self:
            if holiday.can_approve and holiday.state == 'confirm':
                if holiday.validation_type in ['both', 'manager'] and \
                        self.env.user != holiday.employee_id.leave_manager_id and holiday.employee_id.leave_manager_id:
                    user_delegation = self._check_role_delegation(holiday.employee_id.leave_manager_id)
                    if not user_delegation:
                        holiday.can_approve = False
                    elif self.env.user in user_delegation:
                        holiday.can_approve = True
                    else:
                        holiday.can_approve = False

                if holiday.validation_type in ['both', 'manager'] and \
                        not holiday.employee_id.leave_manager_id:
                    holiday.can_approve = True
                elif holiday.validation_type == 'hr' and \
                        self.env.user != holiday.holiday_status_id.responsible_id:
                    user_delegation = self._check_role_delegation(holiday.holiday_status_id.responsible_id)
                    if not user_delegation:
                        holiday.can_approve = False
                    else:
                        holiday.can_approve = True
            elif holiday.can_approve and holiday.state == 'validate1' and \
                    self.env.user != holiday.holiday_status_id.responsible_id:
                user_delegation = self._check_role_delegation(holiday.holiday_status_id.responsible_id)
                if not user_delegation:
                    holiday.can_approve = False
                else:
                    holiday.can_approve = True

        return res