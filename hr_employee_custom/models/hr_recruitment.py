from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.exceptions import UserError


class Applicant(models.Model):
    _inherit = "hr.applicant"

    employee_type = fields.Selection([('fusion_employee', 'Main Company Employee'), ('fos_employee', 'FOS Employee')],
                                     string="Employee Type")
    is_create_user = fields.Boolean('Create User?')

    def create_employee_from_applicant(self):
        """ Create an hr.employee from the hr.applicants """
        employee = False
        for applicant in self:
            contact_name = False
            partner_id = False
            user_id = False
            if applicant.partner_id:
                address_id = applicant.partner_id.address_get(['contact'])['contact']
                partner_id = applicant.partner_id
                contact_name = applicant.partner_id.display_name
            else:
                if not applicant.partner_name:
                    raise UserError(_('You must define a Contact Name for this applicant.'))

            if applicant.partner_name or contact_name:
                running_contract = applicant.proposed_contracts.filtered(lambda x: x.state == 'open')
                name_split = applicant.partner_name.split()
                firstname = ""
                middlename = ""
                lastname = ""
                if len(name_split) >= 3:
                    firstname = name_split[0]
                    middlename = name_split[1]
                    lastname = " ".join(x for x in name_split[2:])
                elif len(name_split) == 2:
                    firstname = name_split[0]
                    lastname = name_split[1]
                else:
                    firstname = name_split[0]
                employee = self.env['hr.employee'].create({
                    'name': applicant.partner_name or contact_name,
                    'firstname': firstname,
                    'middlename': middlename,
                    'lastname': lastname,
                    'phone': applicant.partner_phone or applicant.partner_mobile,
                    'birthday': applicant.date_of_birth,
                    # 'address_home_id': address_id,
                    'country_of_birth': applicant.nationality.id,
                    'marital': applicant.marital_status,
                    'employee_type': applicant.employee_type,
                    # 'address_id': applicant.company_id and applicant.company_id.partner_id
                    #               and applicant.company_id.partner_id.id or False,
                    'work_email': applicant.email_from,
                    'work_phone': applicant.department_id and applicant.department_id.company_id
                                  and applicant.department_id.company_id.phone or False,
                    'department_id': applicant.department_id.id,
                    'parent_id': applicant.job_id.default_manager.id,
                    # 'user_partner_id': partner_id and partner_id.id,
                    # 'user_id': user_id and user_id.id,
                })
                if applicant.is_create_user:
                    employee.create_user()

                applicant.write({'emp_id': employee.id})
                if running_contract:
                    running_contract.write({
                        'employee_id': employee.id,
                    })
                    running_contract._assign_open_contract()
                if applicant.job_id:
                    applicant.job_id.write({'no_of_hired_employee': applicant.job_id.no_of_hired_employee + 1})
                    applicant.job_id.message_post(
                        body=_(
                            'New Employee %s Hired') % applicant.partner_name if applicant.partner_name else applicant.name,
                        subtype_xmlid="hr_recruitment.mt_job_applicant_hired")
                applicant.message_post_with_view(
                    'hr_recruitment.applicant_hired_template',
                    values={'applicant': applicant},
                    subtype_id=self.env.ref("hr_recruitment.mt_applicant_hired").id)

        employee_action = self.env.ref('hr.open_view_employee_list')
        dict_act_window = employee_action.read([])[0]
        dict_act_window['context'] = {'form_view_initial_mode': 'edit'}
        dict_act_window['res_id'] = employee.id
        return dict_act_window
