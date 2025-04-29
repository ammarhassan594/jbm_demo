# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.osv import expression
import datetime
from odoo.exceptions import AccessError, ValidationError, UserError
from lxml import etree
import json
from dateutil.relativedelta import relativedelta


class Survey(models.Model):
    _inherit = 'survey.survey'

    category = fields.Selection([('hr_trial', 'Trial Period')])


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    code = fields.Char('Working Times Code')


class TrialPeriodL1Wizard(models.TransientModel):
    _name = 'trial.period.l1.wizard'
    _description = 'Trial Period Wizard'

    related_trial_period = fields.Many2one(
        comodel_name='trial.period',
        string='Probation Assessment',
        required=True)
    l1_question_1 = fields.Text(
        string="Does the employee have a positive attitude towards his/her work and team/project members?",
        required=True)
    l1_question_2 = fields.Text(
        string="Do you have any concerns regarding the Employee's performance in his/her role so far?", required=True)

    def submit_l1(self):
        if self.related_trial_period.due_date > 15:
            raise ValidationError('No action can be taken before 15 days of the end of probation')
        self.related_trial_period.write(
            {'state': 'pendingl2', 'l1_question_1': self.l1_question_1, 'l1_question_2': self.l1_question_2})


class TrialPeriodL2Wizard(models.TransientModel):
    _name = 'trial.period.l2.wizard'
    _description = 'Trial Period L2 Wizard'

    related_trial_period = fields.Many2one(
        comodel_name='trial.period',
        string='Probation Assessment',
        required=True)
    l1_question_1 = fields.Text(related='related_trial_period.l1_question_1')
    l1_question_2 = fields.Text(related="related_trial_period.l1_question_2")
    l2_decision = fields.Selection(
        string='Final Decision',
        selection=[('confirm', 'Confirm Employment'),
                   ('extend', 'Extend Probation'), ('terminate', 'Terminate Employee')],
        required=True)
    l2_justification = fields.Text(
        string="Decision Justification",
        required=True)

    def submit_l2(self):
        self = self.sudo()
        decision = self.l2_decision
        if decision == 'confirm':
            conf_date = self.related_trial_period.related_contract.trial_date_end + datetime.timedelta(
                days=1)
            self.related_trial_period.write(
                {'state': 'done', 'l2_decision': self.l2_decision, 'l2_justification': self.l2_justification,
                 'confirmation_date': conf_date})
            self.related_trial_period.related_contract.write(
                {'confirmation_date': conf_date})
            # template = self.env.ref('auth_signup.mail_template_data_unregistered_users').with_context({
            #     'email_to': self.related_employee.user_partner_id.email})
            # template.send_mail(self.env.user)
            self.related_trial_period.related_contract.message_notify(
                partner_ids=self.related_trial_period.related_employee.user_partner_id.ids,
                body="Probation assessment done, employee's employment has been confirmed",
                subject="Assessment")
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        elif decision == 'terminate':
            self.related_trial_period.related_contract.write(
                {'state': 'cancel'})
            self.related_trial_period.write(
                {'state': 'terminated', 'l2_decision': self.l2_decision, 'l2_justification': self.l2_justification})
        elif decision == 'extend':
            if not self.related_trial_period.extended_from:
                self.env['trial.period'].create({
                    'start_date': self.related_trial_period.end_date + datetime.timedelta(
                        days=1),
                    'end_date': self.related_trial_period.end_date + datetime.timedelta(
                        days=1) + datetime.timedelta(
                        days=self.related_trial_period.related_contract.job_id.job_grade.probation_period),
                    'related_contract': self.related_trial_period.related_contract.id,
                    'extended_from': self.id
                })
                self.related_trial_period.related_contract.write(
                    {'trial_date_end': self.related_trial_period.end_date + datetime.timedelta(
                        days=1) + datetime.timedelta(
                        days=self.related_trial_period.related_contract.job_id.job_grade.probation_period), })
                self.related_trial_period.write(
                    {'state': 'extended', 'l2_decision': self.l2_decision, 'l2_justification': self.l2_justification})
                self.related_trial_period.related_contract.message_notify(
                    partner_ids=self.related_trial_period.related_employee.user_partner_id.ids,
                    body="Probation assessment done, The probation period will been extended till %s" % (
                        self.related_trial_period.related_contract.trial_date_end),
                    subject="Assessment")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
            else:
                raise ValidationError('Probation Assessment cannot be extended twice!')


