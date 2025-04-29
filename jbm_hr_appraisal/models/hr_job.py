from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError


class InheritHrJob(models.Model):
    _inherit = 'hr.job'
    _parent_store = True

    parent_id = fields.Many2one('hr.job')
    parent_path = fields.Char(index=True)

    child_ids = fields.One2many('hr.job', 'parent_id',
                                string='Jobs subordinates')

    course_ids = fields.Many2many('training.course', 'courses_jobs_rel', 'course_id', 'job_id')

    job_code = fields.Char('Job Code')
    job_category = fields.Selection(string='Job Category',selection=[('supervisory', 'إشرافية'), ('non_supervisory', 'غير إشرافية'), ])
        
    description = fields.Html()
    
    n_allowed_employees = fields.Integer('Number of allowed employees', default=1)

    no_of_employee = fields.Integer(compute='_compute_employees',
                                    string="Current Number of Employees", store=False,
                                    help='Number of employees currently occupying this job position.')
    expected_employees = fields.Integer(compute='_compute_employees',
                                        string='Expected New Employees', store=True,
                                        help='Expected number of employees for this job position after new recruitment.')

    skill_line_ids = fields.One2many('hr.jobs.skills.lines', 'job_id')
    skill_type_line_ids = fields.One2many('hr.job.skill.type.lines', 'job_id')
    department_id = fields.Many2one('hr.department', string='Department', domain=[])
    available_skill_ids = fields.Many2many(comodel_name="employee.skills.objectives", relation="hr_job_skills_rel",
                                           string="Available Skills", compute="_compute_available_skill_ids",
                                           store=True)

    @api.constrains('n_allowed_employees')
    def _check_n_allowed_employees(self):
        for job in self:
            if job.n_allowed_employees <= 0:
                raise ValidationError(_('Not allowed to have a number less than or equal zero'))

    @api.depends('n_allowed_employees',
                 'employee_ids.job_id', 'employee_ids.active')
    def _compute_employees(self):
        """Override this method to recalculate the expected number of employees"""
        employee_data = self.env['hr.employee'].read_group([('job_id', 'in', self.ids)], ['job_id'], ['job_id'])
        result = dict((data['job_id'][0], data['job_id_count']) for data in employee_data)
        for job in self:
            job.no_of_employee = result.get(job.id, 0)
            job.expected_employees = job.n_allowed_employees - result.get(job.id, 0)

    @api.depends('skill_type_line_ids', 'skill_type_line_ids.skill_type_id', 'skill_line_ids',
                 'skill_line_ids.skill_id')
    def _compute_available_skill_ids(self):
        for rec in self:
            job_skill_types = rec.skill_type_line_ids.skill_type_id
            job_types_skill = self.env['employee.skills.objectives'].search([('skill_type_id', 'in', job_skill_types.ids)])
            selected_job_skills = rec.skill_line_ids.skill_id
            rec.available_skill_ids = [(6, 0, (job_types_skill - selected_job_skills).ids)]

    @api.constrains('skill_line_ids')
    def _check_skill_type_overall(self):
        for job in self:
            if job.skill_line_ids:
                skill_type_lines = self.env['hr.jobs.skills.lines'].read_group(
                    [('job_id', '=', job.id)], ['skill_type_id', 'default_percentage:sum'],
                    ['skill_type_id'])
                for skill_type in skill_type_lines:
                    if skill_type.get('default_percentage') and \
                            skill_type.get('default_percentage') > 100:
                        raise ValidationError(_("Not allowed value of percentage to exceed 100% "
                                                f" for skill type {skill_type.get('skill_type_id')[1]}"))
                    elif skill_type.get('default_percentage') and \
                            skill_type.get('default_percentage') < 100:
                        raise ValidationError(_("Not allowed value of percentage less than 100% "
                                                f"for skill type {skill_type.get('skill_type_id')[1]}"))

    @api.constrains('parent_id')
    @api.onchange('parent_id')
    def _check_change_related_employees(self):
        for job in self:
            if job.parent_id and job.parent_id.employee_ids:
                employees = job.employee_ids
                selected_employee = job.parent_id.employee_ids[0]
                for emp in employees:
                    emp.parent_id = selected_employee.id
            else:
                employees = job.employee_ids
                for emp in employees:
                    if emp.department_id.manager_id:
                        emp.parent_id = emp.department_id.manager_id.id

    @api.constrains('skill_type_line_ids')
    def _check_job_skill_type_overall(self):
        for rec in self:
            sum_overall_score = sum(rec.skill_type_line_ids.mapped('overall_score'))
            if sum_overall_score and sum_overall_score > 100:
                raise ValidationError(_('The overall score value can not exceed 100%'))

    # Override to stop domain on department_id
    @api.onchange('group')
    def _on_group_change(self):
        pass

    def view_related_employees(self):
        self.ensure_one()
        return {
            'name': 'Employees',
            'domain': [('id', 'in', self.employee_ids.ids)],
            'view_type': 'form',
            'res_model': 'hr.employee',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'context': {
                'default_job_id': self.id
            }
        }


