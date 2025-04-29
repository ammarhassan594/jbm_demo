# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.exceptions import UserError
import base64
from odoo.modules.module import get_module_resource
from odoo.exceptions import ValidationError

Marital_Status = [('single', 'Single'),
                  ('married', 'Married'),
                  ('widower', 'Widower'),
                  ('divorced', 'Divorced')]


class RecruitmentStage(models.Model):
    _inherit = "hr.recruitment.stage"

    generate_contract = fields.Boolean('Generate Contract')
    create_employee = fields.Boolean('Create Employee')
    start_interview = fields.Boolean('Start Interview')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('under_approve', 'Under Approve'),
        ('approved', 'Approved')
    ], default='draft')

    @api.constrains("state")
    def _check_state(self):
        if self.state == 'approved' or self.state == 'under_approve':
            stages = self.env['hr.recruitment.stage'].search([
                ('state', '=', self.state),
                ('id', '!=', self.id)
            ])
            if stages:
                raise ValidationError("Approved or Under Approved State must be unique ")


class ApplicantChildrens(models.Model):
    _name = "hr.applicant.children"
    _description = 'Hr Applicant Children '

    name = fields.Char('Children Name')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], 'Gender')
    age = fields.Integer('Age')
    related_applicant = fields.Many2one('hr.applicant', 'Applicant')


class ApplicantSurveys(models.Model):
    _name = "hr.applicant.survey"
    _description = 'HR Applicant Survey'

    response_id = fields.Many2one('survey.user_input', "Response", ondelete="set null")
    user_id = fields.Many2one(related="response_id.create_uid")
    related_survey = fields.Many2one(related="related_applicant.survey_id")
    related_applicant = fields.Many2one('hr.applicant', 'Related Applicant', ondelete="cascade")

    def action_start_survey(self):
        self.ensure_one()
        # create a response and link it to this applicant
        if self.env.user.id != self.user_id.id:
            raise UserError("Only survey owner can modified")
        if not self.response_id:
            response = self.related_survey._create_answer(partner=self.related_applicant.partner_id)
            self.response_id = response.id
        else:
            response = self.response_id
        # grab the token of the response and start surveying
        return self.related_survey.with_context(survey_token=response.token).action_start_survey()

    def action_print_survey(self):
        """ If response is available then print this response otherwise print survey form (print template of the survey) """
        self.ensure_one()
        if not self.response_id:
            return self.related_survey.action_print_survey()
        else:
            response = self.response_id
            return self.related_survey.with_context(survey_token=response.token).action_print_survey()


class HrRecruitmentEducation(models.Model):
    _name = 'hr.recruitment.education'
    _description = 'Hr Recruitment Education'

    name = fields.Char(
        string='Name',
        required=True)


