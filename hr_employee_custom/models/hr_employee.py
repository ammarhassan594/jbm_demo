from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from lxml import etree
from datetime import datetime, timedelta, date
from dateutil import relativedelta
import json
from ast import literal_eval

Religions_list = [
    ('apostolic', 'Apostolic'),
    ('baptist', 'Baptist'),
    ('buddhist', 'Buddhist'),
    ('charismatic', 'Charismatic'),
    ('evang', 'Evang'),
    ('lutheran-church', 'Lutheran Church'),
    ('evangelical', 'Evangelical'),
    ('free-church-alzey', 'Free church Alzey'),
    ('free-religion-of-the-den', 'Free religion of the den'),
    ('french-reformed', 'French reformed'),
    ('hebrew-reg-baden', 'Hebrew reg. BADEN'),
    ('hebrew-reg-wuertbg', 'Hebrew reg. WUERTBG'),
    ('hebrew-state', 'Hebrew state'),
    ('hindu', 'Hindu'),
    ('islamic', 'Islamic'),
    ('israelite', 'Israelite'),
    ("jehovah-s-witness", "Jehovah's witness"),
    ('mennonite-church', 'Mennonite Church'),
    ('jewish', 'Jewish'),
    ('mennonite-church', 'Mennonite Church'),
    ('mormon', 'Mormon'),
    ('moravian-congregation', 'Moravian Congregation'),
    ('muslim', 'Muslim'),
    ('netherl', 'Netherl'),
    ('netherl-reformed-church', 'Netherl. Reformed Church'),
    ('new-apostolic', 'New apostolic'),
    ('no-denomination', 'No denomination'),
    ('old-catholic', 'Old Catholic'),
    ('oecumenic', 'Oecumenic'),
    ('protestant', 'Protestant'),
    ('roman-catholic', 'Roman Catholic'),
    ("shia-muslim", "Shi'a Muslim"),
    ('sunni-muslim', 'Sunni Muslim'),
    ('christian', 'Christian'),
    ('christian-reformed', 'Christian Reformed'),
]


def get_dep(dep, level):
    if not dep.id:
        return False
    dep_type = dep.type
    if dep_type == level:
        return dep.id
    else:
        return get_dep(dep.parent_id, level)


