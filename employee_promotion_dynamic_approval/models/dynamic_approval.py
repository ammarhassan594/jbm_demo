from odoo import models, fields, api


class InheritDynamicApproval(models.Model):
    _inherit = 'dynamic.approval'

    @api.model
    def _get_approval_validation_model_names(self):
        res = super(InheritDynamicApproval, self)._get_approval_validation_model_names()
        res.append('employee.promotion')
        return res