class Applicant(models.Model):
    _inherit = "hr.applicant"

    def action_application_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        template_id = self.env.ref('hr_recruitment_custom.send_notification_to_applicant').id
        ctx = {
            'default_model': 'hr.applicant',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            # 'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'active_ids': self.ids,
            # 'model_description': self.with_context(lang=lang).type_name,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    @api.model
    def _default_image(self):
        image_path = get_module_resource('hr', 'static/src/img', 'default_image.png')
        return base64.b64encode(open(image_path, 'rb').read())

    related_generate_contract = fields.Boolean(related='stage_id.generate_contract')
    related_create_employee = fields.Boolean(related='stage_id.create_employee')
    related_start_interview = fields.Boolean(related='stage_id.start_interview')

    proposed_contracts = fields.One2many('hr.contract', 'applicant_id', string="Proposed Contracts",
                                         domain="[('company_id', '=', company_id)]")
    proposed_contracts_count = fields.Integer(compute="_compute_proposed_contracts_count",
                                              string="Proposed Contracts Count")

    response_ids = fields.One2many('hr.applicant.survey', 'related_applicant', "Responses")

    currency = fields.Many2one('res.currency', 'Currency', default=lambda x: x.env.company.currency_id)
    nationality = fields.Many2one('res.country', 'Nationality (Country)')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], 'Gender')
    national_service = fields.Boolean('National Service Completed')
    currently_employed = fields.Boolean('Currently Employed')
    date_of_birth = fields.Date('Date Of Birth')
    last_position = fields.Char('Last Position')
    current_employer = fields.Char('Current Employer')
    current_location = fields.Char('Current location')
    total_years_of_exp = fields.Integer('Total Years of Exp')
    educational_background = fields.Text('Educational Background')
    marital_status = fields.Selection(Marital_Status, 'Marital Status')
    related_children = fields.One2many('hr.applicant.children', 'related_applicant', string="Children")
    current_salary = fields.Float("Current Salary")
    willing_relocate = fields.Boolean('Willing to Relocate')
    notice_period = fields.Float("Notice Period (Days)")
    other_offers = fields.Text("Any other Interviews or Offers ?")
    hiring_date = fields.Date('Hiring Confirmation Date')
    availability = fields.Date("Effective Start Date",
                               help="The date at which the applicant will be available to start working")
    nationality_name = fields.Char(
        string='Nationality Name',
        related='nationality.name')
    panel_ids = fields.Many2many(
        comodel_name='res.users',
        string='Interview Panel',
        related='job_id.panel_ids', readonly=False)
    current_user = fields.Many2one('res.users', 'Current User', default=lambda self: self.env.user)
    can_start_interview = fields.Boolean(
        string='Can Start Interview',
        required=False,
        compute="_can_start_interview")
    image_1920 = fields.Image(default=_default_image)
    education_id = fields.Many2one(
        comodel_name='hr.recruitment.education',
        string='Education',
        required=False)
    name_stage = fields.Char(related="stage_id.name", store=True)
    hiring_manager_id = fields.Many2one('hr.employee', string='Hiring Manager',
                                        domain="[('user_id.share', '=', False), ('department_id', '=', department_id)]")

    # image_1920 = fields.Image("Original Image", compute='_compute_image', compute_sudo=True)
    # image_1024 = fields.Image("Image 1024", compute='_compute_image', compute_sudo=True)
    # image_512 = fields.Image("Image 512", compute='_compute_image', compute_sudo=True)
    # image_256 = fields.Image("Image 256", compute='_compute_image', compute_sudo=True)
    # image_128 = fields.Image("Image 128", compute='_compute_image', compute_sudo=True)

    # def _compute_image(self):
    #     for employee in self:
    #         employee_id = self.sudo().env['hr.applicant'].browse(employee.id)
    #         employee.image_1920 = employee_id.image_1920
    #         employee.image_1024 = employee_id.image_1024
    #         employee.image_512 = employee_id.image_512
    #         employee.image_256 = employee_id.image_256
    #         employee.image_128 = employee_id.image_128

    def _can_start_interview(self):
        for rec in self:
            if self.env.user in rec.panel_ids:
                rec.can_start_interview = True
            else:
                rec.can_start_interview = False

    def action_start_survey(self):
        self.ensure_one()
        # create a response and link it to this applicant
        if self.env.user not in self.response_ids.mapped("create_uid"):
            response = self.survey_id._create_answer(partner=self.partner_id)
            self.response_ids = [(0, 0, {'response_id': response.id})]
        else:
            line = self.response_ids.filtered(lambda x: x.create_uid.id == self.env.user.id)
            response = line.response_id
        # grab the token of the response and start surveying
        return self.survey_id.with_context(survey_token=response.token).action_start_survey()

    def action_print_survey(self):
        """ If response is available then print this response otherwise print survey form (print template of the survey) """
        self.ensure_one()
        if not self.response_ids:
            return self.survey_id.action_print_survey()
        else:
            response = self.response_ids.filtered(lambda x: x.create_uid.id == self.env.user.id).response_id
            return self.survey_id.with_context(survey_token=response.token).action_print_survey()

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        for rec in self:
            if rec.stage_id.create_employee == True:
                rec.hiring_date = fields.Date.today()

    def action_show_proposed_contracts(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.contract",
            "views": [[False, "tree"], [False, "form"]],
            "domain": [["applicant_id", "=", self.id], '|', ["active", "=", False], ["active", "=", True]],
            "name": "Proposed Contracts",
            "context": {'default_employee_id': self.emp_id.id},
        }

    def _compute_proposed_contracts_count(self):
        Contracts = self.env['hr.contract'].sudo()
        for applicant in self:
            applicant.proposed_contracts_count = Contracts.with_context(active_test=False).search_count([
                ('applicant_id', '=', applicant.id)])

    def write(self, vals):
        if vals.get('panel_ids'):
            old_panel = self.panel_ids
            res = super(Applicant, self).write(vals)
            new_panel = self.panel_ids

            for p in new_panel:
                if p not in old_panel:
                    p.employee_ids.message_post(type="notification", subtype_xmlid="mt_comment",
                                                body=_("%s, You have been assigned to the Interview Panel of %s") % (
                                                    p.name, self.partner_name),
                                                partner_ids=[p.partner_id.id])
        else:
            res = super(Applicant, self).write(vals)

        return res


class HrContract(models.Model):
    _inherit = 'hr.contract'

    applicant_id = fields.Many2one('hr.applicant',
                                   domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
