from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class ApprovalRequestCustom(models.Model):
    _inherit = "approval.request"

    def get_read_only_approval(self):
        for rec in self:
            child_employees = self.env['hr.employee'].search(
                [('parent_id', 'child_of', self.env.user.employee_ids.ids)])
            if rec.request_status == 'new' and rec.request_owner_id.id == self.env.user.id:
                rec.read_only_approval = False
            elif rec.request_status != 'new' and (self.env.user.id in rec.approver_ids.filtered(
                    lambda x: x.status == 'pending').user_id.ids or self.env.user.id in rec.approver_ids.filtered(
                lambda x: x.status == 'pending').group_id.users.ids):
                rec.read_only_approval = False
            elif rec.request_owner_id.employee_ids.filtered(lambda s: s in child_employees):
                rec.read_only_approval = False
            else:
                rec.read_only_approval = True

    def unlink(self):
        if self.env.user.has_group('jbm_group_access_right_extended.custom_accountant_role_manager'):
            raise UserError(_('You have no access for the delete record.'))
        elif self.env.user.has_group('jbm_group_access_right_extended.custom_accounting_auditor_manager'):
            raise UserError(_('You have no access for the delete record.'))
        elif self.env.user.has_group('jbm_group_access_right_extended.custom_accounting_manager'):
            raise UserError(_('You have no access for the delete record.'))
        elif self.env.user.has_group('jbm_group_access_right_extended.procurement_user_role'):
            raise UserError(_('You have no access for the delete record.'))
        elif self.env.user.has_group('jbm_group_access_right_extended.custom_procurement_manager'):
            raise UserError(_('You have no access for the delete record.'))
        elif self.env.user.has_group('jbm_group_access_right_extended.custom_committee_user'):
            raise UserError(_('You have no access for the delete record.'))
        elif self.env.user.has_group('jbm_group_access_right_extended.custom_hr_user'):
            raise UserError(_('You have no access for the delete record.'))
        return super(ApprovalRequestCustom, self).unlink()


class ApprovalCategoryCustom(models.Model):
    _inherit = "approval.category"

    def unlink(self):
        if self.env.user.has_group('jbm_group_access_right_extended.custom_hr_user'):
            raise UserError(_('You have no access for the delete record.'))
        return super(ApprovalCategoryCustom, self).unlink()


class JBMAccountAccountCustom(models.Model):
    _inherit = "account.account"

    def unlink(self):
        if self.env.user.has_group('jbm_group_access_right_extended.custom_accountant_role_manager'):
            raise UserError(_('You have no access for the delete record.'))
        elif self.env.user.has_group('jbm_group_access_right_extended.custom_accounting_auditor_manager'):
            raise UserError(_('You have no access for the delete record.'))
        return super(JBMAccountAccountCustom, self).unlink()


class JBMCrossoveredBudgetCustom(models.Model):
    _inherit = "crossovered.budget"

    def unlink(self):
        if self.env.user.has_group('jbm_group_access_right_extended.custom_accountant_role_manager'):
            raise UserError(_('You have no access for the delete record.'))
        elif self.env.user.has_group('jbm_group_access_right_extended.custom_accounting_auditor_manager'):
            raise UserError(_('You have no access for the delete record.'))
        elif self.env.user.has_group('jbm_group_access_right_extended.custom_committee_user'):
            raise UserError(_('You have no access for the delete record.'))
        return super(JBMCrossoveredBudgetCustom, self).unlink()


class JBMAccountPaymentCustom(models.Model):
    _inherit = "account.payment"

    def unlink(self):
        if self.env.user.has_group('jbm_group_access_right_extended.custom_accountant_role_manager'):
            raise UserError(_('You have no access for the delete record.'))
        elif self.env.user.has_group('jbm_group_access_right_extended.custom_accounting_auditor_manager'):
            raise UserError(_('You have no access for the delete record.'))
        return super(JBMAccountPaymentCustom, self).unlink()