class TrialPeriod(models.Model):
    _name = 'trial.period'
    _description = 'Trial Period'

    state = fields.Selection(
        [('pendingl1', 'Pending LM1'), ('pendingl2', 'Pending LM2'),
         ('done', 'Employment Confirmed'), ('extended', 'Probation Extended'),
         ('terminated', 'Employment Terminated'),
         ('done', 'Done')],
        string='Status',
        readonly=True, required=True, tracking=True, copy=False, default='pendingl1')
    start_date = fields.Date('Date Of Joining', readonly=True, states={'pendingl1': [('readonly', False)]})
    end_date = fields.Date('End Of Probation Date', readonly=True, states={'pendingl1': [('readonly', False)]})
    confirmation_date = fields.Date("Probation Confirmation Date", readonly=True)
    related_contract = fields.Many2one('hr.contract', 'Employee', ondelete='cascade')
    related_employee = fields.Many2one(related='related_contract.employee_id', string="Related Employee")
    user_id = fields.Many2one(related='related_employee.user_id')
    survey_id = fields.Many2one('survey.survey', string="Survey",
                                domain=[('category', '=', 'hr_trial')], required=False, readonly=True,
                                states={'pendingl1': [('readonly', False)]})
    response_id = fields.Many2one('survey.user_input', "Response", ondelete="set null", readonly=True,
                                  states={'pendingl1': [('readonly', False)]})
    extended_from = fields.Many2one('trial.period', 'Extended From', readonly=True)
    can_do_survey = fields.Boolean('can do interview', compute="_can_do_survey")
    can_approve_survey = fields.Boolean('can approve interview', compute="_can_approve_survey")
    calculate_due_date = fields.Boolean('Cal', compute="_calculate_get_due_date")
    due_date = fields.Integer('Due Date', compute="_get_due_date", store=True)
    l1_employee = fields.Many2one(related='related_contract.employee_id.parent_id', string="Line Manager 1")
    l2_employee = fields.Many2one(related='related_contract.employee_id.parent_id.parent_id', string="Line Manager 2")
    l1_question_1 = fields.Text(
        string="Does the employee have a positive attitude towards his/her work and team/project members?",
        required=False)
    l1_question_2 = fields.Text(
        string="Do you have any concerns regarding the Employee's performance in his/her role so far?", required=False)
    l2_decision = fields.Selection(
        string='Final Decision',
        selection=[('confirm', 'Confirm Employment'),
                   ('extend', 'Extend Probation'), ('terminate', 'Terminate Employee')],
        required=False)
    l2_justification = fields.Text(
        string="Decision Justification",
        required=False)
    is_l1 = fields.Boolean(
        string='Is L1 Manager',
        compute='_is_l1')
    is_l2 = fields.Boolean(
        string='Is L2 Manager',
        compute='_is_l2')

    def name_get(self):
        names = []
        for record in self:
            names.append((record.id, "%s - %s" % (
                record.related_employee.name, dict(self._fields['state'].selection).get(record.state))))
        return names

    def _is_l1(self):
        for rec in self:
            if rec.l1_employee.user_id.id == self.env.uid:
                rec.is_l1 = True
            else:
                rec.is_l1 = False

    def _is_l2(self):
        for rec in self:
            if rec.l2_employee.user_id.id == self.env.uid or self.env.user.has_group(
                    'security_rules.group_hc_employee'):
                rec.is_l2 = True
            else:
                rec.is_l2 = False

    def _calculate_get_due_date(self):
        for rec in self:
            rec.calculate_due_date = True
            if rec.state in ('pendingl1', 'pendingl2'):
                rec._get_due_date()

    @api.depends('calculate_due_date')
    def _get_due_date(self):
        for rec in self:
            if rec.end_date:
                days = (rec.end_date - fields.Date.today()).days
                if days < 0:
                    days = 0
                rec.due_date = (rec.end_date - fields.Date.today()).days
            else:
                rec.due_date = 0

    def _can_do_survey(self):
        for probation in self:
            probation.can_do_survey = True if (
                    probation.related_employee.parent_id.user_id == self.env.user) else False
            if probation.due_date > 15:
                probation.can_do_survey = False

    def _can_approve_survey(self):
        for probation in self:
            probation.can_approve_survey = True if (
                    probation.related_employee.parent_id.parent_id.user_id == self.env.user) else False
            if probation.due_date > 15:
                probation.can_approve_survey = False

    def submit_probation_survey(self):
        if self.due_date > 15:
            raise ValidationError('No action can be taken before 15 days of the end of probation')
        if self.response_id.state == 'done':
            self.write({'state': 'pendingl2'})
        else:
            raise ValidationError('Please finish the Probation Assessment before submitting.')

    def action_start_survey(self):
        self.ensure_one()
        # create a response and link it to this applicant
        if not self.response_id:
            response = self.survey_id._create_answer(partner=self.env.user.partner_id)
            self.response_id = response.id
        else:
            response = self.response_id
        # grab the token of the response and start surveying
        action = self.survey_id.with_context(survey_token=response.token).action_start_survey()
        action.update({'target': 'new'})
        return action

    def action_print_survey(self):
        """ If response is available then print this response otherwise print survey form (print template of the survey) """
        self.ensure_one()
        if not self.response_id:
            action = self.survey_id.action_print_survey()
            action.update({'target': 'new'})
            return action
        else:
            response = self.response_id
            action = self.survey_id.with_context(survey_token=response.token).action_print_survey()
            action.update({'target': 'new'})
            return action

    def set_done(self):
        if self.response_id.state == 'done':
            self.write({'state': 'done'})
            self.related_contract.write(
                {'confirmation_date': self.related_contract.trial_date_end + datetime.timedelta(days=1)})
            # template = self.env.ref('auth_signup.mail_template_data_unregistered_users').with_context({
            #     'email_to': self.related_employee.user_partner_id.email})
            # template.send_mail(self.env.user)
            self.related_contract.message_notify(
                partner_ids=self.related_employee.user_partner_id.ids,
                body="Probation assessment done, employee's employment has been confirmed",
                subject="Assessment")
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

    def set_terminate(self):
        if self.response_id.state == 'done':
            self.related_contract.write(
                {'state': 'cancel'})
            self.write({'state': 'terminated'})

    def set_extend(self):
        if self.response_id.state == 'done':
            if not self.extended_from:
                self.env['trial.period'].create({
                    'start_date': self.end_date,
                    'end_date': self.end_date + datetime.timedelta(
                        days=self.related_contract.job_id.job_grade.probation_period),
                    'related_contract': self.related_contract.id,
                    'survey_id': self.survey_id.id,
                    'extended_from': self.id
                })
                self.related_contract.write(
                    {'trial_date_end': self.related_contract.trial_date_end + datetime.timedelta(
                        days=self.related_contract.job_id.job_grade.probation_period), })
                self.write({'state': 'extended'})
                self.related_contract.message_notify(
                    partner_ids=self.related_employee.user_partner_id.ids,
                    body="Probation assessment done, The probation period will been extended till %s" % (
                        self.related_contract.trial_date_end),
                    subject="Assessment")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
            else:
                raise ValidationError('Probation Assessment cannot be extended twice!')


