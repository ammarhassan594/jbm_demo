from odoo import models, fields, api, _


class InheritAllowanceRequest(models.Model):
    _inherit = 'allowance.request'

    @api.model
    def create(self, vals):
        object = super(InheritAllowanceRequest, self).create(vals)
        if 'allowance_type' in vals:
            allowance_type = self.env['allowance.type'].search([
                ('id', '=', vals['allowance_type'])
            ])
            is_matched = []
            if allowance_type and allowance_type.condition_ids:
                for condition in allowance_type.condition_ids:
                    print('test test:::', condition.is_condition_matched(res=object))
                    if condition.is_condition_matched(res=object):
                        is_matched = condition
                        break
            if not is_matched:
                raise ValueError('NOT Matched Allowance Type')
        return object

    # @api.onchange('allowance_type')
    # @api.depends('allowance_type')
    # def validate_allowance_type(self):
    #     for record in self:
    #         if record.allowance_type:
    #             is_matched = []
    #             if record.allowance_type and record.allowance_type.condition_ids:
    #                 for condition in record.allowance_type.condition_ids:
    #                     if condition.is_condition_matched(res=record):
    #                         is_matched = condition
    #                         break
    #             if not is_matched:
    #                 raise ValueError('NOT Matched Allowance Type')