class EmployeeEvent(models.Model):
    _name = 'hr.employee.event'
    _description = 'HR Employee Event'

    name = fields.Many2one(
        comodel_name='sap.event.type',
        string='Event Type',
        required=True)
    event_reason = fields.Many2one(
        comodel_name='sap.event.type.reason',
        string='Event Reason',
        required=False)
    start_date = fields.Datetime(
        string='Effective Date',
        required=True)
    end_date = fields.Datetime(
        string='End Date',
        required=False)
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=True, ondelete='cascade')
    is_processed = fields.Boolean(
        string='Is SAP Processed',
        required=True, default=False)
    is_triggered = fields.Boolean(
        string='Is Schedule Processed',
        required=True, default=False)
    update_info = fields.Boolean(
        string='Update Employee Information',
        required=True, default=True)

    old_active_salary = fields.Float(
        string='Old Active Salary',
        required=False)
    new_active_salary = fields.Float(
        string='New Active Salary',
        required=False)

    related_requisition = fields.Many2one('approval.request', string='Related Requisition')

    employee_fusion_id = fields.Char(string='Main Company ID', required=False)

    org_unit = fields.Char(string='Org Unit', required=False)
    org_unit_fkey = fields.Many2one(comodel_name='hr.department', string='Org Unit', required=False)

    line_manager_id = fields.Char(string='Line Manager', required=False)
    line_manager_id_fkey = fields.Many2one(comodel_name='hr.employee', string='Line Manager', required=False)

    position_code = fields.Char(string='Position', required=False)
    position_code_fkey = fields.Many2one(comodel_name='hr.job', string='Position', required=False)

    job_title_fkey = fields.Many2one(comodel_name='job.title', string='Job Title', required=False)

    cost_center = fields.Char(string='Cost Center', required=False)
    cost_center_fkey = fields.Many2one(comodel_name='hr.cost.center', string='Cost Center', required=False)

    employee_group = fields.Char(string='Employee Group', required=False)
    employee_group_fkey = fields.Many2one(comodel_name='hr.contract.group', string='Employee Group', required=False)

    employee_sub_group = fields.Char(string='Employee SubGroup', required=False)
    employee_sub_group_fkey = fields.Many2one(comodel_name='hr.contract.subgroup', string='Employee SubGroup',
                                              required=False)

    payroll_area = fields.Char(string='Payroll Area', required=False)
    payroll_area_fkey = fields.Many2one(comodel_name='hr.payroll.area', string='Payroll Area', required=False)

    contract_type = fields.Char(string='Contract Type', required=False)
    contract_type_fkey = fields.Many2one(comodel_name='hr.contract.type', string='Contract Type', required=False)

    probation_end_date = fields.Datetime(string='Probation End Date', required=False)
    confirmation_date = fields.Datetime(string='Confirmation Date', required=False)

    salutation = fields.Char(string='Salutation', required=False)
    salutation_fkey = fields.Many2one(comodel_name='res.partner.title', string='Salutation', required=False)

    first_name = fields.Char(string='First Name', required=False)
    middle_name = fields.Char(string='Middle Name', required=False)
    last_name = fields.Char(string='Last Name', required=False)
    birth_date = fields.Datetime(string='Birth Date', required=False)

    gender = fields.Char(string='Gender', required=False)
    gender_fkey = fields.Selection(
        string='Gender',
        selection=[('male', 'Male'),
                   ('female', 'Female')],
        required=False)

    nationality = fields.Char(string='Nationality', required=False)
    nationality_fkey = fields.Many2one(comodel_name='res.country', string='Nationality', required=False)

    birth_country = fields.Char(string='Birth Country', required=False)
    birth_country_fkey = fields.Many2one(comodel_name='res.country', string='Birth Country', required=False)

    shift_type = fields.Char(string='Shift Type', required=False)
    shift_type_fkey = fields.Many2one(comodel_name='resource.calendar', string='Shift Type', required=False)

    ot_eligibility = fields.Boolean(string='Overtime Eligibility', required=False)
    system_id = fields.Char(string='System ID', required=False)
    email_id = fields.Char(string='Email', required=False)

    payscale_group = fields.Char(string='Payscale Group', required=False)
    payscale_group_fkey = fields.Many2one(comodel_name='hr.payscale.group', string='Payscale Group', required=False)

    payscale_level = fields.Char(string='Payroll Level', required=False)
    payscale_level_fkey = fields.Many2one(comodel_name='hr.payscale.level', string='Payroll Level', required=False)

    related_compensations = fields.One2many(related='employee_id.contract_id.related_compensation', readonly=False)
    related_inactive_compensations = fields.One2many(related='employee_id.contract_id.inactive_related_compensation',
                                                     readonly=False)
    related_compensation = fields.One2many('event.compensation', 'related_event', string='Related Compensation')
    inactive_related_compensation = fields.One2many('event.compensation', 'related_event',
                                                    domain=[('state', '=', 'inactive')],
                                                    string='Inactive Salary Compensation')
    is_esd = fields.Boolean(string='Change To Contract Salary Components', required=True, default=False)

    @api.onchange('name')
    def onchange_event_type(self):
        self.event_reason = False
        return {'domain': {'event_reason': [('event_type_id', '=', self.name.id)]}}

    @api.onchange('is_esd')
    def onchange_esd(self):
        for rec in self:
            rec.old_active_salary = 0
            rec.new_active_salary = 0
            for comp in rec.related_compensation:
                if comp.state == 'active':
                    rec.old_active_salary += comp.amount
                    rec.new_active_salary += comp.amount

    @api.onchange('related_compensation')
    def onchange_comp(self):
        for rec in self:
            rec.new_active_salary = 0
            for comp in rec.related_compensation:
                if comp.state == 'active':
                    rec.new_active_salary += comp.amount

    @api.onchange('payscale_group_fkey')
    def onchange_payscale_group(self):
        if self.payscale_level_fkey.related_group.id != self.payscale_group_fkey.id:
            self.payscale_level_fkey = False
        return {'domain': {'payscale_level_fkey': [('related_group', '=', self.payscale_group_fkey.id)]}}

    @api.onchange('position_code_fkey')
    def onchange_position(self):
        self = self.sudo()
        self.job_title_fkey = self.position_code_fkey.job_title.id

    @api.onchange('employee_id')
    def onchange_employee(self):
        self = self.sudo()
        employee = self.employee_id

        fusion_id = employee.fusion_id

        real_employee = self.env['hr.employee'].search([('fusion_id', '=', fusion_id)], limit=1)
        if not str(self.id).startswith('<NewId'):
            events = self.search([('employee_id', '=', real_employee.id), ('id', '!=', self.id)],
                                 order="start_date desc")
        else:
            events = self.search([('employee_id', '=', real_employee.id)], order="start_date desc")

        if len(events) == 0:
            self.employee_fusion_id = employee.fusion_id if employee.fusion_id else ''
            self.org_unit_fkey = employee.department_id.id
            self.line_manager_id_fkey = employee.parent_id.id
            self.position_code_fkey = employee.job_id.id
            self.job_title_fkey = employee.contract_id.job_title.id
            self.cost_center_fkey = employee.contract_id.cost_center.id
            self.employee_group_fkey = employee.contract_id.contract_group.id
            self.employee_sub_group_fkey = employee.contract_id.contract_subgroup.id
            self.payroll_area_fkey = employee.contract_id.pay_type_id.id
            self.contract_type_fkey = employee.contract_id.contract_type.id
            self.probation_end_date = employee.contract_id.trial_date_end
            self.confirmation_date = employee.contract_id.confirmation_date
            self.salutation_fkey = employee.title.id
            self.first_name = employee.firstname if employee.firstname else ''
            self.middle_name = employee.middlename if employee.middlename else ''
            self.last_name = employee.lastname if employee.lastname else ''
            self.birth_date = employee.birthday
            self.gender_fkey = employee.gender
            self.nationality_fkey = employee.country_id.id
            self.birth_country_fkey = employee.country_of_birth.id
            self.shift_type_fkey = employee.resource_calendar_id.id
            self.ot_eligibility = employee.contract_id.overtime_eligibility
            self.system_id = employee.system_id if employee.system_id else ''
            self.email_id = employee.work_email if employee.work_email else ''
            self.payscale_group_fkey = employee.contract_id.payscale_group.id
            self.payscale_level_fkey = employee.contract_id.payscale_level.id

            self.related_compensation = [(0, 0, {
                'name': comp.name.id,
                'from_date': comp.from_date,
                'to_date': comp.to_date,
                'amount': comp.amount,
                'currency': comp.currency.id,
                'frequency': comp.frequency,
                'is_payroll': comp.is_payroll,
                'value': comp.value,
                'period': comp.period,
                'active': comp.active,
                'state': comp.state,
                'related_compensation': comp.id,
                'is_new': False,
            }) for comp in employee.contract_id.related_compensation]
        else:
            latest_event = events[0]
            self.employee_fusion_id = latest_event.employee_fusion_id if latest_event.employee_fusion_id else ''
            self.org_unit_fkey = latest_event.org_unit_fkey.id
            self.line_manager_id_fkey = latest_event.line_manager_id_fkey.id
            self.position_code_fkey = latest_event.position_code_fkey.id
            self.job_title_fkey = latest_event.job_title_fkey.id
            self.cost_center_fkey = latest_event.cost_center_fkey.id
            self.employee_group_fkey = latest_event.employee_group_fkey.id
            self.employee_sub_group_fkey = latest_event.employee_sub_group_fkey.id
            self.payroll_area_fkey = latest_event.payroll_area_fkey.id
            self.contract_type_fkey = latest_event.contract_type_fkey.id
            self.probation_end_date = latest_event.probation_end_date
            self.confirmation_date = latest_event.confirmation_date
            self.salutation_fkey = latest_event.salutation_fkey.id
            self.first_name = latest_event.first_name if latest_event.first_name else ''
            self.middle_name = latest_event.middle_name if latest_event.middle_name else ''
            self.last_name = latest_event.last_name if latest_event.last_name else ''
            self.birth_date = latest_event.birth_date
            self.gender_fkey = latest_event.gender_fkey
            self.nationality_fkey = latest_event.nationality_fkey.id
            self.birth_country_fkey = latest_event.birth_country_fkey.id
            self.shift_type_fkey = latest_event.shift_type_fkey.id
            self.ot_eligibility = latest_event.ot_eligibility
            self.system_id = latest_event.system_id if latest_event.system_id else ''
            self.email_id = latest_event.email_id if latest_event.email_id else ''
            self.payscale_group_fkey = latest_event.payscale_group_fkey.id
            self.payscale_level_fkey = latest_event.payscale_level_fkey.id

            for comp in latest_event.related_compensation.filtered(lambda x: x.state == 'active'):
                self.related_compensation = [(0, 0, {
                    'name': comp.name.id,
                    'from_date': comp.from_date,
                    'to_date': comp.to_date,
                    'amount': comp.amount,
                    'currency': comp.currency.id,
                    'frequency': comp.frequency,
                    'is_payroll': comp.is_payroll,
                    'value': comp.value,
                    'period': comp.period,
                    'active': comp.active,
                    'state': comp.state,
                    'related_compensation': comp.related_compensation.id,
                    'related_event_compensation': comp.id,
                    'is_new': False,
                })]

    def run_employee_events_scheduler(self):
        not_processed_events = self.search([('is_triggered', '=', False), ('update_info', '=', True)])
        for event in not_processed_events:
            effective_date = event.start_date
            if effective_date.date() <= datetime.today().date():
                try:
                    self.do_changes(event)
                except Exception:
                    print('Employee: ' + event.employee_id.name + ', Event Type: ' + event.name.name + ' ERROR')

    def do_changes(self, event):
        self = self.sudo()
        employee = event.employee_id
        # check fusion id
        is_changed_fusion_id = is_changed(employee.fusion_id, event.employee_fusion_id)
        if is_changed_fusion_id:
            employee.fusion_id = event.employee_fusion_id
        # check org
        is_changed_org_id = is_changed(employee.department_id.id, event.org_unit_fkey.id)
        if is_changed_org_id:
            employee.contract_id.group = get_dep(event.org_unit_fkey, 'BU')
            employee.contract_id.department = get_dep(event.org_unit_fkey, 'BD')
            employee.contract_id.section = get_dep(event.org_unit_fkey, 'BS')
            employee.contract_id.subsection = get_dep(event.org_unit_fkey, 'SS')
            employee.contract_id.department_id = event.org_unit_fkey.id
            employee.department_id = event.org_unit_fkey.id
        # check manager
        is_changed_manager_id = is_changed(employee.parent_id.id, event.line_manager_id_fkey.id)
        if is_changed_manager_id:
            employee.contract_id.manager_id = event.line_manager_id_fkey.id
            employee.parent_id = event.line_manager_id_fkey.id
        # check position
        is_changed_position_id = is_changed(employee.job_id.id, event.position_code_fkey.id)
        if is_changed_position_id:
            employee.contract_id.job_id = event.position_code_fkey.id
            employee.job_id = event.position_code_fkey.id
        # check job title
        is_changed_job_title_id = is_changed(employee.contract_id.job_title.id, event.job_title_fkey.id)
        if is_changed_job_title_id:
            employee.contract_id.job_title = event.job_title_fkey.id
        # check cost center
        is_changed_cost_center_id = is_changed(employee.contract_id.cost_center.id, event.cost_center_fkey.id)
        if is_changed_cost_center_id:
            employee.contract_id.cost_center = event.cost_center_fkey.id
        # check contract group
        is_changed_group_id = is_changed(employee.contract_id.contract_group.id, event.employee_group_fkey.id)
        if is_changed_group_id:
            employee.contract_id.contract_group = event.employee_group_fkey.id
        # check contract subgroup
        is_changed_subgroup_id = is_changed(employee.contract_id.contract_subgroup.id,
                                            event.employee_sub_group_fkey.id)
        if is_changed_subgroup_id:
            employee.contract_id.contract_subgroup = event.employee_sub_group_fkey.id
        # check payroll area
        is_changed_payroll_area_id = is_changed(employee.contract_id.pay_type_id.id, event.payroll_area_fkey.id)
        if is_changed_payroll_area_id:
            employee.contract_id.pay_type_id = event.payroll_area_fkey.id
        # check contract type
        is_changed_contract_type_id = is_changed(employee.contract_id.contract_type.id,
                                                 event.contract_type_fkey.id)
        if is_changed_contract_type_id:
            employee.contract_id.contract_type = event.contract_type_fkey.id
        # check probation date
        is_changed_prob_date_id = is_changed(employee.contract_id.trial_date_end, event.probation_end_date)
        if is_changed_prob_date_id:
            employee.contract_id.trial_date_end = event.probation_end_date
        # check confirmation datetime
        is_changed_conf_date_id = is_changed(employee.contract_id.confirmation_date, event.confirmation_date)
        if is_changed_conf_date_id:
            employee.contract_id.confirmation_date = event.confirmation_date
        # check salutation
        is_changed_salutation_id = is_changed(employee.title.id, event.salutation_fkey.id)
        if is_changed_salutation_id:
            employee.title = event.salutation_fkey.id
        # check first name
        is_changed_first_name_id = is_changed(employee.firstname, event.first_name)
        if is_changed_first_name_id:
            employee.firstname = event.first_name
        # check middle name
        is_changed_middle_name_id = is_changed(employee.middlename, event.middle_name)
        if is_changed_middle_name_id:
            employee.middlename = event.middle_name
        # check last name
        is_changed_last_name_id = is_changed(employee.lastname, event.last_name)
        if is_changed_last_name_id:
            employee.lastname = event.last_name
        # if any name is changed
        if is_changed_first_name_id or is_changed_middle_name_id or is_changed_last_name_id:
            employee.name = (employee.firstname or '') + ' ' + (employee.middlename or '') + ' ' + (
                    employee.lastname or '')
        # check birth date
        is_changed_birthday_id = is_changed(employee.birthday, event.birth_date)
        if is_changed_birthday_id:
            employee.birthday = event.birth_date
        # check gender
        is_changed_gender_id = is_changed(employee.gender, event.gender_fkey)
        if is_changed_gender_id:
            employee.gender = event.gender_fkey
        # check country
        is_changed_country_id = is_changed(employee.country_id.id, event.nationality_fkey.id)
        if is_changed_country_id:
            employee.country_id = event.nationality_fkey.id
        # check country birth
        is_changed_birth_country_id = is_changed(employee.country_of_birth.id, event.birth_country_fkey.id)
        if is_changed_birth_country_id:
            employee.country_of_birth = event.birth_country_fkey.id
        # check shift type
        is_changed_shift_type_id = is_changed(employee.contract_id.resource_calendar_id.id,
                                              event.shift_type_fkey.id)
        if is_changed_shift_type_id:
            employee.contract_id.resource_calendar_id = event.shift_type_fkey.id
            employee.resource_calendar_id = event.shift_type_fkey.id
        # check overtime eligibility
        is_changed_ot_eligibility_id = is_changed(employee.contract_id.overtime_eligibility, event.ot_eligibility)
        if is_changed_ot_eligibility_id:
            employee.contract_id.overtime_eligibility = event.ot_eligibility
        # check system id
        is_changed_system_id = is_changed(employee.system_id, event.system_id)
        if is_changed_system_id:
            employee.system_id = event.system_id
        # check mail
        is_changed_mail_id = is_changed(employee.work_email, event.email_id)
        if is_changed_mail_id:
            employee.work_email = event.email_id
        # check payscale group
        is_changed_payscale_group_id = is_changed(employee.contract_id.payscale_group.id,
                                                  event.payscale_group_fkey.id)
        if is_changed_payscale_group_id:
            employee.contract_id.payscale_group = event.payscale_group_fkey.id
        # check payscale level
        is_changed_payscale_level_id = is_changed(employee.contract_id.payscale_level.id,
                                                  event.payscale_level_fkey.id)
        if is_changed_payscale_level_id:
            employee.contract_id.payscale_level = event.payscale_level_fkey.id

        # check compensations
        is_changed_compensations = event.is_esd
        if is_changed_compensations:
            for comp in event.related_compensation:
                pay_component = comp.name
                contract = employee.contract_id

                contract_comp_line = get_contract_comp_line(contract, pay_component)

                if contract_comp_line:
                    contract_comp_line.write({'name': comp.name.id,
                                              'from_date': comp.from_date,
                                              'to_date': comp.to_date,
                                              'amount': comp.amount,
                                              'currency': comp.currency.id,
                                              'frequency': comp.frequency,
                                              'is_payroll': comp.is_payroll,
                                              'value': comp.value,
                                              'period': comp.period,
                                              'active': comp.active,
                                              'state': comp.state})
                else:
                    self.env['hr.compensation'].create({'name': comp.name.id,
                                                        'from_date': comp.from_date,
                                                        'to_date': comp.to_date,
                                                        'amount': comp.amount,
                                                        'currency': comp.currency.id,
                                                        'frequency': comp.frequency,
                                                        'is_payroll': comp.is_payroll,
                                                        'value': comp.value,
                                                        'period': comp.period,
                                                        'active': comp.active,
                                                        'state': comp.state,
                                                        'related_contract': employee.contract_id.id})

        event.is_triggered = True