class ContractGroup(models.Model):
    _name = 'hr.contract.group'
    _description = 'HR Contract Group'

    name = fields.Char('Contract Group')
    code = fields.Char('Contract Group Code')


class ContractGroup(models.Model):
    _name = 'hr.contract.group'
    _description = 'HR Contract Group'

    name = fields.Char('Contract Group')
    code = fields.Char('Contract Group Code')


class StandardWeeklyHours(models.Model):
    _name = 'standard.weekly.hours'
    _description = 'Standard Weekly Hours'

    name = fields.Char('Name')
    code = fields.Char('Code')


class ContractSubgroup(models.Model):
    _name = 'hr.contract.subgroup'
    _description = 'Contract Sub Group'

    name = fields.Char('Contract Subgroup')
    code = fields.Char('Contract Subgroup Code')


class HrContractType(models.Model):
    _name = 'hr.contract.type'
    _description = 'Hr Contract Type'

    name = fields.Char('Contract Type')
    code = fields.Char('Contract Type Code')
    related_employment_status = fields.Selection([('contractor', 'Contractor'), ('permanent', 'Permanent')],
                                                 'Employment Status')


class HrPayrollArea(models.Model):
    _name = 'hr.payroll.area'
    _description = 'HR Payroll Area'

    name = fields.Char('Payroll Area')
    code = fields.Char('Payroll Area Code')


