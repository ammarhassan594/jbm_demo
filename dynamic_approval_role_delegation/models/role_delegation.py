from odoo import models, fields, api, _


class InheritRoleDelegation(models.Model):
    _name = 'roles.delegation'
    _inherit = ['roles.delegation', 'dynamic.approval.mixin', 'mail.thread', 'mail.activity.mixin']
    _state_field = "state"
    _state_from = ['submit']
    _state_to = ['approved']


    def _action_final_approve(self):
        res = super(InheritRoleDelegation, self)._action_final_approve()
        if self._name == 'roles.delegation':
            employees = self.env['hr.employee'].sudo().search([
                '|',
                ('parent_id', '=', self.delegate_from.id),
                ('leave_manager_id', '=', self.delegate_from.id)
            ])
            if employees:
                for employee in employees:
                    employee.write({
                        'role_delegation_ids': [(4, self.id)]
                    })
        return res