def get_contract_comp_line(contract, pay_component):
    result = False
    for contract_line in contract.related_compensation:
        contract_pay_component = contract_line.name
        if pay_component.id == contract_pay_component.id:
            result = contract_line
    return result


def is_changed(original_value, event_value):
    result = False
    if original_value != event_value:
        result = True
    return result


class EventCompensation(models.Model):
    _name = 'event.compensation'
    _description = 'Event Compensation'

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
    related_event = fields.Many2one('hr.employee.event', 'Related Event', ondelete='cascade')
    related_compensation = fields.Many2one('hr.compensation', 'Related Compensation')
    related_event_compensation = fields.Many2one('event.compensation', 'Related Event Compensation')
    component_description = fields.Char(
        string='Component Description',
        related='name.description')
    active = fields.Boolean(default=True)
    state = fields.Selection([('active', 'Active'), ('inactive', 'Inactive')], default='active', string="State",
                             required=True)
    is_sap_processed = fields.Boolean(default=False)
    is_new = fields.Boolean(default=True)

    @api.constrains('related_event', 'name')
    def _check_paycomponents_contract(self):
        for rec in self:
            if rec.name and rec.related_event:
                prev_compensations = self.env['event.compensation'].search(
                    [('related_event', '=', rec.related_event.id),
                     ('name', '=', rec.name.id), ('id', '!=', rec.id), ('state', '=', 'active')])
                if len(prev_compensations) > 0 and rec.state == 'active':
                    raise ValidationError(_("Pay Component must be unique per Event!"))


