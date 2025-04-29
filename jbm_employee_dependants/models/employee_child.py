from odoo import models, fields, api, _
from datetime import date
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


def get_year():
    current_year = datetime.now().year
    if datetime.now().month > 6:
        return current_year + 1
    else:
        return current_year


class EmployeeChild(models.Model):
    _name = 'hr.emp.child'
    _description = 'Employee Child'
    _order = 'date_of_birth'

    name = fields.Char(
        string='Name',
        required=True)

    qid = fields.Char(
        string='QID')

    passport_number = fields.Char(
        string='Passport Number')

    passport_issue_date = fields.Date(
        string='Passport Issue Date')

    passport_issue_place = fields.Char(
        string='Passport Issue Place')

    date_of_birth = fields.Date(
        string='Date of Birth',
        default=fields.Datetime.now(),
        required=False)

    is_student = fields.Boolean(
        string='Is Student',
        required=False, default=False)

    emp_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=False)
    # relation = fields.Selection(string="Relation", selection=[('wife', 'Wife'), ('child', 'Child')], default='child'
    #                             , required=False)
    relation = fields.Selection(string="Relation", selection=[('spouse', 'Spouse'), ('child', 'Child')], default='child'
                                , required=False)
    is_child = fields.Boolean(string="is_child", default=False)

    is_infant = fields.Boolean(string="is_infant", default=False)

    school_name = fields.Char()

    age = fields.Float(compute='_get_age', store=False)

    QID_expiry_date = fields.Date("QID Expiry Date")
    QID_attachment = fields.Binary("QID Attachment")
    hamad_card_number = fields.Char("Hamad Card Number")
    Hamad_card_expiry_date = fields.Date("Hamad Card Expiry Date")
    Passport_expiry_date = fields.Date("Passport Expiry Date")
    insurance_details = fields.Char("Insurance Details")

    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ], string="Gender", default='male')

    approval_request_id = fields.Many2one('approval.request')

    @api.depends('date_of_birth')
    def _get_age(self):
        for rec in self:
            if rec.date_of_birth:
                date_jun = datetime(get_year(), 6, 30, 0, 0, 0).date()
                age_cust = (date_jun - rec.date_of_birth).days / 365
                rec.age = age_cust
            else:
                rec.age = 99

    # @api.model
    # def create(self, values):
    #     users = []
    #     ctx = {}
    #     res = super(EmployeeChild, self).create(values)
    #     mail_template = self.env.ref('ebs_lb_payroll.new_dependent_email_template')
    #     users += self.env.ref('hr_payroll.group_hr_payroll_manager').users
    #     users += self.env.ref('hr_payroll.group_hr_payroll_user').users
    #     ctx['email_to'] = ','.join([user.email for user in users if user.email])
    #     ctx['name'] = values['name']
    #     employee_name = self.env['hr.employee'].sudo().browse(values['emp_id']) if values['emp_id'] else False
    #     if employee_name:
    #         ctx['employee_name'] = employee_name.name
    #     template = mail_template.sudo().with_context(ctx)
    #     template.send_mail(self.id, force_send=True)
    #     return res