from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
import json


class InheritHrLeave(models.Model):
    _inherit = 'hr.leave'

    replacement_employee = fields.Boolean(string="Replacement Employee", related='holiday_status_id.replacement_employee')
    replacement_employee_id = fields.Many2one('hr.employee', string="Replacement Employee")
    replacement_employee_domain = fields.Char('Employee Replacement resource Domain',
                                                       compute="_get_replacement_employee_domain")
    replacement_resource_id = fields.Many2one('resource.resource', 'Replacement Employee')

    replacement_resource_domain = fields.Char('Employee Replacement resource Domain',
                                              compute="_get_replacement_resource_domain")

    role_delegation_id = fields.Many2one('roles.delegation')

    roles_delegate = fields.Boolean()

    @api.onchange('roles_delegate', 'replacement_resource_id')
    def _replacement_onchange(self):
        res = {}
        if self.roles_delegate:
            if self.replacement_resource_id.user_id and self.employee_ids.user_id:
                for role in self.employee_ids.user_id.sudo().role_line_ids.mapped('role_id'):
                    if role in self.employee_ids.user_id.sudo().role_line_ids.filtered(lambda s: (s.date_to if s.date_to else self.request_date_to) > self.request_date_to).mapped('role_id'):
                        res['warning'] = {'title': _('Warning'), 'message': _(
                             f'{self.employee_ids.name} and {self.replacement_resource_id.name} have the same roles')}
                        break
                    if role in self.replacement_resource_id.user_id.sudo().role_line_ids.filtered(lambda s: (s.date_to if s.date_to else self.request_date_to) >= self.request_date_to).mapped('role_id'):
                        res['warning'] = {'title': _('Warning'), 'message': _(
                            f'"{self.employee_ids.name}" and "{self.replacement_resource_id.name}" have the same roles')}
                        break
            return res


    @api.depends('employee_id', 'request_date_to', 'request_date_from')
    def _get_replacement_resource_domain(self):
        for rec in self:
            if rec.employee_id:
                ids = [rec.employee_id.resource_id.id]
                if all((rec.request_date_to, rec.request_date_from)):
                    leaves = rec.env['hr.leave'].sudo().search(
                        [('request_date_from', '<=', rec.request_date_to),
                         ('request_date_to', '>=', rec.request_date_from)])
                    if leaves:
                        ids.extend(leaves.mapped('employee_id').mapped('resource_id').ids)
                resources = rec.env['resource.resource'].sudo().search([])
                resources = [x for x in resources.ids if x not in ids]
                rec.replacement_resource_domain = json.dumps([('id', 'in', resources)])
            else:
                rec.replacement_resource_domain = json.dumps([('id', '=', False)])

    @api.depends('employee_id')
    def _get_replacement_employee_domain(self):
        for rec in self:
            if rec.employee_id:
                ids = []
                employees = self.env['hr.employee'].sudo().search([
                    ('department_id', '=', rec.employee_id.department_id.id),
                    ('id', '!=', rec.employee_id.id)
                ])
                ids = employees.ids
                rec.replacement_employee_domain = json.dumps([('id', 'in', ids)])
                # ids = [rec.employee_id.id]
                # if all((rec.request_date_to, rec.request_date_from)):
                #     leaves = rec.env['hr.leave'].sudo().search(
                #         [('request_date_from', '<=', rec.request_date_to),
                #          ('request_date_to', '>=', rec.request_date_from)])
                #     if leaves:
                #         ids.extend(leaves.mapped('employee_id').ids)
                #         print('leaves', leaves)
                # rec.replacement_employee_domain = json.dumps([('id', 'not in', ids)])

            else:
                rec.replacement_employee_domain = json.dumps([('id', '=', False)])

    def _automatic_role_delegation(self):
        if self.roles_delegate:
            if self.replacement_resource_id.user_id and self.employee_ids.user_id:
                for role in self.employee_ids.user_id.sudo().role_line_ids.mapped('role_id'):
                    if role in self.employee_ids.user_id.sudo().role_line_ids.filtered(lambda s: (s.date_to if s.date_to else self.request_date_to) > self.request_date_to).mapped('role_id'):
                        continue
                    if role in self.replacement_resource_id.user_id.sudo().role_line_ids.filtered(lambda s: (s.date_to if s.date_to else self.request_date_to) >= self.request_date_to).mapped('role_id'):
                        continue
                    else:
                        role = self.env['roles.delegation'].create({
                            'delegate_from': self.employee_ids.user_id.id,
                            'delegate_to': self.replacement_resource_id.user_id.id,
                            'date_from': self.request_date_from,
                            'date_to': self.request_date_to,
                            'leave_id': self.id,
                        })
                        self.role_delegation_id = role
                        self._mail_activity()
                        break

    def _mail_activity(self):
        for record in self:
            ref = record.env.ref
            users = self.sudo().env.ref('base.group_erp_manager').users.ids
            for user in users:
                todos = {
                    'res_id': record.role_delegation_id.id,
                    'res_model_id': self.sudo().env['ir.model'].search([('model', '=', 'roles.delegation')]).id,
                    'user_id': user,
                    'summary': 'الإجراء اللازم',
                    'note': f'للتكرم بمراجعة بريدك الإلكتروني.',
                    'activity_type_id': ref('roles_delegation.mail_activity_type_roles_delegation').id,
                    # 'date_deadline': datetime.date.today(),
                }
                record.env['mail.activity'].sudo().create(todos)

    def action_approve(self):
        res = super(InheritHrLeave, self).action_approve()
        self._automatic_role_delegation()
        return res

    def action_refuse(self):
        res = super(InheritHrLeave, self).action_refuse()
        # self.role_delegation_id.state = 'reject'
        if self.role_delegation_id:
            self.role_delegation_id.cancel_roles_delegation()
        return res