class ContractEmploymentType(models.Model):
    _name = 'hr.contract.employment.type'
    _description = 'HR Contract Type'

    name = fields.Char('Type')
    code = fields.Char('Prefix')
    related_sequence = fields.Many2one('ir.sequence', 'Related Sequence')


class HrEmployeePrivate(models.Model):
    _inherit = 'hr.employee'

    title = fields.Many2one('res.partner.title')
    lang = fields.Many2one('res.lang', string='Native Language',
                           domain="['|',('active','=',True),('active','=',False)]")
    contract_employment_type = fields.Many2one('hr.contract.employment.type', 'Contract Employment Type')
    id_generated = fields.Boolean('ID generated')
    fusion_id = fields.Char('Main Company ID')
    system_id = fields.Char('System ID')
    firstname = fields.Char('Employee Firstname')
    middlename = fields.Char('Employee Middlename')
    lastname = fields.Char('Employee Lastname')
    arabic_name = fields.Char('Arabic Name')
    mothers_name = fields.Char("Mother's name")
    arabic_mothers_name = fields.Char("Arabic Mother's name")
    religion = fields.Selection(Religions_list, 'Religions')
    street = fields.Char('Street')
    po_box = fields.Char('Employee Address PO-Box')
    city = fields.Char('City')
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')

    parent_id = fields.Many2one('hr.employee', string='Manager', domain=[])
    job_id = fields.Many2one('hr.job', string='Job Position')
    job_title = fields.Char(related='job_id.job_title.name', string='Job Title')
    # department_id = fields.Many2one(related='contract_id.department_id', store=True, string="OC Path")

    dependents = fields.One2many('res.partner', 'related_employee', 'Dependents')

    notice_ids = fields.One2many('hr.notice', 'related_employee', 'Notices')

    state = fields.Selection([('pending', 'Pending Approval'), ('approved', 'Approved'), ('reject', 'Reject')],
                             default='pending',
                             string="Approval State")
    wizard_name = fields.Char(string="Wizard name")

    housing_ids = fields.One2many(
        comodel_name='hr.housing',
        inverse_name='employee_id',
        string='Housings',
        required=False)
    employee_event_ids = fields.One2many(
        comodel_name='hr.employee.event',
        inverse_name='employee_id',
        string='Events',
        required=False)
    reject_reason = fields.Text('Reject Reason')
    employee_type = fields.Selection(
        [('fusion_employee', 'Main Company Employee'), ('fos_employee', 'Outsourced Employees'),
         ('client_employee', 'Client Employee'), ('employee', 'Employee'),
         ('student', 'Student'), ('trainee', 'Trainee'), ('contractor', 'Contractor'),
         ('freelance', 'Freelancer')], string="Employee Type", default='fos_employee')
    # employee_type = fields.Selection([('fusion_employee', 'Fusion Employee'), ('fos_employee', 'Outsourced Employees'),
    #                                   ('client_employee', 'Client Employee'), ('employee', 'Employee'),
    #                                   ('student', 'Student'), ('trainee', 'Trainee'), ('contractor', 'Contractor'),
    #                                   ('freelance', 'Freelancer')], string="Employee Type", default='fos_employee')
    is_wps = fields.Boolean(string="WPS")
    is_labor = fields.Boolean(string="Is Labor")
    sponsored_company_id = fields.Many2one('res.partner', string="Sponsor Company", readonly=False)
    company_id = fields.Many2one('res.company', string='Main Company')
    partner_parent_id = fields.Many2one('res.partner', string='Client/Company', readonly=False)
    partner_parent_id_fos = fields.Many2one('res.partner', string='FOS Client/ FOS Company', required=True,
                                            readonly=False)

    @api.onchange('company_id')
    def get_company_fields(self):
        partner = self.company_id.partner_id
        partner_default = self.env.company.partner_id
        self.partner_parent_id = partner.id if partner else partner_default.id
        self.sponsored_company_id = partner.id if partner else partner_default.id

    related_contact_ids = fields.Many2many(related='user_partner_id.related_companies', string="Related Contact",
                                           readonly=False)
    main_parent_id = fields.Many2one(related='user_partner_id.main_parent_id', string="Main Parent", readonly=False)
    qid_name = fields.Char("QID Name")
    joining_date = fields.Date("Joining Date")
    nationality_id = fields.Many2one('res.country', "Nationality")
    nationality_birth = fields.Many2one('res.country', string='Nationality – Birth')
    reference = fields.Char("Reference")

    read_only_user_role = fields.Boolean(compute='_get_user_group', default=False)
    all_model_read_only = fields.Boolean(compute='_get_user_group', default=False)
    invisible_user_role = fields.Boolean(compute='_get_user_group', default=False)

    time_hired = fields.Char(
        string='Employment Tenure',
        required=False, compute='_calculate_time_hired')
    time_hired_in_no = fields.Float(
        string='Employment Period in Numbers',
        required=False, compute='_calculate_time_hired')

    private_email = fields.Char(string="Private Email", stored=True, related=False)
    sequence = fields.Char('Sequence', default='New', copy=False)
    attested_e_contract = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ('n/a', 'N/A')
    ], string="Attested E-Contract", default="no")
    ndu = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ('n/a', 'N/A')
    ], string="NDU", default="no")

    medical_insurance = fields.Boolean()
    wc_insurance = fields.Boolean()
    life_insurance = fields.Boolean()
    have_national_address = fields.Boolean('National Address Registered?')
    has_private_medical_insurance = fields.Boolean('Has Private Medical Insurance?')
    has_workmens_compensation = fields.Boolean("Has Workmen's Compensation?")
    has_grading_system = fields.Boolean(related='partner_parent_id.has_grading_system')
    is_contract_access = fields.Boolean(compute="compute_contract_access", default=False)
    # qid_job_position_id = fields.Many2one('hr.job', string='QID Job Position', compute='_qid_name_compute',compute_sudo=True)

    outsourced_status = fields.Selection([
        ('visa_ready_to_use', 'Visa Ready To Use'),
        ('inside_country', 'Inside The Country'),
        ('inside_country_mev', 'Inside the Country – MEV'),
        ('onboarding', 'Outside Visa Test Process'),
        ('potential_candidate', 'Potential Candidate'),
        ('sponsored_outside_country', 'Sponsored – Outside The Country'),
        ('sponsored_absconding', 'Sponsored – Absconding'),
        ('sponsored', 'Sponsored'),
        ('sponsored_transfer_rejected', 'Sponsored – Transfer Rejected'),
        ('sponsored_Transferring_out', 'Sponsored – Transferring Out'),
        ('work_multi_entry', 'Work - Multi Entry'),
        ('sponsored_to_cancelled', 'Sponsored – To be Cancelled'),
        ('sponsored_outside_country_to_cancelled', 'Sponsored - Outside the Country - To be Cancelled'),
        ('transferring_in', 'Transferring In'),
        ('transferred_out', 'Transferred Out'),
        ('work_permit', 'Work Permit'),
        ('cancelled', 'Cancelled'),
    ], string='Status')
    transfer_no = fields.Char(string='Transfer No.')
    end_of_notice_period = fields.Date(string='End of Notice Period')
    release_of_responsibility_date = fields.Date(string='Release of Responsibility Date')
    absconding_report_no = fields.Char(string='Absconding Report Number')
    date_of_transfer_completion = fields.Date(string='Date Of Transfer Completion')
    work_permit_no = fields.Char(string='Work Permit No')
    date_of_cancellation = fields.Date(string='Date Of Cancellation')
    outsourced_status_log_ids = fields.One2many(comodel_name='outsourced.status.log',
                                                inverse_name='employee_id',
                                                string='Outsourced Status Log')
    active_contract = fields.Many2one(comodel_name='hr.contract', string='Active Contract',
                                      compute='_compute_active_contract')
    contract_start_date = fields.Date('Contract Start Date', related='active_contract.date_start')
    grade = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6')], string="Grade")
    oracle_id = fields.Char(string='Oracle ID')
    taleo_id = fields.Char(string='Taleo ID')
    qa_staff_no = fields.Char(string='QA Staff Number')
    is_arabic_session = fields.Char(string="arabic session", compute="_compute_arabic_session")
    employee_check_in = fields.Char(compute='_compute_employee_check_in')
    employee_check_out = fields.Char(compute='_compute_employee_check_out')
    # personal_phone_no = fields.Char(related='phone_personal')

    def _compute_employee_check_in(self):
        for rec in self:
            # if rec.attendance_sheet_ids.filtered(
            #         lambda x: x.date == date.today()):
            #     rec.employee_check_in = rec.attendance_sheet_ids.filtered(
            #         lambda x: x.date == date.today())[0].check_in
            # else:
            #     rec.employee_check_in = False
            today = date.today()
            time_str = ''
            check_in = rec.env['machine.attendance.record'].search([('employee_id', '=', rec.id), ('punch_type', '=', 'I'), ('punch_date', '=', today)])
            if check_in:
                check_in = check_in[-1].punch_time + timedelta(hours=3)
                time_str = check_in.time()
                time_str = time_str.strftime("%H:%M")
                rec.employee_check_in = time_str
            else:
                rec.employee_check_in = False

    def _compute_employee_check_out(self):
        for rec in self:
            today = date.today()
            time_str = ''
            check_out = rec.env['machine.attendance.record'].search(
                [('employee_id', '=', rec.id), ('punch_type', '=', 'O'), ('punch_date', '=', today)])
            if check_out:
                check_out = check_out[0].punch_time + timedelta(hours=3)
                time_str = check_out.time()
                time_str = time_str.strftime("%H:%M")
                rec.employee_check_out = time_str
            else:
                rec.employee_check_out = False

    @api.depends_context('lang')
    def _compute_arabic_session(self):
        if self._context.get('lang') == 'ar_001':
            self.write({
                'is_arabic_session': True
            })
        else:
            self.write({
                'is_arabic_session': False
            })

    def _cron_emp_cust_set_document(self):
        employees = self.env['hr.employee'].search([]).filtered(lambda x: x.user_partner_id.id and x.document_o2m.ids)
        documents_set_partners = self.env['documents.document'].search([('employee_id', 'in', employees.ids)]).filtered(
            lambda x: not x.partner_id.id)
        for document in documents_set_partners:
            document.partner_id = document.employee_id.user_partner_id.id
        customers = self.env['res.partner'].search([]).filtered(lambda x: x.document_o2m.ids)
        employees_user_partner = self.env['hr.employee'].search([('user_partner_id', 'in', customers.ids)]).mapped(
            'user_partner_id')
        doc = self.env['documents.document'].search([('partner_id', 'in', employees_user_partner.ids)]).filtered(
            lambda x: not x.employee_id)
        for document in doc:
            document.employee_id = self.env['hr.employee'].search(
                [('user_partner_id', '=', document.partner_id.id)]).id if document.partner_id else False

    @api.onchange('end_of_notice_period')
    def onchange_end_of_notice_period(self):
        if self.end_of_notice_period:
            self.release_of_responsibility_date = self.end_of_notice_period + timedelta(days=30)
        else:
            self.release_of_responsibility_date = False

    def compute_contract_access(self):
        for rec in self:
            rec.is_contract_access = False
            if self.env.user.has_group(
                    'hr_contract_custom.group_access_fusion_employee_contract') or self.env.user.has_group(
                'hr_contract_custom.group_access_other_employee_contract'):
                rec.sudo().is_contract_access = True
            else:
                rec.sudo().is_contract_access = False

    @api.depends('contract_ids')
    def _compute_active_contract(self):
        if self.contract_ids:
            contracts = self.contract_ids.filtered(lambda contract: contract.state == 'open')
            if contracts:
                self.sudo().active_contract = contracts[0]
            else:
                self.sudo().active_contract = False
        else:
            self.sudo().active_contract = False

    def link_partner(self):
        return {
            'name': _('Link Partner'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'link.employee.partner.wizard',
            'target': 'new',
            'context': {'employee_name': self.name, 'employee_id': self.id},
        }

    def create_user(self):
        for rec in self:
            template_user_id = literal_eval(
                self.env['ir.config_parameter'].sudo().get_param('base.template_portal_user_id', 'False'))
            template_user = self.env['res.users'].browse(template_user_id)
            if not template_user.exists():
                raise ValueError(_('Signup: invalid template user'))
            values = {
                'active': True,
                'name': rec.name,
                'login': rec.work_email,
                'email': rec.work_email,
                'is_employee': True,
                'company_id': rec.company_id.id,
                'company_ids': [(6, 0, [rec.company_id.id])]
            }
            if rec.user_partner_id:
                values.update({
                    'partner_id': rec.user_partner_id.id
                })
            rec.user_id = template_user.with_context(no_reset_password=True).copy(values)
            if not rec.user_partner_id:
                rec.user_partner_id = rec.user_id.partner_id.id
        return True

    def contacts_dependent(self):
        self.ensure_one()
        action = self.env.ref('ebs_fusion_contacts.action_dependents').read()[0]
        action['context'] = {
            'default_dependent_id': self.sponsored_company_id.id,
            'default_is_dependent': True,
            'default_parent_id': self.user_partner_id.id,
            'default_main_parent_id': self.parent_id.id
        }
        if self.user_partner_id:
            action['domain'] = [('parent_id', '=', self.user_partner_id.id), (
                'address_type', 'not in',
                ['head_office', 'local_office', 'Work_sites', "labor_accommodation", "national_address"])]
        else:
            action['domain'] = [('id', 'in', [])]
        return action

    @api.depends('joining_date')
    def _calculate_time_hired(self):
        self = self.sudo()
        for rec in self:
            diff = relativedelta.relativedelta(datetime.now(), rec.joining_date)
            years = diff.years
            months = diff.months

            rec.sudo().time_hired = ('{} years {} months'.format(years, months))
            rec.sudo().time_hired_in_no = years + (months / 12)

    def open_employee_view(self):
        return {
            'name': _("Employees"),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee',
            'view_mode': 'kanban,tree,form,activity',
            'search_view_id': self.env.ref('hr.view_employee_filter').id,
            'domain': ['|', ('user_id', '=', self.env.uid),
                       ('id', 'child_of', [employee.id for employee in self.env.user.employee_ids])],
            'context': {},
            'target': 'current',
        }

    def name_get(self):
        names = []
        for record in self:
            names.append(
                (record.id, "%s" % (record.arabic_name if self._context.get('lang') == 'ar_001' else record.name)))
        return names

    # @api.model
    # def name_search(self, name='', args=None, operator='ilike', limit=100):
    #     args = args or []
    #     if name:
    #         records = self.search(['|', ('name', operator, name), ('arabic_name', operator, name)])
    #         # return records.name_get()
    #     # return self.search([('name', operator, name)]+args, limit=limit).name_get()
    #     return super(HrEmployeePrivate, self).name_search(name=name, args=args, operator=operator, limit=limit)

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        domain = args + ['|', ('arabic_name', operator, name), ('name', operator, name)]
        # res = super(HrEmployeePrivate, self).search(domain, limit=limit).name_get()
        return self._search(domain, limit=limit)


    def write(self, vals):
        if vals.get('outsourced_status') and self.employee_type == 'fos_employee':
            self.write({'outsourced_status_log_ids': [
                (0, 0, {'outsourced_status': vals.get('outsourced_status'), 'created_by': self.env.uid})]})
        res = super(HrEmployeePrivate, self).write(vals)
        if vals.get('parent_id') != None:
            self.env['approval.category'].search([]).check_if_subordinates()
        if self.user_partner_id and self.user_partner_id.dependent_id != self.sponsored_company_id:
            self.user_partner_id.dependent_id = self.sponsored_company_id.id
        if vals.get('outsourced_status') and vals.get('outsourced_status') in ['transferred_out', 'cancelled']:
            self.write({'active': False})
        return res

    @api.depends('read_only_user_role', 'invisible_user_role', 'all_model_read_only')
    def _get_user_group(self):
        for rec in self:
            user = self.env.user
            if user.has_group('base.user_admin'):
                rec.sudo().invisible_user_role = False
                rec.sudo().read_only_user_role = False
                rec.sudo().all_model_read_only = False

            elif user.has_group('security_rules.group_hr_employee'):
                if rec.id in user.employee_ids.ids:
                    rec.sudo().read_only_user_role = True
                    rec.sudo().invisible_user_role = False
                    rec.sudo().all_model_read_only = False
                else:
                    rec.sudo().read_only_user_role = True
                    rec.sudo().invisible_user_role = True
                    rec.sudo().all_model_read_only = True

            else:
                rec.sudo().all_model_read_only = False
                rec.sudo().read_only_user_role = False
                rec.sudo().invisible_user_role = False

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(HrEmployeePrivate, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                                submenu=submenu)
        if view_type == 'tree':
            # Remove the unwanted field from the tree view
            unwanted_field = 'name' if self._context.get('lang') == 'ar_001' else 'arabic_name'
            doc = etree.XML(result['arch'])
            for element in doc.xpath("//field[@name='%s']" % unwanted_field):
                element.getparent().remove(element)
            result['arch'] = etree.tostring(doc, encoding='unicode')

        return result

    def split_code(self, code):
        return code.split(self.contract_employment_type.related_sequence.prefix, 1)[1]

    def generate_id(self):
        for rec in self:

            if not rec.country_id:
                raise ValidationError('Please fill Country before Generating ID!')

            if not rec.gender:
                raise ValidationError('Please fill Gender before Generating ID!')
            if not rec.religion:
                raise ValidationError('Please fill Religions before Generating ID!')
            if not rec.birthday:
                raise ValidationError('Please fill Date of Birth before Generating ID!')
            if not rec.place_of_birth:
                raise ValidationError('Please fill Place of Birth before Generating ID!')
            if not rec.country_of_birth:
                raise ValidationError('Please fill Country of Birth before Generating ID!')
            if not rec.marital:
                raise ValidationError('Please fill Marital Status before Generating ID!')

            if rec.contract_employment_type.related_sequence:
                rec.fusion_id = self.env['ir.sequence'].next_by_code(rec.contract_employment_type.related_sequence.code)
                rec.system_id = rec.contract_employment_type.code + self.split_code(rec.fusion_id)
                rec.id_generated = True
            else:
                raise ValidationError('Select Employee Type Before!')

    @api.onchange('contract_employment_type')
    def onchange_contract_employment_type(self):
        for rec in self:
            rec.id_generated = False

    @api.onchange('department_id')
    def onchange_department_id(self):
        for rec in self:
            rec.parent_id = rec.department_id.manager_id.id

    def state_approve(self):
        if self.employee_type == 'fusion_employee':
            if self.sequence == 'New':
                self.sequence = self.env['ir.sequence'].next_by_code('hr.fusion') or 'New'
        elif self.employee_type == 'fos_employee':
            if self.sequence == 'New':
                self.sequence = self.env['ir.sequence'].next_by_code('hr.fos') or 'New'
        else:
            if self.sequence == 'New':
                self.sequence = self.env['ir.sequence'].next_by_code('hr.client') or 'New'

        if self.user_partner_id:
            self.add_payable_receivable_employee_partner()

        self.reject_reason = ""

        self.with_context(skip_sms_import=True).write({'state': 'approved'})
        if not self.sequence or self.sequence == 'New':
            self.write({'sequence': self.env['ir.sequence'].next_by_code('employee_no')})
        msg = _('Employee Approved')
        self.message_post(body=msg)

    def state_pending(self):
        self.write({'state': 'pending'})

    def log_and_reject(self):
        self = self.sudo()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Reason',
            'res_model': 'log.note.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'view_id': self.env.ref('hr_employee_custom.log_note_reject_wizard_view_form').id,
            'context': {
                'related_name': self._name,
            }
        }

    def state_reject(self):
        if self.reject_reason:
            self.write({'state': 'reject'})
            msg = _('Employee Rejected. Rejection Reason: ' + self.reject_reason)
            self.message_post(body=msg)
        else:
            raise ValidationError('Must add reject reason!')

    @api.onchange('firstname', 'middlename', 'lastname')
    def _onchange_name(self):
        for rec in self:
            if rec.firstname and rec.middlename and rec.lastname:
                rec.name = (rec.firstname or '') + ' ' + (rec.middlename or '') + ' ' + (rec.lastname or '')


