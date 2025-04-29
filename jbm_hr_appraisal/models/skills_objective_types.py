from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class EmployeeSkillsObjectiveTypes(models.Model):
    _name = 'employee.skills.objective.types'
    _description = 'Employee skills objective types'

    company_id = fields.Many2one('res.company', string='Organization',
                                 default=lambda self: self.env.company, required=True)
    name = fields.Char()
    code = fields.Char()
    description = fields.Html()
    default_overall = fields.Float('Overall (%)')
    general_skill = fields.Boolean('General Skill')
    show_on_all = fields.Boolean('Show on all appraisals')
    active = fields.Boolean(default=True)
    skill_objective_ids = fields.One2many('employee.skills.objectives', 'skill_type_id')
    type_category = fields.Selection(
        selection=[('personal_attributes', 'الأداء الوظيفي'), ('job_performance', 'السمات الشخصية'),], string='Category')


    _sql_constraints = [
        ('default_overall_not_zero', 'CHECK(default_overall >= 0)',
         'You cannot set a negative for Overall.')
    ]

    ########
    # Business Rules
    ########

    @api.constrains('company_id', 'default_overall')
    def _check_default_overall(self):
        for record in self:
            same_organization = self.search([
                ('company_id', '=', record.company_id.id),
            ])
            if same_organization and \
                    sum(same_organization.mapped('default_overall')) > 100:
                raise ValidationError(_('Overall on same organization'
                                        f' {record.company_id.name} must be less than 100%'))

    ########
    # ORM
    ########

    # @api.model
    # def name_search(self, name='', args=None, operator='ilike', limit=100):
    #     limit = self.env.context.get('default_limit', 0) or limit
    #     records = super().name_search(name=name, args=args, operator=operator, limit=limit)
    #     print('records:', records, 'limit:', limit)
    #     if self.env.context.get('appraisal_batch_skill_types'):
    #         appraisal_batch_skill_type = self.env['appraisal.batch.skill.type']
    #         batch_types = self.env.context.get('appraisal_batch_skill_types', [])
    #         types = []
    #         return_types = []
    #         for j_s in batch_types:
    #             if j_s[0] == 4:
    #                 batch_type_line_id = appraisal_batch_skill_type.search([
    #                     ('id', '=', j_s[1]), ('skill_type_id', '!=', False)])
    #                 if batch_type_line_id:
    #                     types.append(batch_type_line_id.skill_type_id.id)
    #             elif j_s[0] in [1, 0]:
    #                 if j_s[2].get('skill_type_id'):
    #                     types.append(j_s[2].get('skill_type_id'))
    #         if types:
    #             for r in records:
    #                 if r[0] not in types:
    #                     return_types.append(r)
    #             return return_types
    #         return records
    #
    #     if self.env.context.get('appraisal_skill_type_line'):
    #         appraisal_skill_type_line = self.env['hr.appraisal.skill.type.lines']
    #         appraisal_types = self.env.context.get('appraisal_skill_type_line', [])
    #         appraisal_id = self.env['hr.appraisal'].search([
    #             ('id', '=', int(self.env.context.get('skill_type_appraisal_id')))
    #         ])
    #         batch_appraisal_skill_type = appraisal_id.appraisal_batch_id. \
    #             appraisal_skill_type_ids.mapped('skill_type_id')
    #         types = []
    #         return_types = []
    #         print('appraisal_types', appraisal_types)
    #         for j_s in appraisal_types:
    #             if j_s[0] == 4:
    #                 appraisal_type_line_id = appraisal_skill_type_line.search([
    #                     ('id', '=', j_s[1]), ('skill_type_id', '!=', False)])
    #                 if appraisal_type_line_id:
    #                     types.append(appraisal_type_line_id.skill_type_id.id)
    #             else:
    #                 if j_s[2].get('skill_type_id'):
    #                     types.append(j_s[2].get('skill_type_id'))
    #         if types:
    #             for r in records:
    #                 skill_type_object = self.browse(r[0])
    #                 if skill_type_object.id not in types and \
    #                         skill_type_object.id in batch_appraisal_skill_type.ids:
    #                     return_types.append(r)
    #             return return_types
    #         return records
    #
    #     if self.env.context.get('job_type_skills'):
    #         job_skill_type = self.env['hr.job.skill.type.lines']
    #         job_types = self.env.context.get('job_type_skills', [])
    #         types = []
    #         return_types = []
    #         for j_s in job_types:
    #             if j_s[0] == 4:
    #                 job_type_line_id = job_skill_type.search([
    #                     ('id', '=', j_s[1]), ('skill_type_id', '!=', False)])
    #                 if job_type_line_id:
    #                     types.append(job_type_line_id.skill_type_id.id)
    #             elif j_s[0] in [1, 0]:
    #                 if j_s[2].get('skill_type_id'):
    #                     types.append(j_s[2].get('skill_type_id'))
    #         if types:
    #             for r in records:
    #                 if r[0] not in types:
    #                     return_types.append(r)
    #             return return_types
    #         return records
    #
    #     return records
