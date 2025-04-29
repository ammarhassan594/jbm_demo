import pytz
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, models, fields


class DynamicApprovalRequest(models.Model):
    _name = 'dynamic.approval.request'
    _description = 'Approval Request'
    _order = 'sequence, id'

    name = fields.Char(compute="_compute_name", store=True)
    res_model = fields.Char(
        string='Related Document Model',
        required=True,
    )
    res_id = fields.Many2oneReference(
        string='Related Document ID',
        index=True,
        required=True,
        model_field='res_model'
    )
    res_name = fields.Char(
        string='Document Name',
        compute='_compute_res_name',
        compute_sudo=True,
        store=True,
        help="Display name of the related document.",
    )
    sequence = fields.Integer(
        string='Sequence',
        default=1,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Approver User',
    )
    user_ids = fields.Many2many(
        comodel_name='res.users',
        string='Approver Users',
        required=True,
    )
    group_id = fields.Many2one(
        comodel_name='res.groups',
        string='Approver Group',
    )
    approve_date = fields.Datetime(
        string='Approved Date',
    )
    status = fields.Selection(
        selection=[
            ('new', 'New'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('recall', 'recall')
        ],
        default="new",
    )
    approved_by = fields.Many2one(
        comodel_name='res.users',
    )
    approved_by_users = fields.Many2many(
        'res.users',
        'users_approver_rel',
        string='Approved By'
    )
    reject_date = fields.Datetime(
        string='Reject Date',
    )
    reject_reason = fields.Char()
    approve_note = fields.Char()
    dynamic_approval_id = fields.Many2one(
        comodel_name='dynamic.approval',
        copy=False,
    )
    dynamic_approve_level_id = fields.Many2one(
        comodel_name='dynamic.approval.level',
        copy=False,
    )
    last_reminder_date = fields.Datetime()

    # @api.depends('user_id', 'group_id')
    @api.depends('user_ids', 'group_id')
    def _compute_name(self):
        for req in self:
            name = ""
            # if req.user_id:
            if req.user_ids:
                # name += "User:{}-".format(req.user_id.name)
                name += "User: "
                for each_user in req.user_ids:
                    name += "{}-".format(each_user.name)
            if req.group_id:
                name += "Group:{}".format(req.group_id.name)
            req.name = "Approval By [{}]".format(name)

    @api.depends('res_model', 'res_id')
    def _compute_res_name(self):
        """ appear display name of related document """
        for record in self:
            record.res_name = record.res_model and self.env[record.res_model].browse(record.res_id).display_name

    def get_approve_user(self):
        """ :return users that need to approve """
        users = self.env['res.users']
        for record in self:
            if record.user_ids:
                users |= record.user_ids
            if record.group_id:
                users |= record.group_id.users
        return users

    def action_send_reminder_email(self):
        """ send email to user for each request """
        for record in self:
            cal_obj = record.env['resource.calendar']
            calendar_id = record.env['ir.config_parameter'].sudo().get_param(
                'base_dynamic_approval.email_resource_calendar_id', 0)
            calendar_id = cal_obj.search([('id', '=', calendar_id)])

            if record.dynamic_approval_id and record.dynamic_approval_id.reminder_pending_approver_email_template_id:
                for user in record.get_approve_user():
                    timezone = False
                    if calendar_id and calendar_id.tz:
                        timezone = pytz.timezone(calendar_id.tz)
                    usertime = datetime.now(timezone) if timezone else datetime.now()
                    intersect = calendar_id._time_within(usertime)
                    if not intersect:
                        continue
                    email_values = {'email_to': user.email, 'email_from': self.env.user.email}
                    record.dynamic_approval_id.reminder_pending_approver_email_template_id.with_context(
                        name_to=user.name, user_lang=user.lang).send_mail(
                        self.res_id, email_values=email_values, force_send=True)

    @api.model
    def _cron_send_reminder_to_approve(self):
        """ cron job used to send email template to approve """
        approve_requests = self.search([
            ('status', '=', 'pending'),
            ('dynamic_approval_id.reminder_pending_approver_email_template_id', '!=', False),
        ])
        now = fields.Datetime.now()
        for approve_request in approve_requests:
            if approve_request.dynamic_approval_id.reminder_period_to_approve:
                delay_period = approve_request.dynamic_approval_id.reminder_period_to_approve
                request_end_date = approve_request.last_reminder_date or approve_request.write_date
                deadline_date = request_end_date + timedelta(hours=delay_period)
                if deadline_date <= now:
                    approve_request.action_send_reminder_email()
                    approve_request.last_reminder_date = now

    @api.model
    def _cron_automatic_approve(self):
        requests_pending = self.search([('status', '=', 'pending')])
        today = datetime.now()
        for req in requests_pending:
            if req.dynamic_approve_level_id.automatic_approval:
                number_of_hours_approve = int(
                    self.env['ir.config_parameter'].sudo().get_param('base_dynamic_approval.number_of_hours'))
                requests_approval = self.search([
                    ('res_id', '=', req.res_id), ('status', '=', 'approved')], order='id desc', limit=1)
                if requests_approval:
                    if relativedelta(today, requests_approval.approve_date).hours > number_of_hours_approve:
                        req.update({
                            'status': 'approved',
                            'approve_date': today,
                            'approved_by_users': [(6, 0, req.user_ids.ids)],
                            'approve_note': 'Approved automatic using cron'
                        })
                        req.create_or_done_scheduled_activity()
                        # req.change_new_to_pending(req.res_id)
                else:
                    if relativedelta(today, req.create_date).hours > number_of_hours_approve:
                        req.update({
                            'status': 'approved',
                            'approve_date': today,
                            'approved_by_users': [(6, 0, req.user_ids.ids)],
                            'approve_note': 'Approved automatic using cron'
                        })
                        req.create_or_done_scheduled_activity()
                        # req.change_new_to_pending(req.res_id)

    def create_or_done_scheduled_activity(self):
        if self.res_id and self.res_model == 'hr.leave':
            leave_record = self.env[self.res_model].browse(self.res_id)
            activity = leave_record._get_user_approval_activities()
            if activity:
                activity.action_feedback()
            else:
                msg = 'Approved Leave request from cron'
                leave_record.message_post(body=msg)
            new_approve_requests = \
                leave_record.dynamic_approve_request_ids.filtered(
                    lambda approver: approver.status == 'new')
            if new_approve_requests:
                next_waiting_approval = new_approve_requests.sorted(lambda x: (x.sequence, x.id))[0]
                next_waiting_approval.status = 'pending'
                if next_waiting_approval.get_approve_user():
                    user = next_waiting_approval.get_approve_user()[0]
                    leave_record._notify_next_approval_request(leave_record.dynamic_approval_id, user)
            else:
                leave_record._action_final_approve()

    def change_new_to_pending(self, res_id):
        requests_new = self.search([('res_id', '=', res_id), ('status', '=', 'new')], limit=1)
        if requests_new:
            requests_new.update({'status': 'pending'})

    def get_date_deadline_request(self):
        """Return deadline of request to create an active with value of deadline
            Every request related to level so get value of in days field on level
        """
        self.ensure_one()
        return self.dynamic_approve_level_id.in_days
