# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError, UserError


class HrCompensationPayComponent(models.Model):
    _name = 'hr.compensation.pay.component'
    _description = 'Hr Compensation Pay Component'

    name = fields.Char('Name')
    code = fields.Char('Code')
    description = fields.Char('Description')


class HrCompensation(models.Model):
    _name = 'hr.compensation'
    _description = 'Hr Compensation'

    name = fields.Many2one('hr.compensation.pay.component', 'Pay Component')
    code = fields.Char(related='name.code', string='Code')
    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')
    amount = fields.Float('Amount', default=0.0)
    currency = fields.Many2one('res.currency', default=lambda x: x.env.company.currency_id)
    frequency = fields.Integer('Frequency')
    is_payroll = fields.Boolean('Is Payroll Element')
    value = fields.Char('Value (If not Payroll)')
    period = fields.Selection([('daily', 'Daily'), ('monthly', 'Monthly'), ('yearly', 'Yearly')], 'Period')
    related_job_position = fields.Many2one('hr.job', 'Related Job', copy=False)
    related_contract = fields.Many2one('hr.contract', 'Related Contract')
    component_description = fields.Char(
        string='Component Description',
        related='name.description')
    active = fields.Boolean(default=True)
    state = fields.Selection([('active', 'Active'), ('inactive', 'Inactive')], default='active', string="State",
                             required=True)

    _sql_constraints = [('uniq_components_contract',
                         'unique(id)',
                         'Pay Component must be unique per Contract'), ('uniq_components_position',
                                                                        'unique(id)',
                                                                        'Pay Component must be unique per Job Position')]

    @api.constrains('related_job_position', 'name', 'from_date', 'to_date')
    def _check_paycomponents_position(self):
        for rec in self:
            if rec.name and rec.related_job_position:
                prev_compensations = self.env['hr.compensation'].search(
                    [('related_job_position', '=', rec.related_job_position.id),
                     ('name', '=', rec.name.id), ('id', '!=', rec.id), ('state', '=', 'active'),
                     ('related_contract', '=', False)])
                if len(prev_compensations) > 0 and rec.state == 'active':
                    raise ValidationError(_("Pay Component must be unique per Job Position!"))

    @api.constrains('related_contract', 'name', 'from_date', 'to_date')
    def _check_paycomponents_contract(self):
        for rec in self:
            if rec.name and rec.related_contract:
                prev_compensations = self.env['hr.compensation'].search(
                    [('related_contract', '=', rec.related_contract.id),
                     ('name', '=', rec.name.id), ('id', '!=', rec.id), ('state', '=', 'active'),
                     ('related_job_position', '=', False)])
                if len(prev_compensations) > 0 and rec.state == 'active':
                    raise ValidationError(_("Pay Component must be unique per Contract!"))

    def write(self, vals):
        for rec in self:
            log = 'Component Line: ' + (
                vals.get('component_description') if (vals.get(
                    'component_description') is not None and vals.get(
                    'component_description')) else rec.component_description) + " : "
            log_post = False

            if vals.get('is_payroll') is not None:
                log += '<br/>' + 'Is Payroll Element: ' + str((rec.is_payroll if rec.is_payroll else '')) + ' → ' + str(
                    vals.get(
                        'is_payroll', ''))
                log_post = True

            if vals.get('state') is not None and vals.get('state'):
                log += '<br/>' + 'State: ' + (str(rec.state) if rec.state else '') + ' → ' + str(
                    vals.get('state', ''))
                log_post = True

            if vals.get('name') is not None and vals.get('name'):
                log += '<br/>' + 'Pay Component: ' + (rec.name.name if rec.name.name else '') + ' → ' + (self.env[
                                                                                                             'hr.compensation.pay.component'].browse(
                    vals.get(
                        'name', '')).name if self.env[
                    'hr.compensation.pay.component'].browse(vals.get(
                    'name', '')).name else '')
                log_post = True

            if vals.get('component_description') is not None and vals.get('component_description'):
                log += '<br/>' + 'Component Description: ' + (
                    rec.component_description if rec.component_description else '') + ' → ' + vals.get(
                    'component_description', '')
                log_post = True

            if vals.get('from_date') is not None and vals.get('from_date'):
                log += '<br/>' + 'From Date: ' + str((
                    rec.from_date if rec.from_date else '')) + ' → ' + str(vals.get('from_date', ''))
                log_post = True

            if vals.get('to_date') is not None and vals.get('to_date'):
                log += '<br/>' + 'To Date: ' + str((
                    rec.to_date if rec.to_date else '')) + ' → ' + str(vals.get('to_date', ''))
                log_post = True

            if vals.get('value') is not None and vals.get('value'):
                log += '<br/>' + 'Value: ' + (
                    rec.value if rec.value else '') + ' → ' + vals.get('value', '')
                log_post = True

            if vals.get('amount') is not None and vals.get('amount'):
                log += '<br/>' + 'Amount: ' + (str(rec.amount) if rec.amount else '') + ' → ' + str(
                    vals.get('amount', ''))
                log_post = True

            if vals.get('currency') is not None and vals.get('currency'):
                log += '<br/>' + 'Currency: ' + (rec.currency.name if rec.currency else '') + ' → ' + (self.env[
                    'res.currency'].browse(vals.get('currency', '')).name if self.env[
                    'res.currency'].browse(vals.get('currency', '')).name else '')
                log_post = True

            if vals.get('frequency') is not None and vals.get('frequency'):
                log += '<br/>' + 'Frequency: ' + str(rec.frequency if rec.frequency else '') + ' → ' + str(vals.get(
                    'frequency', ''))
                log_post = True

            if vals.get('period') is not None and vals.get('period'):
                log += '<br/>' + 'Period: ' + (rec.period if rec.period else '') + ' → ' + vals.get(
                    'period', '')
                log_post = True

        res = super(HrCompensation, self).write(vals)

        if log_post:
            if rec.related_contract:
                rec.related_contract.message_post(body=log)

        return res

    @api.model
    def create(self, vals):
        rec = super(HrCompensation, self).create(vals)
        if vals.get('component_description'):
            comp = vals.get('component_description')
        elif rec.component_description:
            comp = rec.component_description
        else:
            comp = ''
        log = 'Component Line Created: ' + comp + " : "
        log_post = False

        if vals.get('is_payroll') is not None:
            log += '<br/>' + 'Is Payroll Element: ' + str((rec.is_payroll if rec.is_payroll else ''))
            log_post = True

        if vals.get('state') is not None:
            log += '<br/>' + 'State: ' + (str(rec.state) if rec.state else '')
            log_post = True

        if vals.get('name') is not None:
            log += '<br/>' + 'Pay Component: ' + (rec.name.name if rec.name.name else '')
            log_post = True

        if vals.get('component_description') is not None:
            log += '<br/>' + 'Component Description: ' + (
                rec.component_description if rec.component_description else '')
            log_post = True

        if vals.get('from_date') is not None:
            log += '<br/>' + 'From Date: ' + str((rec.from_date if rec.from_date else ''))
            log_post = True

        if vals.get('to_date') is not None:
            log += '<br/>' + 'To Date: ' + str((rec.to_date if rec.to_date else ''))
            log_post = True

        if vals.get('value') is not None:
            log += '<br/>' + 'Value: ' + (rec.value if rec.value else '')
            log_post = True

        if vals.get('amount') is not None:
            log += '<br/>' + 'Amount: ' + (str(rec.amount) if rec.amount else '')
            log_post = True

        if vals.get('currency') is not None:
            log += '<br/>' + 'Currency: ' + (rec.currency.name if rec.currency else '')
            log_post = True

        if vals.get('frequency') is not None:
            log += '<br/>' + 'Frequency: ' + str(rec.frequency if rec.frequency else '')
            log_post = True

        if vals.get('period') is not None:
            log += '<br/>' + 'Period: ' + (rec.period if rec.period else '')
            log_post = True

        if log_post:
            if rec.related_contract:
                rec.related_contract.message_post(body=log)

        return rec


