import ast
from odoo import api, fields, models


class HrLeaveResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_leave_ids = fields.Many2many(comodel_name='hr.leave.type',
                                       string='Allow Leaves For Automatic Approval')
    number_of_hours_approval = fields.Integer(string="Automatically Approve Hours",
                                              config_parameter='ebs_hr_leave_custom.number_of_hours_approval')

    @api.model
    def get_values(self):
        res = super(HrLeaveResConfigSettings, self).get_values()
        allow_leave_value = self.env['ir.config_parameter'].sudo().get_param(
            'ebs_hr_leave_custom.allow_leave_ids')
        print("Get Allow Leaves ", allow_leave_value)
        if allow_leave_value:
            res.update(
                allow_leave_ids=[(6, 0, ast.literal_eval(allow_leave_value))]
            )
        else:
            res.update(
                allow_leave_ids=[(6, 0, [])]
            )
        return res

    def set_values(self):
        super(HrLeaveResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        print("In Set All Values: ", self.allow_leave_ids)
        allow_leave_ids = self.allow_leave_ids.ids or False
        print("Set Values ", allow_leave_ids)
        param.set_param(
            'ebs_hr_leave_custom.allow_leave_ids', allow_leave_ids)
