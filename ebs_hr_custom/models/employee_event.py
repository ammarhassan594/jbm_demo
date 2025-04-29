from odoo import models, fields, api, _
from datetime import datetime, date
import logging
from odoo.exceptions import ValidationError, UserError
_logger = logging.getLogger(__name__)


class EmployeeEvent(models.Model):
    _name = 'employee.event'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', required=True)
    contract_id = fields.Many2one('hr.contract')
    event_type = fields.Selection(
        [('update_employee', 'Update Employee'), ('update_contract', 'Update Employee Contract')],
        default='update_employee', required=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirmed'), ('approve', 'Approved'), ('cancel', 'Cancelled')],
        default='draft', required=True)
    effective_date = fields.Date(string='Effective Date', required=True)

    name = fields.Char(string='Name')
    name_previous = fields.Char(string='Name P')
    registration_number = fields.Char(string='Registration Number')
    registration_number_previous = fields.Char(string='Registration Number P')
    employee_type = fields.Selection(string="Employment Category", default="", store=True,
                                     selection=[('temp', 'Temporary Employee'),
                                                ('perm_in_house', 'Permanent In house'),
                                                ('perm_staff', 'Permanent Staff')])
    employee_type_previous = fields.Selection(string="Employment Category P", default="", store=True,
                                     selection=[('temp', 'Temporary Employee'),
                                                ('perm_in_house', 'Permanent In house'),
                                                ('perm_staff', 'Permanent Staff')])
    mobile_phone = fields.Char(string='Work Mobile')
    work_phone = fields.Char(string='Work Phone')
    work_email = fields.Char(string='Work Email')
    permanent_staff_employee = fields.Many2one('permanent.employee.pay.scale', string='Pay Scale')
    payroll_group = fields.Many2one('employee.payroll.group', string='Grade')
    permanent_staff_employee_previous = fields.Many2one('permanent.employee.pay.scale', string='Pay Scale P')
    payroll_group = fields.Many2one('employee.payroll.group', string='Grade')
    payroll_group_previous = fields.Many2one('employee.payroll.group', string='Grade P')
    main_project = fields.Many2one('project.project', string='Work Location(Project)')
    main_project_previous = fields.Many2one('project.project', string='Work Location(Project) P')
    department_id = fields.Many2one('hr.department', string='Department')
    sponsor = fields.Many2one(comodel_name="hr.employee.sponsor", string="Employee Sponsor", required=False)
    sponsorship_type = fields.Selection([('on the company', 'On the company'), ('on the familly', 'On the familly')],
                                        string='Sponsorship Type')
    department_id_previous = fields.Many2one('hr.department', string='Department P')
    sponsor = fields.Many2one(comodel_name="hr.employee.sponsor", string="Employee Sponsor", required=False)
    sponsor_previous = fields.Many2one(comodel_name="hr.employee.sponsor", string="Sponsor P", required=False)
    sponsorship_type = fields.Selection([('on the company', 'On the company'), ('on the familly', 'On the familly')],
                                        string='Sponsorship Type')
    sponsorship_type_previous = fields.Selection([('on the company', 'On the company'), ('on the familly', 'On the familly')],
                                        string='Sponsorship Type P')

    joining_date = fields.Date(string='Joining Date')
    probation = fields.Selection(string='Probation', selection=[('90d', '3 Months'), ('180d', '6 Months')])
    probation_date = fields.Date(string='Probation Date')
    number_of_years_work = fields.Char(string='Yrs w/Waseef')
    contract_duration = fields.Selection(string='Contract Duration',
                                         selection=[('one', 'One'), ('two', 'Two'), ('three', 'Three'),
                                                    ('four', 'Four'), ('five', 'Five'), ('open-ended', 'Unlimited')])
    job_id = fields.Many2one('hr.job', string='Job Position')
    job_id_previous = fields.Many2one('hr.job', string='Job Position P')
    profession_id = fields.Many2one('profession.profession', string='Profession')
    country_id = fields.Many2one('res.country', string='Nationality (Country)')
    country_id_previous = fields.Many2one('res.country', string='Nationality (Country) P')
    gender = fields.Selection(string='Gender', selection=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    gender_previous = fields.Selection(string='Gender P', selection=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    birthday = fields.Date(string='Date of Birth')
    marital = fields.Selection(string='Marital Status', selection=[('single', 'Single'), ('married', 'Married'),
                                                                   ('cohabitant', 'Legal Cohabitant'),
                                                                   ('widower', 'Widower'), ('divorced', 'Divorced')])
    marital_previous = fields.Selection(string='Marital Status P', selection=[('single', 'Single'), ('married', 'Married'),
                                                                   ('cohabitant', 'Legal Cohabitant'),
                                                                   ('widower', 'Widower'), ('divorced', 'Divorced')])
    termination_date = fields.Date(string='Termination Date')
    termination_reason = fields.Char(string='Termination Reason')
    sim_card = fields.Char(string='Mobile')
    qid_doc_number = fields.Char(string='QID Number')
    passport_doc_number = fields.Char(string='Passport Number')
    age = fields.Integer(string='Age')
    certificate_ids = fields.One2many("employee.certificate", "employee_id", string='Certificate')
    qualification_title = fields.Char(string="Qualification Title")
    parent_id = fields.Many2one('hr.employee')
    line_manager_id = fields.Many2one('hr.employee')
    parent_id_previous = fields.Many2one('hr.employee')
    line_manager_id = fields.Many2one('hr.employee')
    line_manager_id_previous = fields.Many2one('hr.employee')
    bank_name = fields.Char(string='Bank Name')
    bank_account_id = fields.Many2one('res.partner.bank')
    employee_name_in_arabic = fields.Char("Employee Name in Arabic")
    job_name_arabic = fields.Char("Job Name in Arabic")

    contract_status = fields.Selection(string='Contract Status',
                                       selection=[('single', 'Single'), ('married', 'Married')])
    contract_status_previous = fields.Selection(string='Contract Status P',
                                       selection=[('single', 'Single'), ('married', 'Married')])

    # contract
    contract_department_id = fields.Many2one('hr.department', string='Department')
    contract_permanent_staff_employee = fields.Many2one('permanent.employee.pay.scale', string='Pay Scale')
    contract_permanent_inhouse_employee = fields.Many2one('employee.payroll.group', string='Pay Scale')
    structure_type_id = fields.Many2one('hr.payroll.structure.type', string='Salary Structure Type')
    contract_job_id = fields.Many2one('hr.job', string='Job Position')
    airport_name = fields.Many2one('world.airports', string='Airport')
    contract_type_id = fields.Many2one('hr.contract.type', string='Employee Category')
    contract_date_start = fields.Date(string='Start Date')
    contract_date_end = fields.Date(string='End Date')
    trial_date_end = fields.Date(string='End of Trial Period')
    resource_calendar_id = fields.Many2one('resource.calendar', string='Working Schedule')
    resource_calendar_id_previous = fields.Many2one('resource.calendar', string='Working Schedule P')


    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError("Only draft records can be deleted")
            return super(EmployeeEvent, self).unlink()

    @api.onchange('employee_id', 'event_type')
    def onchange_employee_id(self):
        if self.employee_id and self.event_type == 'update_employee':
            self.registration_number = self.employee_id.registration_number
            self.name = self.employee_id.name
            self.main_project = self.employee_id.main_project
            self.marital = self.employee_id.marital
            self.department_id = self.employee_id.department_id
            self.sponsorship_type = self.employee_id.sponsorship_type
            self.sponsor = self.employee_id.sponsor
            self.payroll_group = self.employee_id.payroll_group
            self.permanent_staff_employee = self.employee_id.permanent_staff_employee
            self.contract_status = self.employee_id.contract_status
            self.country_id = self.employee_id.country_id
            self.job_id = self.employee_id.job_id
            self.gender = self.employee_id.gender
            self.parent_id = self.employee_id.parent_id
            self.line_manager_id = self.employee_id.line_manager_id
            self.employee_type = self.employee_id.wassef_employee_type
        if self.employee_id and self.event_type == 'update_contract':
            self.resource_calendar_id = self.employee_id.contract_id.resource_calendar_id
            self.payroll_group = self.employee_id.payroll_group
            self.permanent_staff_employee = self.employee_id.permanent_staff_employee
            self.employee_type = self.employee_id.wassef_employee_type
            # self.mobile_phone = self.employee_id.mobile_phone
            # self.work_phone = self.employee_id.work_phone
            # self.work_email = self.employee_id.work_email
            # self.joining_date = self.employee_id.joining_date
            # self.probation = self.employee_id.probation
            # self.probation_date = self.employee_id.probation_date
            # self.number_of_years_work = self.employee_id.number_of_years_work
            # self.contract_duration = self.employee_id.contract_duration
            # self.profession_id = self.employee_id.profession_id
            # self.birthday = self.employee_id.birthday
            # self.contract_status = self.employee_id.contract_status
            # self.contract_department_id = self.employee_id.contract_id.department_id
            # self.contract_permanent_staff_employee = self.employee_id.contract_id.permanent_staff_employee
            # self.structure_type_id = self.employee_id.contract_id.structure_type_id
            # self.contract_job_id = self.employee_id.contract_id.job_id
            # self.airport_name = self.employee_id.contract_id.airport_name
            # self.contract_type_id = self.employee_id.contract_id.type_id
            # self.contract_date_start = self.employee_id.contract_id.date_start
            # self.contract_date_end = self.employee_id.contract_id.date_end
            # self.trial_date_end = self.employee_id.contract_id.trial_date_end
            # self.employee_name_in_arabic = self.employee_id.employee_name_in_arabic
            # self.job_name_arabic = self.employee_id.job_name_arabic

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_confirm(self):
        self.write({'state': 'confirm'})

    def _update_employee_event(self):
        for event in self:
            registration_number = self.env['hr.employee'].sudo().search(
                [('registration_number', '=', event.registration_number)])
            duplicated_registration_number = False
            if len(registration_number) > 1:
                duplicated_registration_number = True
            if len(registration_number) == 1 and registration_number.id != event.employee_id.id:
                duplicated_registration_number = True
            if event.event_type == 'update_employee' and not duplicated_registration_number:
                employee_id = self.env['hr.employee'].sudo().search([('id', '=', event.employee_id.id)])
                employee_id.sudo().with_context(is_created_cron=True).write({
                    'registration_number': event.registration_number,
                    'name': event.name,
                    'main_project': event.main_project,
                    'marital': event.marital,
                    'department_id': event.department_id.id if event.department_id else False,
                    'sponsorship_type': event.sponsorship_type,
                    'sponsor': event.sponsor.id if event.sponsor else False,
                    'payroll_group': event.payroll_group.id if event.payroll_group else False,
                    'permanent_staff_employee': event.permanent_staff_employee.id if event.permanent_staff_employee else False,
                    'contract_status': event.contract_status,
                    'country_id': event.country_id.id if event.country_id else False,
                    'job_id': event.job_id.id if event.job_id else False,
                    'gender': event.gender,
                    'parent_id': event.parent_id.id if event.parent_id else False,
                    'line_manager_id': event.line_manager_id.id if event.line_manager_id else False,
                    # 'employee_type': event.employee_type,
                    # 'mobile_phone': event.mobile_phone,
                    # 'work_phone': event.work_phone,
                    # 'work_email': event.work_email,
                    # 'joining_date': event.joining_date,
                    # 'probation': event.probation,
                    # 'probation_date': event.probation_date,
                    # 'number_of_years_work': event.number_of_years_work,
                    # 'contract_duration': event.contract_duration,
                    # 'profession_id': event.profession_id.id if event.profession_id else False,
                    # 'birthday': event.birthday,
                })
                event.sudo().write({'state': 'approve'})
            if event.event_type == 'update_contract' and not duplicated_registration_number:

                contract_id = self.env['hr.contract'].sudo().search([('id', '=', event.contract_id.id)])
                res = contract_id.sudo().with_context(is_created_cron=True).write({
                    'registration_number': event.registration_number,
                    'permanent_staff_employee': event.permanent_staff_employee.id if event.permanent_staff_employee else False,
                    'payroll_group': event.payroll_group.id if event.payroll_group else False,
                    'resource_calendar_id': event.resource_calendar_id.id if event.resource_calendar_id else False,
                    # 'department_id': event.contract_department_id.id if event.contract_department_id else False,
                    # 'structure_type_id': event.structure_type_id.id if event.structure_type_id else False,
                    # 'job_id': event.contract_job_id.id if event.contract_job_id else False,
                    # 'airport_name': event.airport_name,
                    # 'type_id': event.contract_type_id.id if event.contract_type_id else False,
                    # 'date_start': event.contract_date_start,
                    # 'date_end': event.contract_date_end,
                    # 'trial_date_end': event.trial_date_end,
                })
                if event.registration_number and event.registration_number != contract_id.sudo().employee_id.registration_number:
                    contract_id.sudo().employee_id.sudo().with_context(is_created_cron=True).write(
                        {'registration_number': event.registration_number})
                event.sudo().write({'state': 'approve'})
            if duplicated_registration_number:
                _logger.info('Duplicate registration number found for: %s', event.employee_id.name)
                event.message_post(body=f'Duplicate registration number found for: {event.employee_id.name}')

    def _update_employee_event_auto(self):
        event_ids = self.search([('state', '=', 'confirm'), ('effective_date', '<=', date.today())],
                                order='effective_date ASC')
        event_ids._update_employee_event()
