from odoo import fields, models, api, _
from odoo.exceptions import UserError
from ast import literal_eval


class LinkUserWizard(models.TransientModel):
    _name = 'link.employee.user.wizard'
    _description = 'Link Employee User Wizard'

    def get_employee_email(self):
        return self.env['hr.employee'].search([('id','=',self._context.get('active_id'))]).work_email

    user_id = fields.Many2one('res.users')
    email = fields.Char('Email', default=get_employee_email)

    def button_confirm(self):
        employee = self.env['hr.employee'].browse(self._context.get('active_id'))
        if self.user_id:
            employee.user_id = self.user_id.id
            employee.work_email = self.user_id.login
        else:
            template_user_id = literal_eval(
                self.env['ir.config_parameter'].sudo().get_param('base.template_portal_user_id', 'False'))
            template_user = self.env['res.users'].browse(template_user_id)
            if not template_user.exists():
                raise ValueError(_('Signup: invalid template user'))
            values = {
                'active': True,
                'name': employee.name,
                'login': self.email,
                'email': self.email,
                'is_employee': True,
                'company_id': employee.company_id.id or employee.user_id.company_id.id or self.env.user.company_id.id,
                'company_ids': [(6, 0, [employee.company_id.id or employee.user_id.company_id.id or self.env.user.company_id.id])]
            }
            if employee.user_partner_id:
                values.update({
                    'partner_id': employee.user_partner_id.id
                })
            employee.user_id = self.env['res.users'].with_context(no_reset_password=True).create(values)
            employee.work_email = self.email
            if not employee.user_partner_id:
                employee.user_partner_id = employee.user_id.partner_id.id