class CostCenter(models.Model):
    _name = 'hr.cost.center'
    _description = 'Cost Center'

    name = fields.Char("Name", store=True)
    code = fields.Char("Code", required=True)
    related_department = fields.Many2one('hr.department', "Related Department", ondelete='set null')

    def name_get(self):
        names = []
        for record in self:
            names.append((record.id, "%s - %s" % (record.code, record.name)))
        return names


class HrJobTitle(models.Model):
    _name = 'job.title'
    _description = 'Hr Job Title'

    name = fields.Char('Name')
    arabic_name = fields.Char('Arabic Name')


class HrJobGrade(models.Model):
    _name = 'job.grade'
    _description = 'Job Grade'

    name = fields.Char('Job Grade')
    level = fields.Integer('Job Grade Level')
    related_compensations = fields.Many2many('hr.compensation.pay.component', string='Related Compensations')
    notice_period = fields.Integer('Notice Period (Days)', default=30)
    probation_period = fields.Integer('Probation Period (Days)', default=30)
    grade_date = fields.Date("Grade Date")


department_types = [('BU', 'Group'), ('BD', 'Department'), ('BS', 'Section'),
                    ('SS', 'Subsection'), ]


class Department(models.Model):
    _inherit = "hr.department"

    type = fields.Selection(department_types, string='Type', default='BU')
    code = fields.Char('Code')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    @api.model
    def create(self, vals):
        res = super(Department, self).create(vals)
        if res.type == 'BU':
            res.code = self.env['ir.sequence'].next_by_code('business.unit')
        if res.type == 'BD':
            res.code = self.env['ir.sequence'].next_by_code('business.department')
        if res.type == 'BS':
            res.code = self.env['ir.sequence'].next_by_code('business.section')
        if res.type == 'SS':
            res.code = self.env['ir.sequence'].next_by_code('sub.section')
        return res


