from odoo import models, fields, api, _


class ResUsersRoleInherit(models.Model):
    _inherit = "res.users.role"

    menu_items_ids = fields.Many2many('ir.ui.menu', string="Menu", store=True,
                                      help='Select menu items that needs to be '
                                           'hidden to this user ')


class ResUsers(models.Model):
    _inherit = 'res.users'

    hide_menu_ids = fields.Many2many('ir.ui.menu', string="Menu", store=True,
                                     help='Select menu items that needs to be '
                                          'hidden to this user', compute="onchange_role_user")

    @api.onchange('role_line_ids', 'role_ids', 'role_ids.menu_items_ids')
    @api.depends('role_line_ids', 'role_ids', 'role_ids.menu_items_ids')
    def onchange_role_user(self):
        for rec in self:
            rec.hide_menu_ids = [(6, 0, rec.role_line_ids.mapped('role_id').mapped('menu_items_ids').ids)]
