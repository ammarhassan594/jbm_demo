from odoo import fields, models, api, _, Command
from odoo.exceptions import ValidationError

STATES = {
    'confirmed': [('readonly', True)],
    'sent': [('readonly', True)],
    'done': [('readonly', True)],
}


class AppraisalBatch(models.Model):
    _name = 'hr.appraisal.batch'
    _description = 'Appraisal Batch'
    _inherit = ['dynamic.approval.mixin', 'mail.thread', 'mail.activity.mixin']
    _state_from = ['under_approval']
    _state_to = ['done']

    name = fields.Char(string="Name", required=True, compute='_compute_name', readonly=False, store=True, states=STATES)
    company_id = fields.Many2one('res.company', string='Organization',
                                 default=lambda self: self.env.company,
                                 required=True, states=STATES)
    department_ids = fields.Many2many('hr.department', states=STATES)
    employee_ids = fields.Many2many('hr.employee', compute="_compute_employee_ids", store=True,
                                    readonly=False)
    partner_manager_ids = fields.Many2many('res.partner', compute='_compute_partner_manager')
    appraisal_start_date = fields.Date('Start Date', states=STATES, required=True)
    appraisal_deadline = fields.Date('Deadline', states=STATES, required=True)
    current_overall_grade = fields.Float('Current Overall Grade', compute="_compute_current_overall_grade")
    overall_grade_appraisal = fields.Float('Overall Grade Appraisal', states=STATES)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('under_approval', 'Under Approval'),
        ('done', 'Done'),
    ], default='draft', string='Status',
        index=True, readonly=True, copy=False)
    appraisal_ids = fields.One2many('hr.appraisal', 'appraisal_batch_id')
    appraisal_skill_type_ids = fields.One2many('appraisal.batch.skill.type',
                                               'appraisal_batch_id', states=STATES)
    number_appraisal = fields.Integer('Appraisals', compute="_compute_number_appraisal")

    _sql_constraints = [
        ('overall_grade_appraisal_not_zero', 'CHECK(overall_grade_appraisal >= 0)',
         'You cannot set a negative Overall Grade Appraisal.'),
    ]

    @api.depends('appraisal_start_date', 'appraisal_deadline')
    def _compute_name(self):
        for record in self:
            record_name = "Appraisal Batch "
            if record.appraisal_start_date and record.appraisal_deadline:
                record_name += " from %s, to %s" % (record.appraisal_start_date, record.appraisal_deadline)
            record.name = record_name

    @api.depends('department_ids')
    def _compute_employee_ids(self):
        for rec in self:
            rec.employee_ids = [(6, 0, rec.department_ids.member_ids.ids)]

    @api.depends('appraisal_ids', 'appraisal_ids.appraisal_current_grade')
    def _compute_current_overall_grade(self):
        for batch in self:
            if batch.appraisal_ids:
                batch.current_overall_grade = (sum(batch.appraisal_ids.mapped('appraisal_current_grade'))
                                               / len(batch.appraisal_ids))
            else:
                batch.current_overall_grade = 0

    @api.depends('appraisal_ids')
    def _compute_number_appraisal(self):
        for batch in self:
            batch.number_appraisal = len(batch.appraisal_ids)

    @api.depends('department_ids')
    def _compute_partner_manager(self):
        for batch in self:
            managers = batch.department_ids.mapped('manager_id').mapped('user_id')
            batch.partner_manager_ids = managers.mapped('partner_id')

    @api.constrains('appraisal_start_date', 'appraisal_deadline')
    def _check_start_deadline_date(self):
        for rec in self:
            if rec.appraisal_start_date and rec.appraisal_deadline and \
                    rec.appraisal_deadline <= rec.appraisal_start_date:
                raise ValidationError(_('Deadline should be greater than start date'))

    @api.constrains('appraisal_skill_type_ids')
    def _check_appraisal_skill_type_ids(self):
        for rec in self:
            sum_overall_score = sum(rec.appraisal_skill_type_ids.mapped('overall_score'))
            if sum_overall_score and sum_overall_score > 100:
                raise ValidationError(_('The overall score value can not exceed 100%'))

    #################
    # ORM
    ################
    # def name_get(self):
    #     names = []
    #     for record in self:
    #         record_name = "Appraisal Batch "
    #         if record.appraisal_start_date and record.appraisal_deadline:
    #             record_name += " from %s, to %s" % (record.appraisal_start_date, record.appraisal_deadline)
    #         names.append((record.id, record_name))
    #     return names

    @api.model
    def default_get(self, fields):
        res = super(AppraisalBatch, self).default_get(fields)
        skill_types = self.env['employee.skills.objective.types']. \
            search([('default_overall', '>', 0)])

        command = [
            Command.create({
                'skill_type_id': skill_type.id,
                'name': skill_type.name,
                'code': skill_type.code,
                'description': skill_type.description,
                'overall_score': skill_type.default_overall,
            }) for skill_type in skill_types
        ]
        if skill_types:
            res.update({'appraisal_skill_type_ids': command})
        return res

    def unlink(self):
        for batch in self:
            if batch.state not in ['draft']:
                raise ValidationError(_('Can not delete batch not on draft'))
        return super().unlink()

    ################
    # Business Logic
    ################

    def action_confirm(self):
        for batch in self:
            employees = batch.employee_ids
            val_list = []
            for employee in employees:
                if not employee.parent_id:
                    raise ValidationError(_('Not found manager for employee %s') % employee.name)
                # get skills types from job positions
                job_skills_types = employee.job_id.skill_type_line_ids.mapped('skill_type_id')
                from_job_position = True
                # if not skill types then get from batch
                if not job_skills_types:
                    from_job_position = False
                    job_skills_types = self.appraisal_skill_type_ids.mapped('skill_type_id')
                sum_overall_score_job_type = sum(employee.job_id.skill_type_line_ids.mapped('overall_score'))

                general_types = self.env['employee.skills.objective.types'].search([
                    ('general_skill', '=', True)
                ])

                # get skills from job positions and all skills related to types show on all
                command_skills = []
                job_skills = employee.job_id.skill_line_ids. \
                    filtered(lambda s:
                             s.default_show and s.default_overall_grade and s.default_percentage
                             and s.default_overall_grade > 0 and s.default_percentage > 0) \
                    .mapped('skill_id')
                if job_skills:
                    command_skills += [
                        Command.create({
                            'skill_id': job_skill.id,
                            'from_job_position': True,
                        }) for job_skill in job_skills
                    ]
                general_skills = self.env['employee.skills.objectives']
                if general_types.skill_objective_ids:
                    general_skills |= general_types.skill_objective_ids. \
                        filtered(lambda s:
                                 s.id not in job_skills.ids and
                                 s.default_overall_grade and s.default_percentage
                                 and s.default_overall_grade > 0 and s.default_percentage > 0)
                if general_skills:
                    command_skills += [
                        Command.create({
                            'skill_id': show_job_skill.id,
                        }) for show_job_skill in general_skills
                    ]

                command_skills_types = [
                    Command.create({
                        'skill_type_id': job_skill_type.id,
                        'from_job_position': from_job_position,
                    }) for job_skill_type in job_skills_types
                ]
                # Adjust show all appraisal types
                if from_job_position:
                    batch_show_all_types = self.appraisal_skill_type_ids. \
                        filtered(lambda t:
                                 t.skill_type_id.id not in job_skills_types.ids
                                 and t.skill_type_id.show_on_all and
                                 t.overall_score and t.overall_score > 0)
                    remaining_type_score = 100 - sum_overall_score_job_type
                    sum_all_skill_type_show = sum(batch_show_all_types.mapped('overall_score'))
                    if sum_overall_score_job_type and sum_all_skill_type_show and \
                            sum_overall_score_job_type < 100 and sum_all_skill_type_show > remaining_type_score:
                        for skill_type_show in batch_show_all_types:
                            new_score = (skill_type_show.overall_score / sum_all_skill_type_show) * \
                                        remaining_type_score
                            command_skills_types += [
                                Command.create({
                                    'skill_type_id': skill_type_show.skill_type_id.id,
                                    'overall_score': new_score,
                                })
                            ]
                    else:
                        command_skills_types += [
                            Command.create({
                                'skill_type_id': skill_type_show.skill_type_id.id,
                            }) for skill_type_show in batch_show_all_types
                        ]
                if not command_skills:
                    raise ValidationError(
                        _("There's no skills and objectives evaluation for employee %s" % employee.name))
                if not command_skills_types:
                    raise ValidationError(_("There's no skill types evaluations for employee %s" % employee.name))
                val_list.append({
                    'employee_id': employee.id,
                    'manager_ids': [(4, employee.parent_id.id)],
                    'date_close': batch.appraisal_deadline,
                    'appraisal_start_date': batch.appraisal_start_date,
                    'state': 'new',
                    'appraisal_overall_grade': batch.overall_grade_appraisal,
                    'appraisal_batch_id': batch.id,
                    'appraisal_skill_line_ids': command_skills,
                    'appraisal_skill_type_line_ids': command_skills_types,
                })
            appraisals = self.env['hr.appraisal'].with_context(create_from_batch=True, skip_constrain=True).create(
                val_list)
            appraisals.with_context(state='new').send_appraisal()
            batch.write({'state': 'confirmed'})

    def _run_final_approve_function(self):
        self.appraisal_ids.write({'state': 'done'})

    def _get_default_template(self):
        return False

    def action_send_email(self):
        """ Open a window to compose an email, with an edit a template
            message loaded by default
        """
        self.ensure_one()
        default_template = self._get_default_template()
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='hr.appraisal.batch',
            default_partner_ids=self.partner_manager_ids.ids,
            default_res_id=self.id,
            default_use_template=bool(default_template),
            default_template_id=default_template and default_template.id,
            default_composition_mode='comment',
            custom_layout='mail.mail_notification_light',
            mark_appraisal_batch_as_sent=True,
            force_email=True,
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    def action_done(self):
        for batch in self:
            if batch.state not in ['sent']:
                return
            for appraisal in batch.appraisal_ids:
                appraisal.action_done()
            batch.write({'state': 'done'})

    def action_reset_draft(self):
        for batch in self:
            for appraisal in batch.appraisal_ids.filtered(lambda a: a.state != 'done'):
                appraisal.unlink()
            batch.write({'state': 'draft'})

    def action_open_appraisal(self):
        self.ensure_one()
        context = dict(self.env.context, create=False, edit=True)
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,list,form',
            'res_model': 'hr.appraisal',
            'name': 'Appraisal Requests',
            'domain': [('id', 'in', self.appraisal_ids.ids)],
            'context': context,
        }


class AppraisalBatchSkillType(models.Model):
    _name = 'appraisal.batch.skill.type'

    appraisal_batch_id = fields.Many2one('hr.appraisal.batch', ondelete='cascade')
    name = fields.Char()
    code = fields.Char()
    skill_type_id = fields.Many2one('employee.skills.objective.types')
    description = fields.Html()
    overall_score = fields.Float('Overall Score (%)')
    overall_grade = fields.Float('Overall Grade')

    _sql_constraints = [
        ('overall_score_not_zero', 'CHECK(overall_score >= 0)', 'You cannot set a negative Overall Score.'),
        ('overall_grade_not_zero', 'CHECK(overall_grade >= 0)', 'You cannot set a negative Overall Grade.'),
    ]

    @api.constrains('skill_type_id')
    @api.onchange('skill_type_id')
    def _onchange_skill_type_id(self):
        for record in self:
            if record.skill_type_id:
                record.description = record.skill_type_id.description
                record.overall_score = record.skill_type_id.default_overall
            else:
                record.description = ''
                record.overall_score = 0.0
