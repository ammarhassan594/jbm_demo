from odoo import models, fields, _
from odoo.exceptions import UserError


class DynamicApprovalRole(models.Model):
    _name = 'dynamic.approval.role'
    _description = 'Approval Role'
    _rec_name = 'name'

    short_code = fields.Char(
        required=True,
    )
    name = fields.Char(
        required=True,
    )
    active = fields.Boolean(
        default=True,
    )

    def get_approval_user_role(self, approval, model, res):
        """ return approval user
            this function can be override to add custom users based on each model
        """
        user = self.env['res.users']
        if res.role_distribution_id:
            role_id = res.role_distribution_id.line_ids.filtered(lambda line: line.role_id.id == self.id)
            msg = _('No user assigned to role %s in approval %s!') % (self.id, approval.display_name)
            if role_id:
                # user = role_id.get_approve_user(approval, model, res)
                users = role_id.get_approve_user(approval, model, res)
                # if user:
                #     return user
                if users:
                    return users
                else:
                    raise UserError(msg)
            else:
                raise UserError(msg)
        return user
