from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from odoo.addons.auth_signup.models.res_partner import now
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class User(models.Model):
    _inherit = 'res.users'

    # employee_number = fields.Char(related="employee_id.registration_number", string="Employee Number",
    #                               related_sudo=False, readonly=False)
    # employee_type = fields.Selection(related="employee_id.employee_type", string="Employment Category",
    # related_sudo=False, readonly=False)
    # total_amount_working_days_no_store = fields.Float(related="employee_id.total_amount_working_days_no_store",
    #                                                   string="End of Service Benefit")
    # permanent_staff_employee = fields.Many2one(related="employee_id.permanent_staff_employee", string="Pay Scale")
    # directorate = fields.Many2one(related="employee_id.directorate", string="Directorate")
    # joining_date = fields.Date(related="employee_id.joining_date", string="Joining Date")
    # probation = fields.Selection(related="employee_id.probation", string="Probation")
    # probation_date = fields.Date(related="employee_id.probation_date", string="Probation Date")
    # number_of_years_work = fields.Char(related="employee_id.number_of_years_work", string="Yrs w/ Waseef")
    # contract_duration = fields.Selection(related="employee_id.contract_duration", string="Contract Duration")
    # job_name_arabic = fields.Char(related="employee_id.job_name_arabic", string="Job Position in Arabic")
    # age = fields.Integer(related="employee_id.age", string="Age")
    # contract_status = fields.Selection(related="employee_id.contract_status", string="Contract Status")
    #
    # bank_name = fields.Char(related="employee_id.bank_name", string="Bank Name")
    # bank_account_type = fields.Selection(related="employee_id.bank_account_type", string="Bank Account Type")
    # sim_card = fields.Char(related="employee_id.sim_card", string="Mobile")
    # sponsorship_type = fields.Selection(related="employee_id.sponsorship_type", string="Sponsorship Type")
    # sponsor = fields.Many2one(related="employee_id.sponsor", string="Sponsor")
    # owns_car = fields.Boolean(related="employee_id.owns_car", string="Owns a car")
    # religion = fields.Selection(related="employee_id.religion", string="Religion")
    # mother_nationality = fields.Selection(related="employee_id.mother_nationality", string="Mother Nationality")
    # driving_licence = fields.Many2many(related="employee_id.driving_licence", string="Driving Licence")
    # qualification_type = fields.Char(related="employee_id.qualification_type", string="Qualification Type")
    # qualification_title = fields.Char(related="employee_id.qualification_title", string="Qualification Title")
    # qid_doc_number = fields.Char(related="employee_id.qid_doc_number", string="QID Number")
    # passport_doc_number = fields.Char(related="employee_id.passport_doc_number", string="Passport Number")
    # visa_doc_number = fields.Char(related="employee_id.visa_doc_number", string="Visa Number")
    # home_country_phone_number = fields.Char(related="employee_id.home_country_phone_number",
                                            # string="Home Country Phone Number")
    # home_country_address = fields.Char(related="employee_id.home_country_address", string="Home Country Address")
    # extension = fields.Char(related="employee_id.extension", string="Ext")

    def action_reset_password_portal(self):
        """ create signup token for each portal user , and send their signup url by email """
        # prepare reset password signup
        create_mode = bool(self.env.context.get('create_user'))

        # no time limit for initial invitation, only for reset password
        expiration = False if create_mode else now(days=+1)

        self.mapped('partner_id').signup_prepare(signup_type="reset", expiration=expiration)

        # send email to users with their signup url
        template = False
        if create_mode:
            try:
                template = self.env.ref('ebs_hr_custom.portal_set_password_email', raise_if_not_found=False)
            except ValueError:
                pass
        if not template:
            template = self.env.ref('ebs_hr_custom.portal_reset_password_email')
        assert template._name == 'mail.template'

        template_values = {
            'email_to': '${object.email|safe}',
            'email_cc': False,
            'auto_delete': True,
            'partner_to': False,
            'scheduled_date': False,
        }
        template.write(template_values)
        print("In Portal Reset Password")
        for user in self:
            if not user.email:
                raise UserError(_("Cannot send email: user %s has no email address.") % user.name)
            with self.env.cr.savepoint():
                force_send = not (self.env.context.get('import_file', False))
                template.with_context(lang=user.lang).send_mail(user.id, force_send=force_send, raise_exception=True)
            _logger.info("Password reset email sent for user <%s> to <%s>", user.login, user.email)
