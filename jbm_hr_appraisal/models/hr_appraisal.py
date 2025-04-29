import logging
import datetime

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.addons.hr_appraisal.models.hr_appraisal import HrAppraisal

_logger = logging.getLogger(__name__)


class InheritHrAppraisal(models.Model):
    _inherit = 'hr.appraisal'

    appraisal_batch_id = fields.Many2one('hr.appraisal.batch')
    appraisal_skill_line_ids = fields.One2many('hr.appraisal.skill.lines', 'appraisal_id')
    appraisal_skill_type_line_ids = fields.One2many('hr.appraisal.skill.type.lines', 'appraisal_id')
    appraisal_start_date = fields.Date('Appraisal Start Date', required=True)
    job_id = fields.Many2one(
        'hr.job', related='employee_id.job_id', string='Job Position', store=True)
    appraisal_overall_grade = fields.Float('Overall Grade')
    appraisal_current_grade = fields.Float('Current Grade', compute="_compute_appraisal_current_grade")
    appraisal_employee_grade = fields.Float('Employee Grade', compute="_compute_appraisal_employee_grade")
    job_code = fields.Char(related="job_id.job_code", string="Job Code")
    available_skill_ids = fields.Many2many(comodel_name="employee.skills.objectives",
                                           relation="hr_appraisal_skills_rel",
                                           string="Available Skills", compute="_compute_available_skill_ids",
                                           store=True)
    approved_by_id = fields.Many2one(comodel_name="res.users", string="Approved BY")
    approved_in = fields.Datetime(string="Approved In")
    in_probation = fields.Boolean(string="In Probation")
    state = fields.Selection(selection_add=[('manager_approve', 'Manager Approve'), ('pending',)],
                             ondelete={'manager_approve': 'set default'})

    recommendation = fields.Char()
    approver_user_ids = fields.Many2many(comodel_name="res.users", relation="appraisal_approver_user_rel",
                                         string="Approvers", compute="_compute_approver_user_ids", store=True)
    _sql_constraints = [
        ('appraisal_overall_grade_not_zero', 'CHECK(appraisal_overall_grade >= 0)',
         'You cannot set a negative Overall Grade.')
    ]

    @api.depends('appraisal_batch_id', 'appraisal_batch_id.dynamic_approve_request_ids')
    def _compute_approver_user_ids(self):
        for rec in self:
            record_approvers = self.env['res.users']
            for line in rec.appraisal_batch_id.dynamic_approve_request_ids:
                if line.user_ids:
                    record_approvers |= line.user_ids
                if line.group_id:
                    record_approvers |= line.group_id.users
                rec.approver_user_ids = record_approvers

    @api.depends("appraisal_skill_type_line_ids", "appraisal_skill_type_line_ids.score", "appraisal_overall_grade")
    def _compute_appraisal_current_grade(self):
        for record in self:
            record.appraisal_current_grade = (sum(record.appraisal_skill_type_line_ids.mapped("score")) *
                                              record.appraisal_overall_grade) / 100
    @api.depends("appraisal_skill_line_ids", "appraisal_skill_line_ids.employee_grade", "appraisal_overall_grade")
    def _compute_appraisal_employee_grade(self):
        for record in self:
            record.appraisal_employee_grade = sum(record.appraisal_skill_line_ids.mapped("employee_grade"))

    @api.depends('appraisal_skill_type_line_ids', 'appraisal_skill_type_line_ids.skill_type_id',
                 'appraisal_skill_line_ids', 'appraisal_skill_line_ids.skill_id')
    def _compute_available_skill_ids(self):
        for rec in self:
            job_skill_types = rec.appraisal_skill_type_line_ids.skill_type_id
            job_types_skill = self.env['employee.skills.objectives'].search(
                [('default_percentage', '>', 0), ('default_overall_grade', '>', 0), '|', '|',
                 ('skill_type_id', 'in', job_skill_types.ids), ('skill_type_id.show_on_all', '=', True),
                 ('skill_type_id.general_skill', '=', True)])
            selected_job_skills = rec.appraisal_skill_line_ids.skill_id
            rec.available_skill_ids = [(6, 0, (job_types_skill - selected_job_skills).ids)]

    # @api.depends('employee_id')
    # def _compute_approval_manager_ids(self):
    #     for rec in self:
    #         if rec.employee_id:
    #             direct_manager_user_id = rec.employee_id.parent_id.user_id if rec.employee_id.parent_id else \
    #                 self.env['res.users']
    #             line_manager_user_id = rec.employee_id.line_manager_id.user_id if rec.employee_id.line_manager_id else \
    #                 self.env['res.users']
    #             rec.approval_manager_ids = [(6, 0, (direct_manager_user_id + line_manager_user_id).ids)]

    @api.constrains('appraisal_start_date', 'date_close')
    def _check_start_deadline_date(self):
        for rec in self:
            if rec.appraisal_start_date and rec.date_close and \
                    rec.date_close <= rec.appraisal_start_date:
                raise ValidationError(_('Deadline should be greater than start date'))

    def _check_done_state(self):
        for appraisal in self:
            if appraisal.appraisal_skill_type_line_ids:
                total_type_score = sum(appraisal.appraisal_skill_type_line_ids.mapped('overall_score'))
                if total_type_score and total_type_score < 100:
                    raise ValidationError(_('The total score value of skill type can not less than 100%'))
                if total_type_score and total_type_score > 100:
                    raise ValidationError(_('The total score value of skill type can not exceed 100%'))

            if appraisal.appraisal_skill_line_ids:
                skill_type_lines = self.env['hr.appraisal.skill.lines'].read_group(
                    [('appraisal_id', '=', appraisal.id)], ['skill_type_id', 'total_score:sum'],
                    ['skill_type_id'])
                for skill_type in skill_type_lines:
                    if skill_type.get('total_score') and \
                            skill_type.get('total_score') < 100:
                        raise ValidationError(_("Not allowed value of total score of skill and objective "
                                                "to less than 100% "
                                                f" for skill type {skill_type.get('skill_type_id')[1]}"))

                    if skill_type.get('total_score') and \
                            skill_type.get('total_score') > 100:
                        raise ValidationError(_("Not allowed value of total score of skill and objective "
                                                "can not exceed 100%"
                                                f" for skill type {skill_type.get('skill_type_id')[1]}"))

    @api.constrains('appraisal_skill_type_line_ids', 'appraisal_skill_type_line_ids.overall_score')
    def _check_type_overall_score(self):
        for appraisal in self:
            if not self.env.context.get('skip_constrain'):
                if appraisal.appraisal_skill_type_line_ids:
                    total_type_score = sum(appraisal.appraisal_skill_type_line_ids.mapped('overall_score'))
                    if total_type_score > 100:
                        raise ValidationError(_('The total score value of skill type can not exceed 100%'))

    @api.constrains('appraisal_skill_line_ids', 'appraisal_skill_line_ids.total_score')
    def _check_skill_total_score_lines(self):
        for appraisal in self:
            if appraisal.appraisal_skill_line_ids:
                if not self.env.context.get('skip_constrain'):
                    skill_type_lines = self.env['hr.appraisal.skill.lines'].read_group(
                        [('appraisal_id', '=', appraisal.id)], ['skill_type_id', 'total_score:sum'],
                        ['skill_type_id'])
                    for skill_type in skill_type_lines:
                        if skill_type.get('total_score') and \
                                skill_type.get('total_score') > 100:
                            raise ValidationError(_("Not allowed value of total score on skill and objective "
                                                    f" for skill to exceed 100% "
                                                    f" for skill type {skill_type.get('skill_type_id')[1]}"))
                    # elif skill_type.get('total_score') and \
                    #         skill_type.get('total_score') < 100:
                    #     raise ValidationError(_("Not allowed value of percentage less than 100% "
                    #                             f"for skill type {skill_type.get('skill_type_id')[1]}"))

    @api.model_create_multi
    def create(self, val_list):
        activate_skills_appraisal = self.env['ir.config_parameter'].sudo(). \
            get_param('jbm_hr_appraisal.activate_skills_appraisal')
        if activate_skills_appraisal and not self.env.context.get('create_from_batch'):
            raise ValidationError(_('Can not create appraisal from appraisal menu, '
                                    ' Can create appraisals from appraisal batch menu'))

        return super(InheritHrAppraisal, self).create(val_list)

    def write(self, vals):
        self._check_access(vals.keys())
        if 'state' in vals and vals['state'] in ['manager_approve', 'pending']:
            self.sudo().activity_feedback(['mail.mail_activity_data_meeting', 'mail.mail_activity_data_todo'])
        if 'state' in vals and vals['state'] == 'done':
            vals['employee_feedback_published'] = True
            vals['manager_feedback_published'] = True
            current_date = datetime.date.today()
            self.sudo().activity_feedback(['mail.mail_activity_data_meeting', 'mail.mail_activity_data_todo'])
            for appraisal in self:
                appraisal.employee_id.sudo().write({
                    'last_appraisal_id': appraisal.id,
                    'last_appraisal_date': current_date,
                    'next_appraisal_date': False})
            # vals['date_close'] = current_date
            self._appraisal_plan_post()
        if 'state' in vals and vals['state'] == 'cancel':
            self.meeting_ids.unlink()
            self.activity_unlink(['mail.mail_activity_data_meeting', 'mail.mail_activity_data_todo'])
            current_date = datetime.date.today()
            # vals['date_close'] = current_date
        previous_managers = {}
        if 'manager_ids' in vals:
            previous_managers = {x: y for x, y in self.mapped(lambda a: (a.id, a.manager_ids))}
        result = super(HrAppraisal, self).write(vals)
        if 'employee_id' in vals or 'date_close' in vals:
            self.sudo()._update_previous_appraisal()
        if vals.get('date_close'):
            self.sudo()._update_next_appraisal_date()
        if 'manager_ids' in vals:
            self._sync_meeting_attendees(previous_managers)
        return result

    def unlink(self):
        for appraisal in self:
            appraisal.appraisal_skill_line_ids.sudo().unlink()
            appraisal.appraisal_skill_type_line_ids.sudo().unlink()
            appraisal_batch = appraisal.appraisal_batch_id
            if appraisal_batch and self.search_count([('appraisal_batch_id', '=', appraisal_batch.id)]) == 1:
                raise ValidationError(_("Please Cancel Batch Instead of delete appraisal ....."))
            if appraisal.state not in ('new', 'cancel'):
                raise ValidationError(_("You can't delete approved appraisal ....."))
        return super(InheritHrAppraisal, self).unlink()

    def action_back(self):
        if self.appraisal_batch_id.state not in ['done']:
            self.action_confirm()

    def action_print_appraisal_report(self):
        return self.env.ref('jbm_hr_appraisal.jbm_report_hr_appraisal_supervisory_non_supervisory').report_action(self)

    @api.depends_context('uid')
    @api.depends('employee_id', 'manager_ids')
    def _compute_user_manager_rights(self):
        for appraisal in self:
            appraisal.manager_user_ids = appraisal.manager_ids.mapped('user_id')
            appraisal.is_appraisal_manager = self.user_has_groups('hr_appraisal.group_hr_appraisal_user')
            if appraisal.is_appraisal_manager:
                appraisal.is_implicit_manager = False
                appraisal.employee_autocomplete_ids = self.env['hr.employee'].search(
                    [('company_id', '=', self.env.company.id)])
            else:
                child_ids = self.env.user.employee_id.child_ids
                appraisal_child_ids = self.env.user.employee_id.appraisal_child_ids
                appraisal.employee_autocomplete_ids = child_ids + appraisal_child_ids + self.env.user.employee_id
                appraisal.is_implicit_manager = len(appraisal.employee_autocomplete_ids) > 1

    def send_appraisal(self):
        for appraisal in self.sudo():
            confirmation_mail_template = appraisal.company_id.appraisal_confirm_mail_template
            mapped_data = {}
            if self.env.context.get('state') == 'new':
                mapped_data.update({
                    **{appraisal.employee_id: confirmation_mail_template}
                })
            elif self.env.context.get('state') == 'manager_approve':
                mapped_data.update({
                    **{manager: confirmation_mail_template for manager in appraisal.manager_ids}
                })
            for employee, mail_template in mapped_data.items():
                if not employee.work_email or not self.env.user.email or not mail_template:
                    continue
                ctx = {
                    'employee_to_name': employee.name,
                    'recipient_users': employee.user_id,
                    'url': '/mail/view?model=%s&res_id=%s' % ('hr.appraisal', appraisal.id),
                }
                mail_template = mail_template.with_context(**ctx)
                subject = mail_template._render_field('subject', appraisal.ids, post_process=False)[appraisal.id]
                body = mail_template._render_field('body_html', appraisal.ids, post_process=True)[appraisal.id]
                # post the message
                mail_values = {
                    'email_from': self.env.user.email_formatted,
                    'author_id': self.env.user.partner_id.id,
                    'model': None,
                    'res_id': None,
                    'subject': subject,
                    'body_html': body,
                    'auto_delete': True,
                    'email_to': employee.work_email
                }
                try:
                    template = self.env.ref('mail.mail_notification_light', raise_if_not_found=True)
                except ValueError:
                    _logger.warning(
                        'QWeb template mail.mail_notification_light not found when sending appraisal confirmed mails. Sending without layouting.')
                else:
                    template_ctx = {
                        'model_description': self.env['ir.model']._get('hr.appraisal').display_name,
                        'message': self.env['mail.message'].sudo().new(
                            dict(body=mail_values['body_html'], record_name=_("Appraisal Request"))),
                        'company': self.env.company,
                    }
                    body = template._render(template_ctx, engine='ir.qweb', minimal_qcontext=True)
                    mail_values['body_html'] = self.env['mail.render.mixin']._replace_local_links(body)
                self.env['mail.mail'].sudo().create(mail_values)

                if employee.user_id:
                    appraisal.activity_schedule(
                        'mail.mail_activity_data_todo', appraisal.date_close,
                        summary='للتكرم بتعبئة تقييم الموظف على نظام موارد.',
                        note=_('Fill appraisal for <a href="#" data-oe-model="%s" data-oe-id="%s">%s</a>') % (
                            appraisal.employee_id._name, appraisal.employee_id.id, appraisal.employee_id.display_name),
                        user_id=employee.user_id.id)

    def action_confirm(self):
        self.write({'state': 'manager_approve'})
        self.with_context(state='manager_approve').send_appraisal()

    def action_manager_confirm(self):
        self._check_done_state()
        self.write({
            'state': 'pending',
            'approved_by_id': self.env.uid,
            'approved_in': fields.Date.today(),
        })
        batch_appraisal = self.search(
            [('appraisal_batch_id', 'in', self.appraisal_batch_id.ids)])
        if all(appraisal.state == 'pending' for appraisal in batch_appraisal):
            batch_appraisal.appraisal_batch_id.write({'state': 'under_approval'})
            batch_appraisal.appraisal_batch_id.action_dynamic_approval_request()


