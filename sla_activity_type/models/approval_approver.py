from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


class InheritApprovalApprover(models.Model):
    _inherit = 'approval.approver'

    activity_type_id = fields.Many2one('mail.activity.type', string="Activity Type", compute='_compute_activity_type',
                                       store=True, readonly=False)

    @api.depends('user_id', 'request_id', 'request_id.category_id')
    def _compute_activity_type(self):
        for rec in self:
            if rec.user_id and rec.request_id and rec.request_id.category_id:
                related_category_approver = rec.request_id.category_id.approver_ids.filtered(
                    lambda user_to_approve: user_to_approve.user_id == rec.user_id)
                if related_category_approver:
                    rec.activity_type_id = related_category_approver[0].activity_type_id.id

    def _create_activity(self):
        for approver in self:
            date_deadline = (fields.Date.today() + relativedelta(days=approver.date_deadline_after))
            activity_type = approver.activity_type_id
            if activity_type:
                approver.request_id.activity_schedule(
                    activity_type_id=activity_type.id,
                    date_deadline=date_deadline,
                    user_id=approver.user_id.id)
            if not activity_type:
                approver.request_id.activity_schedule(
                    "approvals.mail_activity_data_approval",
                    date_deadline=date_deadline,
                    user_id=approver.user_id.id)
