from odoo import models, fields, api, _


class ContractLeaveType(models.Model):
    _name = 'contract.leave.type'
    _rec_name = "leave_type"

    leave_type = fields.Many2one(comodel_name="hr.leave.type", string="Leave Type", required=True)
    days = fields.Float(required=True)
    contract_id = fields.Many2one('hr.contract', 'Contract', readonly=True, ondelete="cascade")
    allocation_id = fields.Many2one('hr.leave.allocation', 'Allocation', ondelete="cascade", readonly=True)
    payscale_id = fields.Many2one('employee.payscale', 'Pay Scale', ondelete="cascade", readonly=True)

    # @api.onchange('leave_type')
    # def _get_default_number_of_days(self):
    #     for rec in self:
    #         if rec.leave_type:
    #             if rec.leave_type.default_days and not rec.days:
    #                 rec.days = rec.leave_type.default_days
