# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HrLeaveConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    alias_prefix = fields.Char(string='Default Alias Name for Leave', help='Default Alias Name for Leave')
    alias_domain = fields.Char(string='Alias Domain', help='Default Alias Domain for Leave',
                               default=lambda self: self.env["ir.config_parameter"].get_param("mail.catchall.domain"))
    max_days_to_approve = fields.Integer(string='Max Days To Approve', help='Max Days To Remove Violation Hours from attendance')


    # @api.constrains('max_days_to_approve')
    # def max_days_constrain(self):
    #     if self.max_days_to_approve > 4:
    #         raise ValidationError(_('Max Days Can not be more than 4 Days'))

    def set_values(self):
        super(HrLeaveConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].set_param
        set_param('alias_prefix', self.alias_prefix)
        set_param('alias_domain', self.alias_domain ),
        set_param('max_days_to_approve', self.max_days_to_approve ),


    @api.model
    def get_values(self):
        res = super(HrLeaveConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            alias_prefix=get_param('alias_prefix', default=''),
            alias_domain=get_param('alias_domain', default=''),
            max_days_to_approve=get_param('max_days_to_approve', default=''),
        )
        return res

