from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime



class InheritDynamicApprovalLevel(models.Model):
    _inherit = 'dynamic.approval.level'


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



    def prepare_approval_request_values(self, model, res):
        """ return values for create approval request """
        role_delegation = ''
        vals = {}
        self.ensure_one()
        group, users = None, None
        if self.validate_by == 'by_group':
            group = self.group_id if self.group_id else False
            if group and group.users:
                for user_line in group.users:
                    delegation_user = self._check_role_delegation(user_line)
                    if delegation_user:
                        delegation_user.write({'groups_id': [(4, group.id)]})
                        role_delegation = 'Role Delegation'


        # user = self._get_approval_user(model, res)
        elif self.validate_by in ['by_user', 'by_role']:
            users = self._get_approval_user(model, res)

        elif self.validate_by == 'by_fields':
            if self.approval_id.model == model:
                resource = self.env[self.approval_id.model].browse(res)
                for field in self.field_ids:
                    reviewer_user = getattr(res, field.name, False)
                    if users:
                        users |= reviewer_user
                    else:
                        users = reviewer_user

                    if not reviewer_user or not reviewer_user._name == "res.users":
                        raise ValidationError(_("There are no res.users in the selected field"))
        if users:
            for user in users:
                delegation_user = self._check_role_delegation(user)
                if delegation_user:
                    users = users.filtered(lambda u: u.id != user.id)
                    users = users | delegation_user
                    role_delegation = "Role Delegation"

        # if group or user:
        if group or users:
            return {
                'res_model': model,
                'res_id': res.id,
                'sequence': self.sequence,
                # 'user_id': user.id if user else False,
                'user_ids': [(6, 0, users.ids)] if users else False,
                'group_id': group.id if group else False,
                'status': 'new',
                'approve_date': False,
                'approved_by': False,
                'approve_note': role_delegation,
                'dynamic_approve_level_id': self.id,
                'dynamic_approval_id': self.approval_id.id,
            }

        raise UserError(_("System can`t find user for user / group for approval type '%s' level sequence number'%s'.") %
                        (self.approval_id.display_name, self.sequence))