class SkillHrAppraisal(models.Model):
    _name = 'hr.appraisal.skill.lines'

    appraisal_id = fields.Many2one('hr.appraisal', ondelete='cascade')
    skill_id = fields.Many2one('employee.skills.objectives')
    create_from_batch = fields.Boolean('Create from batch', default=False)
    from_job_position = fields.Boolean('Create from Job Position', default=False)
    description = fields.Html()
    skill_type_id = fields.Many2one('employee.skills.objective.types')
    employee_grade = fields.Float('Employee Grade')
    approve_grade = fields.Float('Approved Grade')
    employee_notes = fields.Text('Employee Notes')
    manager_notes = fields.Text('Manager Notes')
    overall_grade = fields.Float('Overall Grade')
    total_score = fields.Float('Total Score (%)')
    score = fields.Float('Score (%)', compute="_compute_score_appraisal_skill_line")

    _sql_constraints = [
        ('employee_grade_not_zero', 'CHECK(employee_grade >= 0)',
         'You cannot set a negative Employee Grade.'),
        ('approve_grade_not_zero', 'CHECK(approve_grade >= 0)',
         'You cannot set a negative Approved Grade.'),
        ('overall_grade_not_zero', 'CHECK(overall_grade >= 0)',
         'You cannot set a negative Overall Grade.'),
        ('total_score_not_zero', 'CHECK(total_score >= 0)',
         'You cannot set a negative Total Score.'),
    ]

    @api.depends("approve_grade", "total_score", "overall_grade", "skill_id")
    def _compute_score_appraisal_skill_line(self):
        for line in self:
            if line.overall_grade:
                line.score = (line.approve_grade * line.total_score) / line.overall_grade
            else:
                line.score = 0.0

    @api.constrains('skill_id')
    @api.onchange('skill_id')
    def _onchange_skill_id(self):
        for record in self:
            if record.skill_id:
                job_skill_line = record.appraisal_id.employee_id.job_id.skill_line_ids.filtered(
                    lambda s: s.skill_id == record.skill_id
                )
                if job_skill_line:
                    record.description = job_skill_line.skill_id.description
                    record.skill_type_id = job_skill_line.skill_id.skill_type_id.id
                    if not record.overall_grade:
                        record.overall_grade = job_skill_line.default_overall_grade
                    if not record.total_score:
                        record.total_score = job_skill_line.default_percentage
                else:
                    record.description = record.skill_id.description
                    record.skill_type_id = record.skill_id.skill_type_id.id
                    if not record.overall_grade:
                        record.overall_grade = record.skill_id.default_overall_grade
                    if not record.total_score:
                        record.total_score = record.skill_id.default_percentage
            else:
                record.description = ''
                record.skill_type_id = False
                record.overall_grade = 0.0
                record.total_score = 0.0

    @api.constrains('approve_grade', 'overall_grade')
    def _check_approve_grade(self):
        for record in self:
            if record.approve_grade and record.overall_grade \
                    and (record.approve_grade < 0 or record.approve_grade > record.overall_grade):
                raise ValidationError(_('Approve Grade cannot be greater than or equal Overall Grade'
                                        ' or less than  or equal 0'))

    @api.constrains('employee_grade', 'overall_grade')
    def _check_employee_grade(self):
        for record in self:
            if record.employee_grade and record.overall_grade \
                    and (record.employee_grade < 0 or record.employee_grade > record.overall_grade):
                raise ValidationError(_('Employee Grade cannot be greater than or equal Overall Grade'
                                        ' or less than  or equal 0'))

    def delete_skill_line(self):
        self.ensure_one()
        if self.from_job_position:
            return
        if self.appraisal_id.state == 'done':
            return
        self.sudo().unlink()


