from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InheritApprovalRequest(models.Model):
    _inherit = 'approval.request'

    @api.constrains('create_uid', 'date')
    def _check_max_approval_request(self):
        print('zerrrrrrrrrrrrrrrro')
        for approval in self:
            approvals = self.env['approval.request'].search([
                ('create_uid', '=', approval.create_uid.id),
                ('date', '=', approval.date)
            ])
            max_number_requests = int(self.env['ir.config_parameter'].sudo().get_param(
                'max_approval_request.max_number_requests', 0))
            print('len(approvals)::', len(approvals))
            print('approvals::', approvals)
            print('max_number_letter::', max_number_requests)
            if max_number_requests and approvals:
                if len(approvals) > max_number_requests:
                    raise ValidationError(_(f'Can not create more than {max_number_requests} letters'
                                            f', Contact to your manager for help !'))
