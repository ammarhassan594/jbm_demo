from odoo import fields, models, api, _
from odoo.exceptions import UserError


class LinkPartnerWizard(models.TransientModel):
    _name = 'link.employee.partner.wizard'
    _description = 'Link Employee Partner Wizard'

    def get_partner_domain(self):
        domain = []
        if self._context.get('employee_name'):
            employee_names = self._context.get('employee_name').split(' ')
            for l in range(len(employee_names) - 1):
                domain.append('|')
            for l in range(len(employee_names)):
                string = '%' + employee_names[l] + '%'
                domain.append(('name', 'ilike', string))
        return domain


    partner_ids = fields.Many2one('res.partner', domain=get_partner_domain)

    def button_confirm(self):
        employee = self.env['hr.employee'].browse(self._context.get('employee_id'))
        if self.partner_ids:
            employee.link_employee_partner(self.partner_ids)
        else:
            employee.link_employee_partner()

