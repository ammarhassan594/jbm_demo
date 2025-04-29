import logging
import datetime

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.safe_eval import safe_eval, time

_logger = logging.getLogger(__name__)


def evaluate_python_code(record=None, python_code=''):
    """Return the value of python expression

    @param record: The object to evaluate expression from it
    @param python_code: Python expression

    @return: The value of python expression if found, else False and error message
    @retype: float, str
    """
    if not python_code:
        return False
    record_sudo = record.sudo()
    try:
        localdict = {
            'time': time,
            'context_today': datetime.datetime.now,
            'user': record_sudo.env.user,
            'record': record_sudo,
            'env': record_sudo.env
        }
        # result = env['ir.config_parameter'].sudo().get_param('attendance_api_token')
        safe_eval(python_code, localdict, mode="exec", nocopy=True)
        test = None
        message = ''
        if "result" in localdict:
            test = localdict.get('result', False)
        else:
            message = 'Please check expression as mentioned before must be write result'
    except Exception as e:
        _logger.warning(e)
        message = str(e)
        test = None
    return test, message


class EmployeeSkillsObjectives(models.Model):
    _name = 'employee.skills.objectives'
    _description = 'Employee Skills Objectives'

    name = fields.Char()
    code = fields.Char()
    description = fields.Html()
    skill_type_id = fields.Many2one('employee.skills.objective.types')
    default_show = fields.Boolean('Show in employee appraisal')
    default_percentage = fields.Float('Percentage on appraisal')
    default_overall_grade = fields.Float('Overall Grade')
    computation_type = fields.Selection([
        ('python_code', 'Python Code'),
        ('sql_code', 'SQL Code'),
        ('manual', 'Manual'),
    ], default='python_code')
    computation_code = fields.Text('Expression')
    computation_result = fields.Float('Result')
    skill_job_ids = fields.One2many('hr.jobs.skills.lines', 'skill_id')
    n_related_jobs = fields.Integer('N.Jobs', compute="_compute_related_jobs")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('default_percentage_not_zero', 'CHECK(default_percentage >= 0)',
         'You cannot set a negative for Percentage on appraisal.'),
        ('default_overall_grade_not_zero', 'CHECK(default_overall_grade >= 0)',
         'You cannot set a negative for Overall Grade.')
    ]

    @api.depends('skill_job_ids')
    def _compute_related_jobs(self):
        for skill in self:
            related_jobs = skill.skill_job_ids.mapped('job_id')
            skill.n_related_jobs = len(related_jobs)

    ########
    # Business Rules
    ########

    @api.constrains('default_percentage')
    def _check_default_percentage(self):
        for record in self:
            if record.default_percentage and record.default_percentage > 100:
                raise ValidationError(_('The percentage does not exceed 100%'))

    @api.onchange('computation_type')
    def _onchange_computation_type(self):
        for record in self:
            if record.computation_type == 'python_code':
                record.computation_code = """# Your expression must be return one value like this:\n# employees = env['hr.employee'].sudo().search([])\n# result = employees.mapped('field_name')\n"""
            elif record.computation_type == 'sql_code':
                record.computation_code = """# Your expression must be return one value like this:\n# env.cr.execute(query, params=None, log_exceptions=None) \n# result = env.cr.fetchone()[0]\n"""

    ##############
    # ORM Methods
    ##############

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        limit = self.env.context.get('default_limit', 0) or limit
        records = super().name_search(name=name, args=args, operator=operator, limit=limit)
        # if self.env.context.get('from_job_position'):
        #     job_skill_line = self.env['hr.jobs.skills.lines'].sudo()
        #     current_job_id = self.env['hr.job'].sudo().search([
        #         ('id', '=', int(self.env.context.get('current_job_id')))
        #     ])
        #     job_skill_types = current_job_id.skill_type_line_ids.mapped('skill_type_id')
        #     job_skills = self.env.context.get('job_skills', [])
        #     skills = []
        #     return_skills = []
        #     for j_s in job_skills:
        #         if j_s[0] == 4:
        #             job_skill_line_id = job_skill_line.search([
        #                 ('id', '=', j_s[1]), ('skill_id', '!=', False)])
        #             if job_skill_line_id:
        #                 skills.append(job_skill_line_id.skill_id.id)
        #         elif j_s[0] in [1, 0]:
        #             if j_s[2].get('skill_id'):
        #                 skills.append(j_s[2].get('skill_id'))
        #
        #     for r in records:
        #         skill_object = self.browse(r[0])
        #         if skill_object.id not in skills and \
        #                 skill_object.skill_type_id.id in job_skill_types.ids:
        #             return_skills.append(r)
        #     return return_skills
        # Check if search from appraisal_skill_lines
        # if self.env.context.get('from_hr_appraisal'):
        #     appraisal_skill_line = self.env['hr.appraisal.skill.lines'].sudo()
        #     current_appraisal_id = self.env['hr.appraisal'].sudo().search([
        #         ('id', '=', int(self.env.context.get('skill_appraisal_id')))
        #     ])
        #     appraisal_skill_types = current_appraisal_id.appraisal_skill_type_line_ids.mapped('skill_type_id')
        #     appraisal_skills = self.env.context.get('skill_appraisal', [])
        #     skills = []
        #     return_skills = []
        #     for j_s in appraisal_skills:
        #         if j_s[0] == 4:
        #             appraisal_skill_line_id = appraisal_skill_line.search([
        #                 ('id', '=', j_s[1]), ('skill_id', '!=', False)])
        #             if appraisal_skill_line_id:
        #                 skills.append(appraisal_skill_line_id.skill_id.id)
        #         elif j_s[0] in [1, 0]:
        #             if j_s[2].get('skill_id'):
        #                 skills.append(j_s[2].get('skill_id'))
        #
        #     for r in records:
        #         skill_object = self.browse(r[0])
        #         if not (skill_object.default_percentage > 0
        #                 and skill_object.default_overall_grade > 0):
        #             continue
        #         if skill_object.id not in skills and \
        #                 (skill_object.skill_type_id.show_on_all or
        #                  skill_object.skill_type_id.general_skill or
        #                  skill_object.skill_type_id in appraisal_skill_types):
        #             return_skills.append(r)
        #     return return_skills
        return records

    @api.model_create_multi
    def create(self, val_list):
        for val in val_list:
            if val.get('computation_code') and \
                    val.get('computation_type') in ['python_code', 'sql_code'] \
                    and val.get('default_show') is True:
                test, message = evaluate_python_code(self,
                                                     python_code=val['computation_code'])

                if test is None and message:
                    raise ValidationError(_('Wrong Python expression\n'
                                            f'{message}'))
                if not isinstance(test, (float, int)):
                    raise ValidationError(_('Expression must return a numerical value'))
                if test is not None and isinstance(test, (float, int)):
                    val['computation_result'] = test
        return super().create(val_list)

    def write(self, vals):
        if (self.default_show is True or vals.get('default_show') is True) \
                and (vals.get('computation_type') in ['python_code', 'sql_code']
                     or self.computation_type in ['python_code', 'sql_code']):
            if vals.get('computation_code'):
                test, message = evaluate_python_code(self,
                                                     python_code=vals['computation_code'])

                if test is None and message:
                    raise ValidationError(_('Wrong Python expression\n'
                                            f'{message}'))
                if not isinstance(test, (float, int)):
                    raise ValidationError(_('Expression must return a numerical value'))
                vals['computation_result'] = test
        return super().write(vals)

    def action_open_jobs(self):
        self.ensure_one()
        return {
            'name': 'Jobs',
            'domain': [('id', 'in', self.skill_job_ids.mapped('job_id').ids)],
            'view_type': 'form',
            'res_model': 'hr.job',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'context': {
                'create': False,
                'edit': False,
            }
        }
