from odoo import models, fields


class RoleDistribution(models.Model):
    _name = 'role.distribution'
    _description = 'Role Distribution'
    _rec_name = 'name'

    name = fields.Char(required=True)
    line_ids = fields.One2many(
        comodel_name="role.distribution.line",
        inverse_name="distribution_id",
    )
    description = fields.Text()
    related_to = fields.Selection([('leave', 'Leave'), ('manpower', 'Manpower Transfer')], string="Scope")


class RoleDistributionLine(models.Model):
    _name = 'role.distribution.line'
    _description = 'Role Distribution Line'
    _rec_name = 'role_id'

    distribution_id = fields.Many2one(
        comodel_name='role.distribution',
        ondelete='cascade',
    )
    role_id = fields.Many2one(
        comodel_name='dynamic.approval.role',
        required=True,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Default User',
        # required=True,
    )
    user_ids = fields.Many2many(
        comodel_name='res.users',
        string='Default Users',
        required=True,
    )
    automatic_approval = fields.Boolean(string='Applicable for Dynamic Approval', default=True)

    _sql_constraints = [
        (
            'role_distribution_uniq',
            'unique(distribution_id,role_id)',
            'Role must be unique per Distribution Record !'
        ),
    ]

    def get_approve_user(self, approval=False, model=False, res=False):
        """
        return user need approve.
        you can override to add custom user based on requirement
        :param obj approval: configuration object
        :param string model: technical name of model ex 'sale.order'
        :param  obj res: recordset of object ex 'sale.order(1)'
        """
        self.ensure_one()
        # return self.user_id
        return self.user_ids