class SkillTypeHrAppraisal(models.Model):
    _name = 'hr.appraisal.skill.type.lines'

    appraisal_id = fields.Many2one('hr.appraisal', ondelete='cascade')
    skill_type_id = fields.Many2one('employee.skills.objective.types')
    create_from_batch = fields.Boolean('Create from batch', default=False)
    from_job_position = fields.Boolean('From Job Position', default=False)
    grade = fields.Float('Grade', compute="_compute_grade_appraisal_skill_type_line")
    overall_grade = fields.Float('Overall Grade')
    score = fields.Float('Score (%)', compute="_compute_score_appraisal_skill_type_line")
    overall_score = fields.Float('Overall Score (%)')

    _sql_constraints = [
        ('overall_grade_not_zero', 'CHECK(overall_grade >= 0)',
         'You cannot set a negative Overall Grade.'),
        ('overall_score_not_zero', 'CHECK(overall_score >= 0)',
         'You cannot set a negative Overall Score.'),
    ]

    @api.depends("appraisal_id.appraisal_skill_line_ids", "overall_score",
                 "appraisal_id.appraisal_skill_line_ids.score")
    def _compute_score_appraisal_skill_type_line(self):
        for record in self:
            same_skill_type = record.appraisal_id.appraisal_skill_line_ids. \
                filtered(lambda l: l.skill_type_id == record.skill_type_id)
            record.score = (sum(same_skill_type.mapped("score")) * record.overall_score) / 100

    @api.depends("score", "overall_grade", "overall_score")
    def _compute_grade_appraisal_skill_type_line(self):
        for record in self:
            if record.overall_score:
                record.grade = (record.score * record.overall_grade) / record.overall_score
            else:
                record.grade = 0.0

    @api.constrains('skill_type_id')
    @api.onchange('skill_type_id')
    def _onchange_skill_id(self):
        for record in self:
            if record.skill_type_id:
                job_skill_type_line = record.appraisal_id.employee_id.job_id.skill_type_line_ids.filtered(
                    lambda s: s.skill_type_id == record.skill_type_id
                )
                if job_skill_type_line:
                    if not record.overall_grade:
                        record.overall_grade = job_skill_type_line and job_skill_type_line[0].overall_grade
                    if not record.overall_score:
                        record.overall_score = job_skill_type_line and job_skill_type_line[0].overall_score
                    continue
                job_skill_type_batch = record.appraisal_id.appraisal_batch_id.appraisal_skill_type_ids.filtered(
                    lambda t: t.skill_type_id == record.skill_type_id
                )
                if job_skill_type_batch:
                    if not record.overall_grade:
                        record.overall_grade = job_skill_type_batch.overall_grade
                    if not record.overall_score:
                        record.overall_score = job_skill_type_batch.overall_score
                    continue
                skill_type_show_all = self.env['employee.skills.objective.types'].search([
                    ('show_on_all', '=', True), ('id', '=', record.skill_type_id.id)
                ])
                if skill_type_show_all:
                    if not record.overall_score:
                        record.overall_score = skill_type_show_all.default_overall
            else:
                record.overall_grade = 0.0
                record.overall_score = 0.0

    def delete_skill_type_line(self):
        self.ensure_one()
        if self.from_job_position:
            return
        if self.appraisal_id.state == 'done':
            return
        self.sudo().unlink()