class Partner(models.Model):
    _inherit = 'res.partner'

    related_employee = fields.Many2one('hr.employee', 'Related Employee')

    # state = fields.Selection([('pending', 'Pending Approval'), ('approved', 'Approved'), ('reject', 'Reject')],
    #                          default='pending',
    #                          string="Approval State")

    reject_reason = fields.Text('Reject Reason')

    contact_relation_type_id = fields.Many2one(
        comodel_name='contact.relation.type',
        string='Relation Type',
        required=False)

    def action_see_employee(self):
        action = self.env.ref('ebs_fusion_hr_employee.open_view_client_employee_list_my').read()[0]
        action['domain'] = [('sponsored_company_id', '=', self.id)]
        return action

    def state_approve(self):
        self.reject_reason = ""
        self.write({'state': 'approved'})
        msg = _('Dependent ' + self.name + ' Approved')
        self.related_employee.message_post(body=msg)

    def state_pending(self):
        self.write({'state': 'pending'})

    def log_and_reject(self):
        self = self.sudo()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Reason',
            'res_model': 'log.note.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'view_id': self.env.ref('hr_employee_custom.log_note_reject_wizard_view_form').id,
            'context': {
                'related_name': self._name,
            }
        }

    def state_reject(self):
        if self.reject_reason:
            self.write({'state': 'reject'})
            msg = _('Dependent ' + self.name + ' Rejected. Rejection Reason: ' + self.reject_reason)
            self.related_employee.message_post(body=msg)
        else:
            raise ValidationError('Must add reject reason!')


