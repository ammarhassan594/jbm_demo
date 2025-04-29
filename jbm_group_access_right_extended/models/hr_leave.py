from odoo import api, fields, models, tools, _
from odoo.exceptions import AccessError, UserError, ValidationError


class EmployeeLeave(models.Model):
    _inherit = "hr.leave"

    def _check_approval_update(self, state):
        """ Check if target state is achievable. """
        if self.env.is_superuser():
            return

        current_employee = self.env.user.employee_id
        is_officer = self.env.user.has_group('hr_holidays.group_hr_holidays_user')
        is_manager = self.env.user.has_group('jbm_group_access_right_extended.group_timeOff_manager') or \
                     self.env.user.has_group('hr_holidays.group_hr_holidays_manager')

        for holiday in self:
            val_type = holiday.validation_type

            if not is_manager and state != 'confirm':
                if state == 'draft':
                    if holiday.state == 'refuse':
                        raise UserError(_('Only a Time Off Manager can reset a refused leave.'))
                    if holiday.date_from and holiday.date_from.date() <= fields.Date.today():
                        raise UserError(_('Only a Time Off Manager can reset a started leave.'))
                    if holiday.employee_id != current_employee:
                        raise UserError(_('Only a Time Off Manager can reset other people leaves.'))
                else:
                    if val_type == 'no_validation' and current_employee == holiday.employee_id:
                        continue
                    # use ir.rule based first access check: department, members, ... (see security.xml)
                    holiday.check_access_rule('write')

                    # This handles states validate1 validate and refuse
                    if holiday.employee_id == current_employee:
                        raise UserError(_('Only a Time Off Manager can approve/refuse its own requests.'))

                    if (state == 'validate1' and val_type == 'both') and holiday.holiday_type == 'employee':
                        if not is_officer and self.env.user != holiday.employee_id.leave_manager_id:
                            raise UserError(
                                _('You must be either %s\'s manager or Time off Manager to approve this leave') % (
                                    holiday.employee_id.name))

                    if (
                            state == 'validate' and val_type == 'manager') and self.env.user != holiday.employee_id.leave_manager_id:
                        raise UserError(_('You must be %s\'s Manager to approve this leave', holiday.employee_id.name))

                    if not is_officer and (
                            state == 'validate' and val_type == 'hr') and holiday.holiday_type == 'employee':
                        raise UserError(
                            _('You must either be a Time off Officer or Time off Manager to approve this leave'))