class HrPayType(models.Model):
    _name = 'hr.pay.type'
    _description = 'Hr Pay Type'

    name = fields.Char('Pay Type')
    code = fields.Char('Pay Type Code')


class HrPayscaleGroup(models.Model):
    _name = 'hr.payscale.group'
    _description = 'Hr Payscale Group'

    name = fields.Char('Payscale Group')
    code = fields.Char('Payscale Group Code')
    related_level = fields.One2many('hr.payscale.level', 'related_group', "Related Levels")


class HrPayscaleLevel(models.Model):
    _name = 'hr.payscale.level'
    _description = 'Hr Payscale Level'

    name = fields.Char('Payscale Level')
    code = fields.Char('Payscale Level Code')
    related_group = fields.Many2one('hr.payscale.group', "Related Goup")


class Contract(models.Model):
    _inherit = 'hr.contract'

    name = fields.Char('Contract Reference', required=True, default='Draft')
    section = fields.Many2one('hr.department', string='Section', domain=[('type', '=', 'BS')])
    subsection = fields.Many2one('hr.department', string='Subsection', domain=[('type', '=', 'SS')])
    group = fields.Many2one('hr.department', string='Group', domain=[('type', '=', 'BU')])
    department = fields.Many2one('hr.department', string='Department',
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    department_id = fields.Many2one('hr.department',
                                    domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                    string="Current OC Path")

    related_resign_request = fields.One2many('hr.resignation', 'related_contract', 'Resignation Requests')
    effective_end_date = fields.Date(string='Effective End Date',
                                     help="Effective End date of the contract")

    related_trial_request = fields.One2many('trial.period', 'related_contract', 'Probation Assessments')
    default_survey_id = fields.Many2one('survey.survey', string="Probation Period Survey",
                                        domain=[('category', '=', 'hr_trial')])
    trial_date_end = fields.Date('End of Probation Period',
                                 help="End date of the trial period (if there is one).")
    part_time_date_end = fields.Date('Part Time End Date')

    # hiring_type = fields.Selection(related="job_id.requisition_type", string='Hiring Type')
    manager_id = fields.Many2one('hr.employee', 'Manager',
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    job_title = fields.Many2one(related="job_id.job_title")
    arabic_job_title = fields.Char(related="job_title.arabic_name", string="Job Title (Arabic)")
    job_grade = fields.Many2one(related="job_id.job_grade")
    employment_status = fields.Selection([('contractor', 'Contractor'), ('permanent', 'Permanent')],
                                         'Employment Status')
    contract_group = fields.Many2one('hr.contract.group', 'Contract Group')

    contract_type = fields.Many2one('hr.contract.type', 'Contract Type',
                                    domain="[('related_employment_status', '=', employment_status)]")

    contract_subgroup = fields.Many2one('hr.contract.subgroup', 'Contract Subgroup')

    working_days_week = fields.Integer('Working Days/Week')

    overtime_eligibility = fields.Boolean('Overtime Eligibility')

    hiring_date = fields.Date(string="Hiring Confirmation Date", related='applicant_id.hiring_date')

    cost_center = fields.Many2one('hr.cost.center', string="Cost Center")

    confirmation_date = fields.Date("Probation Confirmation Date")
    cid_date_issue = fields.Date('CID Date of Issue')
    cid_end_date = fields.Date('CID End Date')
    cid_type = fields.Selection([('open', 'Open'), ('temp', 'Temporary'), ('limited', 'Limited')], 'CID Type')
    standard_weekly_hours = fields.Many2one(
        comodel_name='standard.weekly.hours',
        string='Standard Weekly Hours',
        required=False)

    inactive_related_compensation = fields.One2many('hr.compensation', 'related_contract',
                                                    domain=[('state', '=', 'inactive')],
                                                    string='Inactive Salary Compensation')

    e_contract_document_date = fields.Date(string='E-Contract Document Date',
                                           compute='compute_e_contract_document_date')
    e_contract_attested_date = fields.Date(string='E-Contract Attested Date')
    # contract_validity = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('unlimited', 'Unlimited')],
    #                                      string='Contract Validity')
    contract_validity = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'),
                                          ('8', '8'),('9', '9'),('10', '10'),('11', '11'),('12', '12'),('13', '13'),('14', '14'),
                                          ('15', '15'),('16', '16'),('17', '17'),('18', '18'),('19', '19'),('20', '20'),('21', '21'),
                                          ('22', '22'),('23', '23'),('24', '24'),('25', '25')],
                                         string='Contract Validity')
    pay_type_id = fields.Many2one('hr.payroll.area', 'Payroll Area')
    payroll_area_id = fields.Many2one('hr.pay.type', 'Pay Type')
    payscale_group = fields.Many2one('hr.payscale.group', 'Payscale Group')
    payscale_level = fields.Many2one('hr.payscale.level', 'Payscale Level',
                                     domain="[('related_group','=',payscale_group)]")
    wage = fields.Monetary('Basic Salary', required=True, tracking=True, default=0.0)
    wizard_name = fields.Char(string="Wizard Name")
    employment_wizard_name = fields.Char(string="Employment wizard Name")
    car_allowance = fields.Float(string="Car Allowance")
    social_allowance = fields.Float(string="Social Allowance")

    @api.onchange('contract_validity', 'date_start')
    def onchange_contract_validity(self):
        for record in self:
            if record.contract_validity and record.date_start:
                record.date_end = record.date_start + relativedelta(years=int(record.contract_validity))
            else:
                record.date_end = False

    @api.depends('employee_id')
    def compute_e_contract_document_date(self):
        for rec in self:
            if rec.employee_id:
                e_contract_doc_id = self.env['documents.document'].search(
                    [('employee_id', '=', rec.employee_id.id), ('status', '=', 'active'),
                     ('document_type_name', '=', 'E-Contract')], limit=1)
                if e_contract_doc_id:
                    rec.e_contract_document_date = e_contract_doc_id.issue_date
                else:
                    rec.e_contract_document_date = False
            else:
                rec.e_contract_document_date = False

    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(Contract, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                    submenu=submenu)
        if view_type == "form" and self.env.user.has_group('security_rules.group_hr_employee'):
            doc = etree.XML(res['arch'])
            for field in res['fields']:
                if field != 'job_id' and field != 'employee_id' and field != 'default_survey_id':
                    for node in doc.xpath("//field[@name='%s']" % field):
                        node.set("options", "{'no_open': True}")
                        modifiers = json.loads(node.get("modifiers"))
                        if not modifiers.get('options'):
                            modifiers['options'] = "{'no_open': True}"
                        node.set("modifiers", json.dumps(modifiers))

            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    @api.onchange('employee_id', 'date_start')
    def get_contract_name(self):
        rec = self._origin
        origin_name = ""
        if rec.employee_id and rec.date_start:
            origin_name = str(rec.employee_id.name) + ' - Contract - ' + rec.date_start.strftime("%d/%m/%Y")
        if not self.name or self.name == 'Draft' or self.name == origin_name and self.date_start and self.employee_id:
            self.name = str(self.employee_id.name) + ' - Contract - ' + self.date_start.strftime("%d/%m/%Y")

    @api.constrains('employee_id', 'state', 'kanban_state', 'date_start', 'date_end')
    def _check_current_contract(self):
        """ Two contracts in state [incoming | open | close] cannot overlap """
        for contract in self.filtered(
                lambda c: c.state not in ['draft', 'cancel'] or c.state == 'draft' and c.kanban_state == 'done'):
            domain = [
                ('id', '!=', contract.id),
                ('employee_id', '=', contract.employee_id.id),
                '|',
                ('state', 'in', ['open', 'close']),
                '&',
                ('state', '=', 'draft'),
                ('kanban_state', '=', 'done')  # replaces incoming
            ]

            if not contract.date_end:
                start_domain = []
                end_domain = ['|', ('date_end', '>=', contract.date_start), ('date_end', '=', False)]
            else:
                start_domain = [('date_start', '<=', contract.date_end)]
                end_domain = ['|', ('date_end', '>', contract.date_start), ('date_end', '=', False)]

            domain = expression.AND([domain, start_domain, end_domain])
            if self.search_count(domain) and contract.employee_id:
                raise ValidationError(_(
                    'An employee can only have one contract at the same time. (Excluding Draft and Cancelled contracts)'))

    @api.depends('related_compensation')
    def _get_total_wages(self):
        if self.related_compensation:
            self.wage = sum(self.related_compensation.filtered(lambda x: x.is_payroll == True).mapped('amount'))
        else:
            self.wage = 0.0

    @api.onchange('group')
    def _on_group_change(self):
        if self.group:
            self.department = False
            self.section = False
            self.subsection = False
            self.department_id = self.group
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

    @api.onchange('department')
    def _on_department_change(self):
        if self.department:
            self.section = False
            self.subsection = False
            self.department_id = self.department
            return {'domain': {
                'section': [('type', '=', 'BS'),
                            ('parent_id', 'child_of',
                             self.department.id)],
                'subsection': [('type', '=', 'SS'),
                               ('parent_id', 'child_of', self.department.id)]}}
        elif self.group:
            return self._on_group_change()
        else:
            return {'domain': {
                'section': [('type', '=', 'BS')],
                'subsection': [('type', '=', 'SS')]}}

    @api.onchange('section')
    def _on_section_change(self):
        if self.section:
            self.subsection = False
            self.department_id = self.section
            return {'domain': {
                'subsection': [('type', '=', 'SS'),
                               ('parent_id', 'child_of', self.section.id)]}}
        elif self.department:
            return self._on_department_change()
        else:
            return {'domain': {
                'subsection': [('type', '=', 'SS')]}}

    @api.onchange('subsection')
    def _on_subsection_change(self):
        if self.subsection:
            self.department_id = self.subsection

    def _get_compensations(self):
        line = [{'name': "Pay Component", 'amount': "Amount", 'description': "Description", 'bold': True}]

        for comp in self.related_compensation.filtered(lambda x: x.is_payroll == True):
            line.append({'name': comp.name.name, 'amount': comp.amount, 'description': comp.component_description,
                         'bold': False})

        line.append({'name': "", 'amount': self.wage, 'description': "Total Monthly Salary (AED)", 'bold': True})
        return line

    def _get_benefits(self):
        line = []
        for comp in self.related_compensation.filtered(lambda x: x.is_payroll == False):
            line.append({'name': comp.name.name, 'amount': comp.value})
        return line

    def _get_signatures(self):
        line = []
        for comp in self.required_signatures:
            user = comp.name
            employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
            if employee.id:
                job_title = employee.job_title
                line.append({'name': job_title, 'signature': comp.signature})
        return line

    @api.onchange('date_start')
    def on_change_date_start(self):
        if self.date_start:
            self.trial_date_end = self.date_start + datetime.timedelta(days=self.job_id.job_grade.probation_period)

    # @api.onchange('trial_date_end')
    # def on_change_trial_date(self):
    #     if self.trial_date_end:
    #         self.trial_date_end = self.trial_date_end + datetime.timedelta(days=1)

    def action_offer_print(self):
        return self.env.ref('hr_contract_custom.contract_job_offer').report_action(self)

    def _assign_open_contract(self):
        for contract in self:
            if contract.employee_id:
                contract.employee_id.sudo().write({'contract_id': contract.id})

    def action_contract_signed(self):
        # todo task #34
        pending_signatures = self.env['hr.contract.signature'].search(
            [('hr_contract_id', '=', self.id), ('signature', '=', False)])

        if len(pending_signatures) > 0:
            raise ValidationError(_('All required signatures must be signed before proceeding.'))

        if not self.related_trial_request.filtered(lambda x: x.state in ('done', 'terminated')):
            self.env['trial.period'].create({
                'start_date': self.date_start,
                'end_date': self.trial_date_end,
                'related_contract': self.id,
                # 'survey_id': self.default_survey_id.id,
            })
        if self.applicant_id:
            stage = self.env['hr.recruitment.stage'].search([('create_employee', '=', True)])
            self.applicant_id.write({'stage_id': stage.id})
        sequence = self.name
        # if self.name == "Draft":
        #     # sequence = self.env['ir.sequence'].next_by_code('hr.contract')
        #     name = str(self.employee_id.name) + ' - Contract - ' + self.date_start.strftime("%d/%m/%Y")
        self.write({'state': 'open'})

    def action_job_offer_sent(self):
        self.ensure_one()
        template = self.env.ref('hr_contract_custom.email_template_job_offer', raise_if_not_found=False)
        compose_form = self.env.ref('hr_contract_custom.job_offer_send_wizard_form', raise_if_not_found=False)
        ctx = dict(
            default_model='hr.contract',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            # custom_layout="mail.mail_notification_paynow",
            force_email=True
        )
        return {
            'name': ('Send Job Offer'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'job.offer.send',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    required_signatures = fields.One2many('hr.contract.signature', 'hr_contract_id', string='Required Signatures',
                                          ondelete='cascade')

    def name_get(self):
        return [
            (contract.id, contract.name + ((" - " + contract.employee_id.name) if contract.employee_id else ''))
            for contract in self]

    #     @api.model
    #     def create(self, vals):
    #         applicant_id = vals.get('applicant_id', '')
    #         if applicant_id != '':
    #             applicantt = self.env['hr.applicant'].browse(applicant_id)
    #             if not applicantt.stage_id.generate_contract:
    #                 raise ValidationError(_("You can't create a contract at this stage"))

    #         result = super(Contract, self).create(vals)
    #         applicant = result.applicant_id
    #         job = applicant.job_id
    #         required_signatures = job.required_signatures

    #         fill_values = [(0, 0, {'name': required_signature.name.id, 'sequence': required_signature.sequence}) for
    #                        required_signature in required_signatures]
    #         result.required_signatures = fill_values

    #         if (len(required_signatures) > 0):
    #             first_signature = min(required_signatures, key=lambda x: x.sequence)
    #             first_user = first_signature.name if first_signature else None
    #
    #             msg = _(
    #                 'A signature is required by ') + ': <a href=# data-oe-model=res.users data-oe-id=%d>%s</a>' % (
    #                       first_user.id, first_user.name)
    #             # for rec in self:
    #             result.message_post(body=msg)

    #         return result

    def write(self, vals):
        state = vals.get('state', '')
        if state == 'open':
            contract = self.search([('employee_id', 'in', self.mapped('employee_id').ids), ('state', '=', 'open')])
            if contract:
                raise ValidationError(_("Employee has already have current running contract "))

        return super(Contract, self).write(vals)


class HrContractHistoryInherit(models.Model):
    _inherit = 'hr.contract.history'

    employee_type = fields.Selection(related="employee_id.employee_type")
