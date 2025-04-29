from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class HrPayslipRunCustom(models.Model):
    _inherit = "hr.payslip.run"

    hide_generate_payslip = fields.Boolean(string="Hide Generate Payslip", compute="compute_hide_generate_payslip")

    def compute_hide_generate_payslip(self):
        for record in self:
            record.hide_generate_payslip = False
            if self.env.user.has_group('jbm_group_access_right_extended.custom_accountant_role_manager'):
                record.hide_generate_payslip = True
            elif self.env.user.has_group('jbm_group_access_right_extended.custom_accounting_auditor_manager'):
                record.hide_generate_payslip = True
            elif self.env.user.has_group('jbm_group_access_right_extended.custom_accounting_manager'):
                record.hide_generate_payslip = True

    # @api.model
    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     payslips = super(HrPayslipRunCustom, self).search(args, offset=offset, limit=limit, order=order, count=count)
    #     if self.env.user.has_group('jbm_group_access_right_extended.group_payroll_outsourced'):
    #         slip_ids = payslips.mapped('slip_ids').filtered(lambda s: s.employee_type == 'fos_employee')
    #         payslips = payslips.filtered(lambda s: s.slip_ids in slip_ids)
    #     return payslips

    def unlink(self):
        if self.env.user.has_group('jbm_group_access_right_extended.custom_hr_user'):
            raise UserError(_('You have no access for the delete record.'))
        return super(HrPayslipRunCustom, self).unlink()


class JBMHrPayslipCustom(models.Model):
    _inherit = "hr.payslip"

    def unlink(self):
        if self.env.user.has_group('jbm_group_access_right_extended.custom_hr_user'):
            raise UserError(_('You have no access for the delete record.'))
        return super(JBMHrPayslipCustom, self).unlink()