class HrContractInherit(models.Model):
    _inherit = 'hr.contract'

    employee_type = fields.Selection([('fusion_employee', 'Fusion Employee'), ('fos_employee', 'Outsourced Employees'),
                                      ('client_employee', 'Client Employee')], related='employee_id.employee_type',
                                     string='Employee Type')
    partner_parent_id = fields.Many2one('res.partner', related='employee_id.partner_parent_id', string='Company')
    sponsored_company_id = fields.Many2one('res.partner', related='employee_id.sponsored_company_id',
                                           string="Company Sponsor")


class OutsourcedStatusLog(models.Model):
    _name = 'outsourced.status.log'
    _description = 'Outsourced Status Log'

    employee_id = fields.Many2one(comodel_name='hr.employee')
    outsourced_status = fields.Selection([
        ('visa_ready_to_use', 'Visa Ready To Use'),
        ('inside_country', 'Inside The Country'),
        ('inside_country_mev', 'Inside the Country – MEV'),
        ('onboarding', 'Outside Visa Test Process'),
        ('potential_candidate', 'Potential Candidate'),
        ('sponsored_outside_country', 'Sponsored – Outside The Country'),
        ('sponsored_absconding', 'Sponsored – Absconding'),
        ('sponsored', 'Sponsored'),
        ('sponsored_transfer_rejected', 'Sponsored – Transfer Rejected'),
        ('sponsored_Transferring_out', 'Sponsored – Transferring Out'),
        ('work_multi_entry', 'Work - Multi Entry'),
        ('sponsored_to_cancelled', 'Sponsored – To be Cancelled'),
        ('sponsored_outside_country_to_cancelled', 'Sponsored - Outside the Country - To be Cancelled'),
        ('transferring_in', 'Transferring In'),
        ('transferred_out', 'Transferred Out'),
        ('work_permit', 'Work Permit'),
        ('cancelled', 'Cancelled'),
    ], string='Status')
    created_by = fields.Many2one('res.users', 'Amended By')
