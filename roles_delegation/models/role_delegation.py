from odoo import models, fields, api, _
from datetime import date, timedelta
from odoo.exceptions import ValidationError


class RolesDelegation(models.Model):
    _name = 'roles.delegation'
    _rec_name = 'delegate_from'
    _description = "Roles Delegation"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    delegate_from = fields.Many2one('res.users', tracking=True)
    delegate_to = fields.Many2one('res.users', tracking=True)

    roles_ids = fields.Many2many('res.users.role')
    roles2_ids = fields.Many2many('res.users.role', relation="roles", compute="roles_ids_compute", store=True)
    date_from = fields.Date(tracking=True)
    date_to = fields.Date(tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approved', 'Approved'),
        ('reject', 'Rejected')], default='draft', tracking=True)

    leave_id = fields.Many2one('hr.leave')
    date_to_state = fields.Boolean(defult=False)

    extended_role_date = fields.Boolean()
    update_role_date = fields.Boolean()

    # @api.depends('roles_ids')
    # @api.onchange('delegate_from', 'delegate_to')
    # def roles_ids_onchange(self):
    #     # ['&amp;', ('state', '!=', 'rejected'), ('state', '!=', 'passed')]
    #     return {
    #         'domain': {
    #             'roles_ids': [('line_ids.user_id','=',self.delegate_from.id), ('line_ids.user_id','!=',self.delegate_to.id)],
    #         },
    #     }

    @api.constrains("date_to")
    def check_date(self):
        for rec in self:

            if rec.date_from and rec.date_to and rec.date_to < rec.date_from:
                raise ValidationError("'Date to' must be higher than 'Date from'")
    @api.onchange('delegate_from')
    def _clear_roles_ids_values(self):
        self.roles_ids = None
    @api.depends('delegate_from', 'delegate_to')
    def roles_ids_compute(self):
        for rec in self:
            if rec.delegate_from and rec.delegate_to:
                # roles_line = rec.env['res.users.role.line'].search(
                #     [('user_id', '=', rec.delegate_from.id),
                #      ('role_id', 'not in', rec.delegate_to.role_line_ids.mapped('role_id').ids)])
                roles_line = rec.sudo().env['res.users.role.line'].search([('user_id', '=', rec.delegate_from.id)])
                rec.roles2_ids = roles_line.mapped('role_id')

    def submit_state(self):
        roles = []
        temporary_roles = []
        out_dated_roles = []
        if self.roles2_ids and not self.roles_ids:
            raise ValidationError("Please Select a role to delegate")
        for role in self.roles_ids:
            if role in self.delegate_from.sudo().role_line_ids.filtered(lambda s: (s.date_to if s.date_to else self.date_to) < self.date_to).mapped('role_id'):
                temporary_roles.append(role.name)
                # raise ValidationError(f"this {role.name} role is a temporary role")

            elif role in self.delegate_from.sudo().role_line_ids.filtered(lambda s: (s.date_from if s.date_from else self.date_to) > self.date_to).mapped('role_id'):
                out_dated_roles.append(role.name)

            elif role in self.delegate_to.sudo().role_line_ids.filtered(lambda s: ((s.date_to if s.date_to else self.date_to) >= self.date_to) and (
                    (s.date_from if s.date_from else self.date_from) <= self.date_from)).mapped('role_id'):
                roles.append(role.name)

            elif (role in self.delegate_to.sudo().role_line_ids
                    .filtered(lambda s: ((s.date_to if s.date_to else self.date_to) >= self.date_from) and ((s.date_to if s.date_to else self.date_to) < self.date_to))
                    .mapped('role_id')):
                self.extended_role_date = True

        if roles:
            raise ValidationError(f"{self.delegate_to.name} already has this roles {roles}")
        if temporary_roles:
            raise ValidationError(f"this {temporary_roles} roles are temporary for employee {self.delegate_from.name} and it will end before {self.date_to}")
        if out_dated_roles:
            raise ValidationError(f"this {out_dated_roles} roles are temporary for employee {self.delegate_from.name}")
        self.state = 'submit'

    def _update_date_from_to(self, role):
        if (role in self.delegate_to.sudo().role_line_ids
                .filtered(lambda s: ((s.date_from if s.date_from else self.date_from) > self.date_from) and (
                (s.date_to if s.date_to else self.date_to) < self.date_to)).mapped('role_id')):
            return True
        else:
            return False

    def _update_date_to(self, role):
        if (role in self.delegate_to.sudo().role_line_ids
              .filtered(lambda s: ((s.date_to if s.date_to else self.date_to) >= self.date_from) and (
                (s.date_to if s.date_to else self.date_to) < self.date_to))
              .mapped('role_id')):
            return True
        else:
            return False

    def _update_date_from(self, role):
        if (role in self.delegate_to.sudo().role_line_ids
              .filtered(lambda s: ((s.date_from if s.date_from else self.date_from) > self.date_from) and (
                (s.date_from if s.date_from else self.date_from) <= self.date_to)).mapped('role_id')):
            return True
        else:
            return False

    def _check_date(self, role):
        rec = self.env['res.users.role.line'].search(
            [('role_id', '=', role.id), ('user_id', '=', self.delegate_to.id)])
        if rec:
            records = self.env['roles.delegation'].search(
                [('delegate_to', '=', self.delegate_to.id), ('state', '=', 'approved'),
                 ('update_role_date', '!=', True), ('date_from', '>', self.date_to)])
            if records:
                records.filtered(lambda s: s.roles_ids.filtered(lambda l: l.id == role.id))
                for record in records:
                    record.update_role_date = True
                rec.date_from = self.date_from
                rec.date_to = self.date_to
        else:
            self.sudo().env['res.users.role.line'].create(
                {'role_id': role.id, 'user_id': self.delegate_to.id, 'date_from': self.date_from,
                 'date_to': self.date_to})


    def roles_delegations(self):
        extended_date_role = []
        for role in self.roles_ids:
            if self._update_date_from_to(role):
                self.delegate_to.sudo().role_line_ids.filtered(lambda s: s.role_id == role).write(
                    {'date_from': self.date_from, 'date_to': self.date_to})

            elif self._update_date_to(role):
                self.delegate_to.sudo().role_line_ids.filtered(lambda s: s.role_id == role).write({'date_to': self.date_to})

            elif self._update_date_from(role):
                self.delegate_to.sudo().role_line_ids.filtered(lambda s: s.role_id == role).write({'date_from': self.date_from})

            elif (role in self.delegate_to.sudo().role_line_ids
                        .filtered(lambda s: (s.date_to if s.date_to else self.date_from) < self.date_from).mapped('role_id')):
                self.update_role_date = True

            # self.delegate_to.role_line_ids = [(0, 0, {'role_id': role.id})]
            else:
                self._check_date(role)
                self.sudo().env['res.users.role'].with_context(cron_job=True).cron_update_users()

                # self.env['res.users.role.line'].create({'role_id': role.id, 'user_id': self.delegate_to.id,'date_from': self.date_from, 'date_to': self.date_to})

    def cancel_roles_delegation(self):
        self.state = 'reject'
        for role in self.roles_ids:
            rec = self.env['res.users.role.line'].search(
                [('role_id', '=', role.id), ('user_id', '=', self.delegate_to.id)])

            if rec:
                records = self.env['roles.delegation'].search([('delegate_to', '=', self.delegate_to.id), ('state', '=', 'approved'), ('update_role_date', '!=', True)])
                if records:
                    records.filtered(lambda s: s.roles_ids.filtered(lambda l: l.id == role.id))
                    date_from = records[0].date_from
                    date_to = records[0].date_to
                    for record in records:
                        if role in record.roles_ids.mapped('role_id'):
                            if record.date_from < date_from:
                                date_from = record.date_from
                            if record.date_to > date_to:
                                date_to = record.date_to
                    rec.date_from = date_from
                    rec.date_to = date_to
                else:
                    self.env['res.users.role.line'].search(
                         [('role_id', '=', role.id), ('user_id', '=', self.delegate_to.id)]).unlink()

    def set_to_draft(self):
        self.state = 'draft'

    @api.model
    def delete_role_delegation(self):
        current_date = date.today()
        records = self.env['roles.delegation'].search([('date_to', '<', current_date), ('state', '=', 'approved')])
        for rec in records:
            for role in rec.roles_ids:
                rec.sudo().env['res.users.role.line'].search(
                    [('role_id', '=', role.id), ('user_id', '=', rec.delegate_to.id), ('date_to', '<=', current_date)]).unlink()
            rec.date_to_state = True

        records = self.env['roles.delegation'].search([('date_from', '=', current_date), ('state', '=', 'approved')])
        for rec in records:
            for role in rec.roles_ids:
                if rec.update_role_date:
                    if (role in rec.delegate_to.sudo().role_line_ids
                            .filtered(lambda s: ((s.date_from if s.date_from else rec.date_from) > rec.date_from) and (
                                (s.date_to if s.date_to else rec.date_to) < rec.date_to)).mapped('role_id')):
                        rec.delegate_to.role_line_ids.sudo().filtered(lambda s: s.role_id == role).write(
                            {'date_from': rec.date_from, 'date_to': rec.date_to})

                    elif (role in rec.delegate_to.sudo().role_line_ids
                            .filtered(lambda s: ((s.date_from if s.date_from else rec.date_from) <= rec.date_from) and (
                                (s.date_to if s.date_to else rec.date_to) < rec.date_to)).mapped('role_id')):
                        rec.delegate_to.sudo().role_line_ids.filtered(lambda s: s.role_id == role).write(
                            {'date_to': rec.date_to})

                    elif (role in rec.delegate_to.sudo().role_line_ids
                            .filtered(lambda s: ((s.date_from if s.date_from else rec.date_from) > rec.date_from) and (
                                (s.date_to if s.date_to else rec.date_to) >= rec.date_to)).mapped('role_id')):
                        rec.delegate_to.sudo().role_line_ids.filtered(lambda s: s.role_id == role).write(
                            {'date_from': rec.date_from})

                    elif (role in rec.delegate_to.sudo().role_line_ids
                            .filtered(lambda s: (s.date_to if s.date_to else rec.date_to) >= rec.date_to).mapped('role_id')):
                        continue
                    else:
                        self.create_role(rec, role)
            rec.update_role_date = False

    def create_role(self, rec, role):
        self.sudo().env['res.users.role.line'].create({'role_id': role.id, 'user_id': rec.delegate_to.id,
                                                'date_from': rec.date_from, 'date_to': rec.date_to})
        self.sudo().env['res.users.role'].with_context(cron_job=True).cron_update_users()

    def unlink(self):
        for rec in self:
            if rec.state == 'approved':
                raise ValidationError("You can't delete an approved delegation")
            elif rec.state == 'reject':
                raise ValidationError("You can't delete a rejected delegation")

        return super(RolesDelegation, self).unlink()


class RoleDelegationApp(models.Model):
    _name = 'roles.delegation'
    _inherit = ['roles.delegation', 'dynamic.approval.mixin', 'mail.thread', 'mail.activity.mixin']
    _state_field = "state"
    _state_from = ['submit']
    _state_to = ['approved']


    def _action_final_approve(self):
        res = super(RoleDelegationApp, self)._action_final_approve()
        activity = self._get_user_approval_activities()
        if activity:
            activity.action_feedback()
        if self.activity_ids:
            self.activity_ids.action_feedback()
        return res

    def _action_final_approve_activity(self):
        records = self.env['roles.delegation'].search([
            ('state', '=', 'approved')
        ])
        if records:
            for record in records:
                if record.activity_ids:
                    record.activity_ids.action_feedback()
                # activity = record._get_user_approval_activities()
                # if activity:
                #     activity.action_feedback()


