from odoo import fields, models, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    job_id = fields.Many2one('hr.job',string='Job Position')
    client_employee_ids = fields.One2many('hr.employee', 'partner_parent_id', domain=[('employee_type','=','client_employee')],string="Client Employees")
    fos_employee_ids = fields.One2many('hr.employee', 'partner_parent_id', domain=[('employee_type','=','fos_employee')] ,string="FOS Employees")
    prorata_method = fields.Selection([('30', '30 Days per Month'), ('365', '365 Days'), ('m', 'Days per month')],
                                      string='Prorata Method')
    total_service_fees = fields.Float(string='Total Service Fees', compute='compute_total_fees')
    total_salary_package = fields.Float(string='Total Salary Package', compute='compute_total_fees')
    #Operations tab
    madlsa_username = fields.Char('Username')
    madlsa_password = fields.Char('Password')
    madlsa_email = fields.Char('MADLSA Email')
    madlsa_phone = fields.Char('Phone Number')
    madlsa_electricity = fields.Char('Electricity Number')
    madlsa_water = fields.Char('Water Number')
    med_com_password = fields.Char('Media Passsword')
    med_com_phone = fields.Char('Mobile Number')

    @api.depends('fos_employee_ids')
    def compute_total_fees(self):
        for rec in self:
            rec.total_service_fees = sum(rec.fos_employee_ids.mapped('service_fee'))
            rec.total_salary_package = sum(rec.fos_employee_ids.mapped('active_contract.package'))

    def open_employee_list(self):
        action = self.env.ref('ebs_fusion_hr_employee.open_view_client_employee_list_my').read([])[0]
        action['domain'] = [('partner_parent_id', '=', self.id),('employee_type', '=', 'client_employee')]
        action['context'] = {'default_partner_parent_id': self.id, 'default_employee_type': 'client_employee'}
        return action

    def open_outsourced_employee_list(self):
        action = self.env.ref('ebs_fusion_hr_employee.open_view_fos_employee_list_my').read([])[0]
        action['domain'] = [('partner_parent_id', '=', self.id),('employee_type', '=', 'fos_employee')]
        action['context'] = {'default_partner_parent_id': self.id, 'default_employee_type': 'fos_employee'}
        return action

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if self._context.get('partner_parent_from_employee'):
            if self._context.get('employee_type') and (self._context.get('employee_type') == 'fusion_employee'):
                args.append(('company_partner','=',True))
            else:
                args.append(('is_customer', '=', True))
                args.append(('is_company', '=', True))
                args.append(('parent_id', '=', False))
        if self._context.get('partner_sponsered_from_employee'):
            if self._context.get('employee_type') and (self._context.get('employee_type') in ['fusion_employee', 'fos_employee']):
                args.append(('company_partner','=',True))
            else:
                args.append(('is_customer', '=', True))
                args.append(('is_company', '=', True))
                args.append(('parent_id', '=', False))
                # args.append(('id', '=', self._context.get('partner_parent_id')))
        return super(ResPartner, self)._search(args=args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)

    def action_see_employee(self):

        return {}