class IscoCode(models.Model):
    _name = "hr.isco.code"
    _description = 'Hr Isco Code'

    name = fields.Char('Label')
    code = fields.Char('Code')

    def name_get(self):
        names = []
        for record in self:
            names.append((record.id, "%s - %s" % (record.code, record.name)))
        return names


class Job(models.Model):
    _inherit = "hr.job"
    _description = "Job Position"

    name = fields.Char(string='Job Position', required=False, index=True, store=True)
    position_status = fields.Selection([('active', 'Active'), ('inactive', 'Inactive')], default='active')
    job_grade = fields.Many2one('job.grade', string='Job Grade')
    job_title = fields.Many2one('job.title', string='Job Title')
    default_manager = fields.Many2one('hr.employee', 'Reporting To')
    group = fields.Many2one('hr.department', string='Group', domain=[('type', '=', 'BU')])
    department_id = fields.Many2one('hr.department', string='Department', domain=[('type', '=', 'BD')])
    section = fields.Many2one('hr.department', string='Section', domain=[('type', '=', 'BS')])
    subsection = fields.Many2one('hr.department', string='Subsection', domain=[('type', '=', 'SS')])
    related_compensations = fields.One2many('hr.compensation', 'related_job_position', string='Related Compensations')
    isco_code = fields.Many2one('hr.isco.code', 'ISCO Code')
    cost_center = fields.Many2one('hr.cost.center', string="Cost Center")
    state = fields.Selection([
        ('recruit', 'Recruitment in Progress'),
        ('open', 'Not Recruiting')
    ], string='Status', readonly=False, required=True, copy=False, default='recruit',
        help="Set whether the recruitment process is open or closed for this job position.")

    related_jobs = fields.One2many('hr.contract', 'job_id', 'Related Jobs')
    panel_ids = fields.Many2many(
        comodel_name='res.users',
        string='Interview Panel')
    active = fields.Boolean('Active', default=True)
    arabic_name = fields.Char(string="Arabic Name")
    is_government = fields.Boolean(string="Government")

    _sql_constraints = [
        ('name_company_uniq', 'check(1=1)',
         'The name of the job position must be unique per department in company!'),
    ]

    @api.onchange('group')
    def _on_group_change(self):
        if self.group:
            # self.department = False
            # self.section = False
            # self.subsection = False
            return {'domain': {
                'department': [('type', '=', 'BD'),
                               ('parent_id', 'child_of', self.group.id)],
                'section': [('type', '=', 'BS'),
                            ('parent_id', 'child_of',
                             self.group.id)],
                'subsection': [('type', '=', 'SS'),
                               ('parent_id', 'child_of', self.group.id)]}}
        else:
            return {'domain': {'department': [('type', '=', 'BD')],
                               'section': [('type', '=', 'BS')],
                               'subsection': [('type', '=', 'SS')]}}

    @api.onchange('department_id')
    def _on_department_change(self):
        if self.department_id:
            # self.section = False
            # self.subsection = False
            return {'domain': {
                'section': [('type', '=', 'BS'),
                            ('parent_id', 'child_of',
                             self.department_id.id)],
                'subsection': [('type', '=', 'SS'),
                               ('parent_id', 'child_of', self.department_id.id)]}}
        elif self.group:
            return self._on_group_change()
        else:
            return {'domain': {
                'section': [('type', '=', 'BS')],
                'subsection': [('type', '=', 'SS')]}}

    @api.onchange('section')
    def _on_section_change(self):
        if self.section:
            # self.subsection = False
            return {'domain': {
                'subsection': [('type', '=', 'SS'),
                               ('parent_id', 'child_of', self.section.id)]}}
        elif self.department_id:
            return self._on_department_change()
        else:
            return {'domain': {
                'subsection': [('type', '=', 'SS')]}}

    @api.onchange('job_grade')
    def onchange_job_grade(self):
        if not self.related_jobs:
            lines = [(5, 0, 0)]
            if self.job_grade:
                for compensations in self.job_grade.related_compensations:
                    lines.append((0, 0, {'name': compensations}))
            self.related_compensations = lines

    @api.model
    def create(self, vals):
        # vals.update({'name': self.env['ir.sequence'].next_by_code('job.position')})
        result = super(Job, self).create(vals)
        default_signatures = self.env['hr.job.default.signature'].search([])
        for signature in default_signatures:
            result.write({
                'required_signatures': [(0, 0, {
                    'sequence': signature.sequence,
                    'name': signature.name.id
                })]
            })

        # result.message_subscribe(partner_ids=set([]))
        # department_manager = result.department_id.manager_id.user_id.partner_id.id
        # old_followers = set(result.message_follower_ids.mapped('partner_id.id'))
        # followers = (old_followers - set([department_manager]))
        # if followers:
        #     result.message_subscribe(partner_ids=followers)
        #     # sign_request.send_follower_accesses(self.env['res.partner'].browse(followers))

        return result

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        return super(Job, self).copy(default=default)


class ResUser(models.Model):
    _inherit = 'res.users'

    def name_get(self):
        names = []
        for record in self:
            names.append((record.id, "%s" % record.name))
        return names
