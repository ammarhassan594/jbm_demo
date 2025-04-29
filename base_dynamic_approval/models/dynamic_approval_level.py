from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class DynamicApprovalLevel(models.Model):
    _name = 'dynamic.approval.level'
    _description = 'Approval level'
    _order = 'sequence, id'

    approval_id = fields.Many2one(
        comodel_name='dynamic.approval',
    )

    sequence = fields.Integer(
        default=1,
    )

    validate_by = fields.Selection([
        ('by_user', 'User'),
        ('by_role', 'role'),
        ('by_group', 'Group'),
        ('by_fields', 'Select fields in related record'),
    ], string='Approve By')

    field_ids = fields.Many2many(comodel_name="ir.model.fields", string="Reviewer fields",
                                 domain="[('id', 'in', valid_field_ids)]")

    valid_field_ids = fields.One2many(
        comodel_name="ir.model.fields",
        compute="_compute_domain_field",
    )

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Approver User',
    )
    group_id = fields.Many2one(
        comodel_name='res.groups',
        string='Approver Group',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        readonly=True,
        related='approval_id.company_id',
        store=True,
    )
    automatic_approval = fields.Boolean(string='Applicable for Dynamic Approval', default=True)

    can_edit = fields.Boolean(string='Applicable for Edit Approval', default=True)

    in_days = fields.Integer(string='Time In Days', default=0)

    def _get_approval_user(self, model, res):
        """ allow to override to select user in other modules """
        self.ensure_one()
        return self.user_id

    def prepare_approval_request_values(self, model, res):
        """ return values for create approval request """
        vals = {}
        self.ensure_one()
        group, users = None, None
        if self.validate_by == 'by_group':
            group = self.group_id if self.group_id else False
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
                'dynamic_approve_level_id': self.id,
                'dynamic_approval_id': self.approval_id.id,
            }

        raise UserError(_("System can`t find user for user / group for approval type '%s' level sequence number'%s'.") %
                        (self.approval_id.display_name, self.sequence))

    def _get_approver_source_field(self):
        """
         helper function to return list of fields need to check
         this function can be inherit to add extra fields
        """
        return ['user_id', 'group_id', 'field_ids']

    def _check_is_approver_source_chosen(self):
        """ return true if at least user_id or group_id has data """
        for record in self:
            is_approver_source_chosen = False
            if any(getattr(record, field) for field in self._get_approver_source_field()):
                is_approver_source_chosen = True
            if not is_approver_source_chosen:
                raise ValidationError(
                    _('Please choose source of users will approve for level sequence %s') % record.sequence)

    # compute functions
    @api.depends('approval_id')
    def _compute_domain_field(self):
        for record in self:
            record.valid_field_ids = self.env["ir.model.fields"].search(
                [("model", "=", record.approval_id.model), ("relation", "=", "res.users")]
            )

    # ORM functions
    @api.model
    def create(self, vals_list):
        """ check for approvers source fields """
        rec = super().create(vals_list)
        rec._check_is_approver_source_chosen()
        return rec

    def write(self, vals):
        """ check for approvers source fields """
        res = super().write(vals)
        self._check_is_approver_source_chosen()
        return res
