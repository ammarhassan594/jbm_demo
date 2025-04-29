from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class JBMHrJob(models.Model):
    _inherit = "hr.job"

    def unlink(self):
        if self.env.user.has_group('jbm_group_access_right_extended.custom_hr_user'):
            raise UserError(_('You have no access for the delete Job position.'))
        return super(JBMHrJob, self).unlink()


class JBMHrContract(models.Model):
    _inherit = "hr.contract"

    def unlink(self):
        if self.env.user.has_group('jbm_group_access_right_extended.custom_hr_user'):
            raise UserError(_('You have no access for the delete contract.'))
        return super(JBMHrContract, self).unlink()


class JBMHrEmployee(models.Model):
    _inherit = "hr.employee"

    def unlink(self):
        if self.env.user.has_group('jbm_group_access_right_extended.custom_hr_user'):
            raise UserError(_('You have no access for the delete employee.'))
        return super(JBMHrEmployee, self).unlink()


class JBMHrAttendance(models.Model):
    _inherit = "hr.attendance"

    def unlink(self):
        if self.env.user.has_group('jbm_group_access_right_extended.custom_hr_user'):
            raise UserError(_('You have no access for the delete Attendance.'))
        return super(JBMHrAttendance, self).unlink()


class JBMHrLeave(models.Model):
    _inherit = "hr.leave"

    def unlink(self):
        if self.env.user.has_group('jbm_group_access_right_extended.custom_hr_user'):
            raise UserError(_('You have no access for the delete leave.'))
        return super(JBMHrLeave, self).unlink()


class JBMHrAppraisal(models.Model):
    _inherit = "hr.appraisal"

    def unlink(self):
        if self.env.user.has_group('jbm_group_access_right_extended.custom_hr_user'):
            raise UserError(_('You have no access for the delete appraisal.'))
        return super(JBMHrAppraisal, self).unlink()