class JobSkillsLines(models.Model):
    _name = 'hr.jobs.skills.lines'
    _description = 'HR Job Skills'

    job_id = fields.Many2one('hr.job', ondelete='cascade')
    skill_id = fields.Many2one('employee.skills.objectives', string='Skill')
    description = fields.Html()
    skill_type_id = fields.Many2one('employee.skills.objective.types', readonly=True)
    default_show = fields.Boolean('Show in employee appraisal')
    default_percentage = fields.Float('Percentage on appraisal')
    default_overall_grade = fields.Float('Overall Grade')

    _sql_constraints = [
        ('default_percentage_not_zero', 'CHECK(default_percentage >= 0)',
         'You cannot set a negative for Percentage on appraisal.'),
        ('default_overall_grade_not_zero', 'CHECK(default_overall_grade >= 0)',
         'You cannot set a negative Overall Grade.'),
    ]

    @api.onchange('skill_id')
    def _onchange_skill_id(self):
        for line in self:
            if line.skill_id:
                line.description = line.skill_id.description
                line.skill_type_id = line.skill_id.skill_type_id.id
                line.default_show = line.skill_id.default_show
                line.default_percentage = line.skill_id.default_percentage
                line.default_overall_grade = line.skill_id.default_overall_grade
            else:
                line.description = ''
                line.skill_type_id = False
                line.default_show = False
                line.default_percentage = 0.0
                line.default_overall_grade = 0.0

    @api.constrains('skill_id')
    def _check_skill_id(self):
        for line in self:
            if not line.skill_id:
                raise ValidationError(_('Please you must select a skill'))


class JobSkillTypeLines(models.Model):
    _name = 'hr.job.skill.type.lines'
    _description = 'HR Job Skill Type Lines'

    job_id = fields.Many2one('hr.job', ondelete='cascade')
    skill_type_id = fields.Many2one('employee.skills.objective.types')
    overall_score = fields.Float('Overall Score (%)')
    overall_grade = fields.Float('Overall Grade')

    _sql_constraints = [
        ('overall_score_not_zero', 'CHECK(overall_score >= 0)',
         'You cannot set a negative for Overall Score.'),
        ('overall_grade_not_zero', 'CHECK(overall_grade >= 0)',
         'You cannot set a negative for Overall Grade.'),
    ]

    @api.onchange('skill_type_id')
    def _onchange_skill_type_id(self):
        if self.skill_type_id:
            self.overall_score = self.skill_type_id.default_overall
        else:
            self.overall_score = 0.0

    @api.constrains('skill_type_id')
    def _check_skill_type_id(self):
        for line in self:
            if not line.skill_type_id:
                raise ValidationError(_('Please you must select a skill type'))
